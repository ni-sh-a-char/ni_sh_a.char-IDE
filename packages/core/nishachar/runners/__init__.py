"""Execution backends. Every one of them satisfies the same tiny interface."""

from __future__ import annotations

from ..registry import Language
from .base import (
    DEFAULT_OUTPUT_LIMIT,
    DEFAULT_TIMEOUT,
    ExecResult,
    ExecutionError,
    Runner,
)
from .docker import DockerRunner
from .local import LocalRunner

__all__ = [
    "DEFAULT_OUTPUT_LIMIT",
    "DEFAULT_TIMEOUT",
    "AutoRunner",
    "DockerRunner",
    "ExecResult",
    "ExecutionError",
    "LocalRunner",
    "Runner",
    "get_runner",
]


class AutoRunner:
    """Use the local toolchain when it exists, otherwise a container.

    This is what makes "runs every language" true in practice: you get the
    fast path for the handful of toolchains you have installed, and Rust or
    COBOL still run without you installing anything.
    """

    name = "auto"

    def __init__(self, **kwargs) -> None:
        self.local = LocalRunner(**kwargs)
        self.docker = DockerRunner()
        self._docker_ready: bool | None = None

    def available(self) -> bool:
        return True

    def docker_ready(self) -> bool:
        """Probe the Docker daemon at most once -- ``docker info`` is slow."""
        if self._docker_ready is None:
            self._docker_ready = self.docker.available()
        return self._docker_ready

    def pick(self, language: Language) -> Runner:
        if self.local.supports(language):
            return self.local
        if self.docker.supports(language) and self.docker_ready():
            return self.docker
        missing = language.run[0]
        raise ExecutionError(
            f"Cannot run {language.name}: '{missing}' is not installed and Docker "
            "is not available. Install the toolchain, start Docker, or run this "
            "language in the browser tier if it supports one."
        )

    def supports(self, language: Language) -> bool:
        return self.local.supports(language) or (
            self.docker.supports(language) and self.docker_ready()
        )

    def run(self, code: str, language: Language, **kwargs) -> ExecResult:
        return self.pick(language).run(code, language, **kwargs)


RUNNERS: dict[str, type] = {
    "auto": AutoRunner,
    "local": LocalRunner,
    "docker": DockerRunner,
}


def get_runner(name: str = "auto", **kwargs) -> Runner:
    """Return a backend by name: ``auto``, ``local`` or ``docker``."""
    name = (name or "auto").lower()
    if name not in RUNNERS:
        raise ExecutionError(
            f"unknown runner {name!r}; choose one of: {', '.join(RUNNERS)}"
        )
    # Only the local-backed runners take a workdir.
    if name == "docker":
        return RUNNERS[name]()
    return RUNNERS[name](**kwargs)
