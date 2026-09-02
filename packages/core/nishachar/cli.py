"""The ``nishachar`` command line.

    nishachar                    launch the IDE in your browser
    nishachar run hello.she      run a file, language inferred from extension
    nishachar run -l py -c '...' run a snippet
    nishachar languages          list what can be run
    nishachar serve --port 9000  API only, no browser
"""

from __future__ import annotations

import argparse
import contextlib
import os
import sys
import threading
import webbrowser
from pathlib import Path

from . import __version__
from .registry import registry
from .runners import DEFAULT_TIMEOUT, ExecutionError, get_runner
from .runners.local import LocalRunner

DEFAULT_PORT = 8777


def _colour() -> bool:
    return sys.stdout.isatty() and not os.environ.get("NO_COLOR")


def paint(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _colour() else text


DIM, BOLD, GREEN, RED, CYAN = "2", "1", "32", "31", "36"


def cmd_languages(args: argparse.Namespace) -> int:
    probe = LocalRunner()
    rows = []
    for language in registry:
        local = probe.supports(language)
        if args.available and not local:
            continue
        rows.append((language, local))

    width = max((len(lang.name) for lang, _ in rows), default=0)
    for language, local in rows:
        mark = paint("*", GREEN) if local else paint("-", DIM)
        exts = paint(" ".join(language.extensions), DIM)
        browser = paint(" browser", CYAN) if language.runs_in_browser else ""
        print(f" {mark} {language.name:<{width}}  {language.id:<14} {exts}{browser}")

    installed = sum(1 for _, local in rows if local)
    print(
        f"\n {len(registry)} languages registered, "
        f"{paint(str(installed), GREEN)} runnable with your installed toolchains "
        f"({paint('*', GREEN)}); the rest need Docker."
    )
    print(paint(" Add one in 8 lines of JSON: languages/README.md", DIM))
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    if args.code is not None:
        if not args.language:
            print("error: -c/--code requires -l/--language", file=sys.stderr)
            return 2
        source, language = args.code, registry.get(args.language)
    elif args.file == "-":
        source = sys.stdin.read()
        language = registry.get(args.language) if args.language else None
    else:
        path = Path(args.file)
        if not path.is_file():
            print(f"error: no such file: {path}", file=sys.stderr)
            return 2
        source = path.read_text(encoding="utf-8")
        language = registry.get(args.language) if args.language else registry.for_file(path)

    if language is None:
        hint = args.language or (args.file if args.file != "-" else "stdin")
        print(
            f"error: could not resolve a language for {hint!r}. "
            "Try 'nishachar languages', or pass -l/--language.",
            file=sys.stderr,
        )
        return 2

    try:
        result = get_runner(args.runner).run(
            source, language, stdin="", timeout=args.timeout
        )
    except ExecutionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if result.stdout:
        sys.stdout.write(result.stdout)
        if not result.stdout.endswith("\n"):
            sys.stdout.write("\n")
    if result.stderr:
        sys.stderr.write(result.stderr)
        if not result.stderr.endswith("\n"):
            sys.stderr.write("\n")

    if args.verbose:
        status = paint("ok", GREEN) if result.ok else paint(f"exit {result.exit_code}", RED)
        print(
            paint(
                f"[{language.name} via {result.runner}] {status} in {result.duration_ms}ms",
                DIM,
            ),
            file=sys.stderr,
        )
    return result.exit_code


def cmd_serve(args: argparse.Namespace, *, open_browser: bool) -> int:
    from .server import serve

    url = f"http://{'localhost' if args.host in ('127.0.0.1', '0.0.0.0') else args.host}:{args.port}"
    print(f" {paint('ni_sh_a.char-IDE', BOLD)} {__version__}  ·  {len(registry)} languages")
    print(f" {paint('→', CYAN)} {url}")
    print(f"   runner: {args.runner}  shell: {'on' if args.allow_shell else 'off'}")
    if args.allow_shell:
        print(paint("   warning: --allow-shell exposes an interactive shell.", RED))
    print(paint("   Ctrl+C to stop\n", DIM))

    if open_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()

    try:
        serve(
            host=args.host,
            port=args.port,
            runner=args.runner,
            cors=tuple(args.cors or ()),
            allow_shell=args.allow_shell,
            allow_remote_exec=args.allow_remote_exec,
            allowed_hosts=tuple(args.allowed_hosts or ()),
            timeout=args.timeout,
        )
    except ExecutionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nstopped")
    return 0


def _add_serve_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--host", default="127.0.0.1", help="bind address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"port (default: {DEFAULT_PORT})")
    parser.add_argument("--runner", default="auto", choices=["auto", "local", "docker"])
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="per-run seconds")
    parser.add_argument(
        "--cors",
        action="append",
        metavar="ORIGIN",
        help="allow embedding from this origin (repeatable). Closed by default.",
    )
    parser.add_argument(
        "--allow-shell",
        action="store_true",
        help="enable the interactive terminal endpoint (off by default)",
    )
    parser.add_argument(
        "--allowed-host",
        action="append",
        metavar="NAME",
        dest="allowed_hosts",
        help="additional Host header value to accept (repeatable)",
    )
    parser.add_argument(
        "--allow-remote-exec",
        action="store_true",
        help="permit the unsandboxed local runner on a non-loopback address",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nishachar",
        description="Run any language, anywhere.",
        epilog="With no arguments, launches the IDE in your browser.",
    )
    parser.add_argument("--version", action="version", version=f"ni_sh_a.char-IDE {__version__}")
    _add_serve_flags(parser)

    subs = parser.add_subparsers(dest="command")

    run_parser = subs.add_parser("run", help="execute a file or snippet")
    run_parser.add_argument("file", nargs="?", default="-", help="source file, or - for stdin")
    run_parser.add_argument("-l", "--language", help="language id, alias or extension")
    run_parser.add_argument("-c", "--code", help="run this snippet instead of a file")
    run_parser.add_argument("--runner", default="auto", choices=["auto", "local", "docker"])
    run_parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    run_parser.add_argument("-v", "--verbose", action="store_true", help="report timing to stderr")

    list_parser = subs.add_parser("languages", help="list supported languages")
    list_parser.add_argument(
        "--available", action="store_true", help="only those runnable with local toolchains"
    )

    serve_parser = subs.add_parser("serve", help="run the API server without opening a browser")
    _add_serve_flags(serve_parser)

    return parser


def _force_utf8() -> None:
    """Stop Unicode in our own output from crashing the process.

    Windows still hands back a cp1252 stream when stdout is redirected, so a
    box-drawing character or an arrow raises UnicodeEncodeError and takes the
    whole command down with it.
    """
    for stream in (sys.stdout, sys.stderr):
        with contextlib.suppress(AttributeError, OSError, ValueError):
            stream.reconfigure(encoding="utf-8", errors="replace")


def main(argv: list[str] | None = None) -> int:
    _force_utf8()
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        return cmd_run(args)
    if args.command == "languages":
        return cmd_languages(args)
    if args.command == "serve":
        return cmd_serve(args, open_browser=False)
    return cmd_serve(args, open_browser=True)


if __name__ == "__main__":
    sys.exit(main())
