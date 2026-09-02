"""Tier 2: run code inside a locked-down container.

This is the backend to use for code you did not write. Every container is
started with no network, a read-only root filesystem, all capabilities
dropped, no privilege escalation, and hard memory/CPU/process caps, on top of
the wall-clock timeout and output cap that every tier enforces.

Languages that need packages installed (``setup`` in the registry) get them at
*image build* time, not at run time. That is the whole reason for the derived
image below: the network is available while the image is built once, and never
again when your code actually runs.
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from ..registry import Language
from .base import (
    DEFAULT_OUTPUT_LIMIT,
    DEFAULT_TIMEOUT,
    ExecResult,
    ExecutionError,
    clamp,
)

WORK = "/work"


def _share_with_container(workspace: Path, source: Path) -> None:
    """Make the mounted workspace reachable by the process inside the container.

    ``tempfile`` creates directories as 0700 owned by the host user, and the
    container process is a different uid. Normally root inside the container
    would read it anyway via CAP_DAC_OVERRIDE -- but we drop every capability,
    which is precisely what takes that bypass away. Without this the program
    fails with "Permission denied" before it ever runs.

    Widening a single-use scratch directory that is destroyed moments later is
    the cheaper trade than handing the container back CAP_DAC_OVERRIDE, or than
    forcing ``--user`` and breaking every toolchain that expects a writable
    HOME. On a shared host another local user could read the snippet while it
    runs; on a single-user machine, which is the normal case, nothing is
    exposed that the user did not already own.
    """
    try:
        workspace.chmod(0o777)  # compile steps write their output here
        source.chmod(0o644)
    except OSError:
        # Windows ignores POSIX modes; the bind mount is permissive there.
        pass


class Limits:
    """Resource ceilings applied to every container."""

    memory = "256m"
    cpus = "1.0"
    pids = "128"
    tmpfs_size = "64m"


class DockerRunner:
    """Executes code in a disposable, network-isolated container."""

    name = "docker"

    def __init__(self, *, docker: str = "docker", limits: type[Limits] = Limits) -> None:
        self.docker = docker
        self.limits = limits

    def available(self) -> bool:
        """True only if the Docker CLI exists *and* a daemon answers."""
        if shutil.which(self.docker) is None:
            return False
        try:
            probe = subprocess.run(
                [self.docker, "info", "--format", "{{.ServerVersion}}"],
                capture_output=True,
                timeout=10,
            )
        except (OSError, subprocess.SubprocessError):
            return False
        return probe.returncode == 0

    def supports(self, language: Language) -> bool:
        return bool(language.image)

    # -- image preparation -------------------------------------------------

    def image_for(self, language: Language) -> str:
        """The image to run. Languages with ``setup`` get a derived, cached image."""
        if not language.setup:
            return language.image
        # Tag by a hash of the recipe so changing setup rebuilds automatically.
        recipe = repr((language.image, language.setup)).encode()
        digest = hashlib.sha256(recipe).hexdigest()[:12]
        return f"nishachar/{language.id}:{digest}"

    def _image_exists(self, tag: str) -> bool:
        probe = subprocess.run(
            [self.docker, "image", "inspect", tag], capture_output=True
        )
        return probe.returncode == 0

    def ensure_image(self, language: Language, *, timeout: float = 600) -> str:
        """Build the derived image if this language needs one. Idempotent."""
        tag = self.image_for(language)
        if not language.setup or self._image_exists(tag):
            return tag
        lines = [f"FROM {language.image}"]
        for step in language.setup:
            lines.append("RUN " + " ".join(step))
        with tempfile.TemporaryDirectory(prefix="nishachar-build-") as build:
            Path(build, "Dockerfile").write_text("\n".join(lines) + "\n", encoding="utf-8")
            built = subprocess.run(
                [self.docker, "build", "-t", tag, build],
                capture_output=True,
                timeout=timeout,
            )
        if built.returncode != 0:
            raise ExecutionError(
                f"could not build the {language.name} image:\n"
                + built.stderr.decode("utf-8", "replace")[-2000:]
            )
        return tag

    # -- execution ---------------------------------------------------------

    def container_argv(self, image: str, mount: Path, argv: list[str]) -> list[str]:
        """Build the ``docker run`` command line. Kept pure so it can be tested."""
        limits = self.limits
        return [
            self.docker, "run", "--rm", "-i",
            "--network", "none",
            "--memory", limits.memory,
            "--memory-swap", limits.memory,
            "--cpus", limits.cpus,
            "--pids-limit", limits.pids,
            "--read-only",
            "--tmpfs", f"/tmp:rw,exec,size={limits.tmpfs_size}",
            "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges",
            "-v", f"{mount}:{WORK}",
            "-w", WORK,
            image,
            *argv,
        ]

    def run(
        self,
        code: str,
        language: Language,
        *,
        stdin: str = "",
        timeout: float = DEFAULT_TIMEOUT,
        output_limit: int = DEFAULT_OUTPUT_LIMIT,
    ) -> ExecResult:
        if not language.image:
            raise ExecutionError(
                f"{language.name} has no container image in the registry. "
                "Add an 'image' field to its language definition, or use --runner local."
            )
        started = time.monotonic()
        image = self.ensure_image(language)

        with tempfile.TemporaryDirectory(prefix="nishachar-") as host:
            mount = Path(host)
            filename = language.filename or f"main{language.extensions[0]}"
            source_on_host = mount / filename
            source_on_host.write_text(code, encoding="utf-8")
            _share_with_container(mount, source_on_host)

            # Paths are resolved as they appear *inside* the container.
            inside = Path(WORK)
            source, binary = inside / filename, inside / "program"

            for step in language.compile:
                argv = language.resolve(step, file=source, workdir=inside, binary=binary)
                compiled = self._exec(image, mount, argv, "", timeout, output_limit)
                if compiled.exit_code != 0 or compiled.timed_out:
                    compiled.language, compiled.runner = language.id, self.name
                    compiled.compile_failed = True
                    compiled.duration_ms = int((time.monotonic() - started) * 1000)
                    return compiled

            argv = language.resolve(language.run, file=source, workdir=inside, binary=binary)
            result = self._exec(image, mount, argv, stdin, timeout, output_limit)

        result.language, result.runner = language.id, self.name
        result.duration_ms = int((time.monotonic() - started) * 1000)
        return result

    def _exec(
        self,
        image: str,
        mount: Path,
        argv: list[str],
        stdin: str,
        timeout: float,
        output_limit: int,
    ) -> ExecResult:
        command = self.container_argv(image, mount, argv)
        try:
            done = subprocess.run(
                command,
                input=stdin.encode("utf-8"),
                capture_output=True,
                # Docker enforces nothing here; the grace margin lets the daemon
                # tear the container down before we give up on it.
                timeout=timeout + 5,
            )
        except FileNotFoundError:
            raise ExecutionError("Docker is not installed or not on PATH.") from None
        except subprocess.TimeoutExpired:
            return ExecResult(
                stderr=f"Killed: exceeded the {timeout:g}s time limit.",
                exit_code=124,
                timed_out=True,
            )

        stdout, cut_out = clamp(done.stdout or b"", output_limit)
        stderr, cut_err = clamp(done.stderr or b"", output_limit)
        return ExecResult(
            stdout=stdout,
            stderr=stderr,
            exit_code=done.returncode,
            truncated=cut_out or cut_err,
        )
