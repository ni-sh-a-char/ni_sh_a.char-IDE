"""The one interface every execution backend implements."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..registry import Language

# Defaults chosen to be safe rather than generous. Callers may raise them.
DEFAULT_TIMEOUT = 10.0
DEFAULT_OUTPUT_LIMIT = 256 * 1024  # bytes per stream


class ExecutionError(RuntimeError):
    """Raised when a backend cannot run at all (missing toolchain, no Docker)."""


@dataclass
class ExecResult:
    """The outcome of one execution. Identical shape from every backend."""

    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    duration_ms: int = 0
    timed_out: bool = False
    truncated: bool = False
    language: str = ""
    runner: str = ""
    compile_failed: bool = False

    @property
    def ok(self) -> bool:
        return self.exit_code == 0 and not self.timed_out

    def to_dict(self) -> dict:
        return {
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exitCode": self.exit_code,
            "durationMs": self.duration_ms,
            "timedOut": self.timed_out,
            "truncated": self.truncated,
            "language": self.language,
            "runner": self.runner,
            "compileFailed": self.compile_failed,
            "ok": self.ok,
        }


class Runner(Protocol):
    """A place code can be executed."""

    name: str

    def available(self) -> bool:
        """Whether this backend can be used on this machine right now."""

    def run(
        self,
        code: str,
        language: Language,
        *,
        stdin: str = "",
        timeout: float = DEFAULT_TIMEOUT,
        output_limit: int = DEFAULT_OUTPUT_LIMIT,
    ) -> ExecResult:
        """Execute ``code`` and return the result. Must never raise on program error."""


def clamp(text: bytes, limit: int) -> tuple[str, bool]:
    """Decode output, capping it so a runaway program cannot exhaust memory.

    Returns the text and whether it was cut short.
    """
    if len(text) <= limit:
        return _decode(text), False
    head = _decode(text[:limit])
    dropped = len(text) - limit
    return f"{head}\n... output truncated, {dropped} more bytes ...", True


def _decode(raw: bytes) -> str:
    """Decode as UTF-8 and normalise line endings.

    Without this the same program yields '\\r\\n' on Windows and '\\n'
    everywhere else, which leaks the host OS into the IDE's output pane and
    into every test assertion.
    """
    return raw.decode("utf-8", "replace").replace("\r\n", "\n")
