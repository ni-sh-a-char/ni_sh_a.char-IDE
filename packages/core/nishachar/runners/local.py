"""Tier 1: run code against the toolchains installed on this machine.

No isolation. This backend executes with the full privileges of the user who
started it, which is exactly right for a local IDE running your own code and
exactly wrong for untrusted input -- use :mod:`~nishachar.runners.docker` for
that. What this tier *does* guarantee is that a program cannot hang forever or
flood memory with output: every run is bounded by a wall-clock timeout and a
per-stream byte cap, and a timed-out process has its whole tree killed.
"""

from __future__ import annotations

import contextlib
import os
import shutil
import signal
import subprocess
import sys
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

WINDOWS = sys.platform == "win32"


def _kill_tree(process: subprocess.Popen) -> None:
    """Kill a process and everything it spawned.

    ``Popen.kill`` only kills the direct child, which leaves orphans behind for
    anything that forks -- compilers and build tools routinely do.
    """
    if process.poll() is not None:
        return
    try:
        if WINDOWS:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                capture_output=True,
                check=False,
            )
        else:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
    except (OSError, PermissionError):
        pass
    finally:
        with contextlib.suppress(OSError):
            process.kill()


def _spawn_kwargs() -> dict:
    """Put the child in its own process group so the whole tree is killable."""
    if WINDOWS:
        return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    return {"start_new_session": True}


class LocalRunner:
    """Executes code as a subprocess using the host's installed toolchains."""

    name = "local"

    def __init__(self, workdir: Path | str | None = None) -> None:
        self.workdir = Path(workdir) if workdir else None

    def available(self) -> bool:
        return True

    def supports(self, language: Language) -> bool:
        """Whether this machine actually has the toolchain for ``language``."""
        for step in (*language.compile, language.run):
            program = step[0]
            if program.startswith("{"):  # {bin} -- produced by a compile step
                continue
            if shutil.which(program) is None:
                return False
        return True

    def run(
        self,
        code: str,
        language: Language,
        *,
        stdin: str = "",
        timeout: float = DEFAULT_TIMEOUT,
        output_limit: int = DEFAULT_OUTPUT_LIMIT,
    ) -> ExecResult:
        started = time.monotonic()
        base = tempfile.mkdtemp(prefix="nishachar-", dir=self.workdir)
        try:
            return self._run_in(
                Path(base), code, language, stdin, timeout, output_limit, started
            )
        finally:
            shutil.rmtree(base, ignore_errors=True)

    def _run_in(
        self,
        workdir: Path,
        code: str,
        language: Language,
        stdin: str,
        timeout: float,
        output_limit: int,
        started: float,
    ) -> ExecResult:
        source = workdir / (language.filename or f"main{language.extensions[0]}")
        source.write_text(code, encoding="utf-8")
        binary = workdir / ("program.exe" if WINDOWS else "program")

        result = ExecResult(language=language.id, runner=self.name)

        for step in language.compile:
            argv = language.resolve(step, file=source, workdir=workdir, binary=binary)
            compiled = self._exec(argv, workdir, "", timeout, output_limit)
            if compiled.exit_code != 0 or compiled.timed_out:
                compiled.language, compiled.runner = language.id, self.name
                compiled.compile_failed = True
                compiled.duration_ms = int((time.monotonic() - started) * 1000)
                if not compiled.stderr and not compiled.stdout:
                    compiled.stderr = f"{argv[0]}: compilation failed"
                return compiled

        argv = language.resolve(language.run, file=source, workdir=workdir, binary=binary)
        result = self._exec(argv, workdir, stdin, timeout, output_limit)
        result.language, result.runner = language.id, self.name
        result.duration_ms = int((time.monotonic() - started) * 1000)
        return result

    def _exec(
        self,
        argv: list[str],
        workdir: Path,
        stdin: str,
        timeout: float,
        output_limit: int,
    ) -> ExecResult:
        try:
            process = subprocess.Popen(
                argv,
                cwd=workdir,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                **_spawn_kwargs(),
            )
        except FileNotFoundError:
            raise ExecutionError(
                f"'{argv[0]}' is not installed or not on PATH. Install the toolchain, "
                "or use the Docker runner (--runner docker) to run it in a container."
            ) from None
        except OSError as exc:
            raise ExecutionError(f"could not start '{argv[0]}': {exc}") from None

        timed_out = False
        try:
            out, err = process.communicate(stdin.encode("utf-8"), timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            _kill_tree(process)
            out, err = process.communicate()
            err = (err or b"") + f"\nKilled: exceeded the {timeout:g}s time limit.".encode()

        stdout, cut_out = clamp(out or b"", output_limit)
        stderr, cut_err = clamp(err or b"", output_limit)
        return ExecResult(
            stdout=stdout,
            stderr=stderr,
            exit_code=process.returncode if not timed_out else 124,
            timed_out=timed_out,
            truncated=cut_out or cut_err,
        )
