"""ni_sh_a.char-IDE -- run any language, anywhere.

A polyglot execution engine, a local IDE, and an embeddable component.

Use it as a library::

    import nishachar

    result = nishachar.run('say "hi"', "she")
    print(result.stdout, result.exit_code)

Or from the shell::

    nishachar run hello.she
    nishachar            # opens the IDE in your browser
"""

from __future__ import annotations

from pathlib import Path

from .registry import Language, Registry, registry
from .runners import (
    DEFAULT_OUTPUT_LIMIT,
    DEFAULT_TIMEOUT,
    AutoRunner,
    DockerRunner,
    ExecResult,
    ExecutionError,
    LocalRunner,
    get_runner,
)

__version__ = "2.0.0"
__all__ = [
    "DEFAULT_OUTPUT_LIMIT",
    "DEFAULT_TIMEOUT",
    "AutoRunner",
    "DockerRunner",
    "ExecResult",
    "ExecutionError",
    "Language",
    "LocalRunner",
    "Registry",
    "__version__",
    "get_runner",
    "languages",
    "registry",
    "run",
    "run_file",
]


def languages() -> list[Language]:
    """Every language the registry knows about, sorted by display name."""
    return list(registry)


def run(
    code: str,
    language: str,
    *,
    runner: str = "auto",
    stdin: str = "",
    timeout: float = DEFAULT_TIMEOUT,
    output_limit: int = DEFAULT_OUTPUT_LIMIT,
) -> ExecResult:
    """Execute a snippet and return the result.

    ``language`` accepts an id, alias or extension: ``"python"``, ``"py"`` and
    ``".py"`` all work.
    """
    target = registry.require(language)
    return get_runner(runner).run(
        code, target, stdin=stdin, timeout=timeout, output_limit=output_limit
    )


def run_file(path: str | Path, *, language: str = "", **kwargs) -> ExecResult:
    """Execute a file, inferring the language from its extension."""
    path = Path(path)
    target = registry.require(language) if language else registry.for_file(path)
    if target is None:
        raise ExecutionError(
            f"Could not tell what language {path.name!r} is. "
            "Pass language= explicitly."
        )
    return run(path.read_text(encoding="utf-8"), target.id, **kwargs)
