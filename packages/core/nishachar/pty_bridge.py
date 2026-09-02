"""A real interactive shell, so languages can drive the system around them.

Running a program is only half of what an IDE is for. The other half is
``pip install``, ``git status``, ``ls`` -- the system commands a language
reaches for. This module gives the IDE a genuine terminal for that.

Three implementations, picked automatically:

* POSIX -- ``pty`` from the standard library. A true TTY, so ``top``, colours,
  progress bars and password prompts all behave.
* Windows -- ConPTY via the optional ``pywinpty`` dependency.
* Anywhere else -- plain pipes. Commands still run; there is just no TTY, so
  interactive full-screen programs will not render.

This is off by default everywhere it is exposed. See ``server.py``.
"""

from __future__ import annotations

import contextlib
import os
import shutil
import subprocess
import sys
import threading
from typing import Protocol

WINDOWS = sys.platform == "win32"


def default_shell() -> list[str]:
    """The shell to open, honouring the user's preference."""
    if WINDOWS:
        pwsh = shutil.which("pwsh") or shutil.which("powershell")
        return [pwsh] if pwsh else [os.environ.get("COMSPEC", "cmd.exe")]
    shell = os.environ.get("SHELL") or shutil.which("bash") or "/bin/sh"
    return [shell, "-i"]


class Terminal(Protocol):
    """A bidirectional byte stream attached to a running shell."""

    def read(self, size: int = 65536) -> bytes: ...
    def write(self, data: bytes) -> None: ...
    def resize(self, cols: int, rows: int) -> None: ...
    def close(self) -> None: ...
    @property
    def alive(self) -> bool: ...


class _PosixTerminal:
    """A true pseudo-terminal using the standard library's ``pty``."""

    def __init__(self, argv: list[str], cwd: str | None, cols: int, rows: int) -> None:
        import pty

        self._master, slave = pty.openpty()
        self._process = subprocess.Popen(
            argv,
            preexec_fn=os.setsid,
            stdin=slave,
            stdout=slave,
            stderr=slave,
            cwd=cwd,
            env={**os.environ, "TERM": "xterm-256color"},
        )
        os.close(slave)
        self.resize(cols, rows)

    def read(self, size: int = 65536) -> bytes:
        try:
            return os.read(self._master, size)
        except OSError:
            return b""

    def write(self, data: bytes) -> None:
        os.write(self._master, data)

    def resize(self, cols: int, rows: int) -> None:
        import fcntl
        import struct
        import termios

        packed = struct.pack("HHHH", rows, cols, 0, 0)
        with contextlib.suppress(OSError):
            fcntl.ioctl(self._master, termios.TIOCSWINSZ, packed)

    @property
    def alive(self) -> bool:
        return self._process.poll() is None

    def close(self) -> None:
        with contextlib.suppress(OSError):
            self._process.kill()
        with contextlib.suppress(OSError):
            os.close(self._master)


class _WinptyTerminal:
    """ConPTY through the optional ``pywinpty`` package."""

    def __init__(self, argv: list[str], cwd: str | None, cols: int, rows: int) -> None:
        import winpty

        self._pty = winpty.PTY(cols, rows)
        self._pty.spawn(argv[0], cwd=cwd)

    def read(self, size: int = 65536) -> bytes:
        try:
            return self._pty.read(size).encode("utf-8", "replace")
        except Exception:
            return b""

    def write(self, data: bytes) -> None:
        self._pty.write(data.decode("utf-8", "replace"))

    def resize(self, cols: int, rows: int) -> None:
        with contextlib.suppress(Exception):
            self._pty.set_size(cols, rows)

    @property
    def alive(self) -> bool:
        return bool(self._pty.isalive())

    def close(self) -> None:
        with contextlib.suppress(Exception):
            del self._pty


class _PipeTerminal:
    """Fallback: a shell on plain pipes. No TTY, but commands still run."""

    def __init__(self, argv: list[str], cwd: str | None, cols: int, rows: int) -> None:
        self._process = subprocess.Popen(
            argv,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=cwd,
            bufsize=0,
        )
        self._lock = threading.Lock()

    def read(self, size: int = 65536) -> bytes:
        assert self._process.stdout is not None
        return self._process.stdout.read1(size) or b""

    def write(self, data: bytes) -> None:
        assert self._process.stdin is not None
        with self._lock:
            self._process.stdin.write(data)
            self._process.stdin.flush()

    def resize(self, cols: int, rows: int) -> None:
        """No-op: pipes have no window size."""

    @property
    def alive(self) -> bool:
        return self._process.poll() is None

    def close(self) -> None:
        with contextlib.suppress(OSError):
            self._process.kill()


def open_terminal(
    *,
    argv: list[str] | None = None,
    cwd: str | None = None,
    cols: int = 80,
    rows: int = 24,
) -> Terminal:
    """Open the best terminal this platform can provide."""
    argv = argv or default_shell()
    if not WINDOWS:
        return _PosixTerminal(argv, cwd, cols, rows)
    try:
        return _WinptyTerminal(argv, cwd, cols, rows)
    except Exception:
        # pywinpty missing or ConPTY unavailable -- degrade rather than fail.
        return _PipeTerminal(argv, cwd, cols, rows)


def has_true_tty() -> bool:
    """Whether a real TTY is available, for reporting capabilities to the UI."""
    if not WINDOWS:
        return True
    try:
        import winpty  # noqa: F401

        return True
    except ImportError:
        return False
