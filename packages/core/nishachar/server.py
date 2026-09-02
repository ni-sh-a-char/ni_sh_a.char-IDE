"""The HTTP + WebSocket API, and the server behind the standalone IDE.

Security notes, because this server's entire job is to execute code:

* The local runner is refused on any non-loopback bind address unless you
  explicitly opt in. Exposing "POST me code and I'll run it as you" to a
  network is a remote shell, not a feature.
* CORS is closed by default. An open ``Access-Control-Allow-Origin`` on a
  localhost server means any page you browse can execute code on your machine.
  Embedding from another origin is opt-in, per origin.
* The ``Host`` header is validated, which is what stops DNS rebinding from
  turning a loopback-only server into a remote one.
* The terminal endpoint is off unless enabled.
"""

from __future__ import annotations

import asyncio
import ipaddress
import json
from pathlib import Path

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Mount, Route, WebSocketRoute
from starlette.staticfiles import StaticFiles
from starlette.websockets import WebSocket, WebSocketDisconnect

from . import __version__
from .registry import registry
from .runners import DEFAULT_OUTPUT_LIMIT, DEFAULT_TIMEOUT, ExecutionError, get_runner
from .runners.local import LocalRunner

STATIC = Path(__file__).parent / "static"
MAX_CODE_BYTES = 1024 * 1024  # 1 MiB of source is already absurd
MAX_TIMEOUT = 120.0


class Settings:
    """Everything the server needs to know, resolved once at startup."""

    def __init__(
        self,
        *,
        runner: str = "auto",
        host: str = "127.0.0.1",
        cors: tuple[str, ...] = (),
        allow_shell: bool = False,
        allow_remote_exec: bool = False,
        allowed_hosts: tuple[str, ...] = (),
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.runner_name = runner
        self.host = host
        self.cors = tuple(cors)
        self.allow_shell = allow_shell
        self.allowed_hosts = tuple(allowed_hosts)
        self.timeout = timeout
        self.runner = get_runner(runner)
        self._local_probe = LocalRunner()

        if not is_loopback(host) and runner != "docker" and not allow_remote_exec:
            raise ExecutionError(
                f"Refusing to serve the {runner!r} runner on {host}, which is not "
                "loopback. Unsandboxed execution reachable from a network is a "
                "remote shell. Use --runner docker, or pass --allow-remote-exec "
                "if you genuinely intend this."
            )


def is_loopback(host: str) -> bool:
    if host in ("localhost", ""):
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _allowed_hosts(settings: Settings) -> set[str]:
    """Host header values we will answer to."""
    return {
        "localhost", "127.0.0.1", "::1", "[::1]",
        settings.host,
        *settings.allowed_hosts,
    }


def _host_ok(request: Request | WebSocket, settings: Settings) -> bool:
    """Reject a mismatched Host header, which is how DNS rebinding is caught.

    Only enforced for a loopback bind. Rebinding is an attack on servers that
    are *supposed* to be private: a hostile page resolves its own domain to
    127.0.0.1 and then talks to your localhost server from its own origin. A
    deliberately exposed server is reached by hostnames we cannot predict, so
    enforcing a guess there would break legitimate use without adding safety.
    """
    if not is_loopback(settings.host):
        return True
    header = request.headers.get("host", "")
    name = header.rsplit(":", 1)[0] if header.count(":") == 1 else header
    return name.strip("[]").lower() in {h.strip("[]").lower() for h in _allowed_hosts(settings)}


# -- routes ---------------------------------------------------------------


async def health(request: Request) -> JSONResponse:
    settings: Settings = request.app.state.settings
    return JSONResponse(
        {
            "name": "ni_sh_a.char-IDE",
            "version": __version__,
            "runner": settings.runner_name,
            "languages": len(registry),
            "shell": settings.allow_shell,
        }
    )


async def languages(request: Request) -> JSONResponse:
    settings: Settings = request.app.state.settings
    probe = settings._local_probe
    payload = []
    for language in registry:
        entry = language.to_dict()
        entry["localToolchain"] = probe.supports(language)
        payload.append(entry)
    return JSONResponse({"languages": payload, "count": len(payload)})


async def run(request: Request) -> JSONResponse:
    settings: Settings = request.app.state.settings
    if not _host_ok(request, settings):
        return JSONResponse({"error": "host not allowed"}, status_code=421)

    try:
        body = await request.json()
    except (json.JSONDecodeError, ValueError):
        return JSONResponse({"error": "body must be JSON"}, status_code=400)

    code = body.get("code", "")
    if not isinstance(code, str):
        return JSONResponse({"error": "'code' must be a string"}, status_code=400)
    if len(code.encode("utf-8")) > MAX_CODE_BYTES:
        return JSONResponse({"error": "source too large"}, status_code=413)

    language = registry.get(str(body.get("language", "")))
    if language is None:
        return JSONResponse(
            {"error": f"unknown language {body.get('language')!r}"}, status_code=404
        )

    # Note the ordering: `body.get("stdin") or ""` would quietly turn a falsy
    # non-string such as [] into "", so validate before defaulting.
    stdin = body.get("stdin", "")
    if stdin is None:
        stdin = ""
    if not isinstance(stdin, str):
        return JSONResponse({"error": "'stdin' must be a string"}, status_code=400)

    try:
        timeout = min(float(body.get("timeout") or settings.timeout), MAX_TIMEOUT)
    except (TypeError, ValueError):
        return JSONResponse({"error": "'timeout' must be a number"}, status_code=400)

    try:
        # Executing blocks; keep the event loop free so the UI stays responsive.
        result = await asyncio.to_thread(
            settings.runner.run,
            code,
            language,
            stdin=stdin,
            timeout=timeout,
            output_limit=DEFAULT_OUTPUT_LIMIT,
        )
    except ExecutionError as exc:
        return JSONResponse({"error": str(exc)}, status_code=422)

    return JSONResponse(result.to_dict())


async def terminal(websocket: WebSocket) -> None:
    """Bidirectional shell. Only reachable when --allow-shell was passed."""
    settings: Settings = websocket.app.state.settings
    if not settings.allow_shell or not _host_ok(websocket, settings):
        await websocket.close(code=4403)
        return

    from .pty_bridge import open_terminal

    await websocket.accept()
    term = open_terminal()
    loop = asyncio.get_running_loop()
    stop = asyncio.Event()

    async def pump_out() -> None:
        """Shell output -> browser."""
        try:
            while not stop.is_set():
                chunk = await loop.run_in_executor(None, term.read)
                if not chunk:
                    break
                await websocket.send_text(chunk.decode("utf-8", "replace"))
        except (WebSocketDisconnect, RuntimeError):
            pass
        finally:
            stop.set()

    pumping = asyncio.create_task(pump_out())
    try:
        while not stop.is_set():
            message = await websocket.receive_text()
            try:
                parsed = json.loads(message)
            except json.JSONDecodeError:
                term.write(message.encode("utf-8"))
                continue
            if parsed.get("type") == "resize":
                term.resize(int(parsed.get("cols", 80)), int(parsed.get("rows", 24)))
            else:
                term.write(str(parsed.get("data", "")).encode("utf-8"))
    except WebSocketDisconnect:
        pass
    finally:
        stop.set()
        term.close()
        pumping.cancel()


async def index(request: Request) -> PlainTextResponse:
    """Served only when the built IDE shell is missing."""
    return PlainTextResponse(
        "ni_sh_a.char-IDE API is running, but the IDE bundle was not built.\n"
        "Build it with:  cd packages/web && npm install && npm run build\n"
        f"\nAPI: GET /api/languages ({len(registry)} languages), POST /api/run\n",
        status_code=200,
    )


def create_app(settings: Settings | None = None) -> Starlette:
    settings = settings or Settings()

    routes = [
        Route("/api/health", health),
        Route("/api/languages", languages),
        Route("/api/run", run, methods=["POST"]),
        WebSocketRoute("/api/pty", terminal),
    ]
    if STATIC.is_dir() and (STATIC / "index.html").exists():
        routes.append(Mount("/", StaticFiles(directory=STATIC, html=True)))
    else:
        routes.append(Route("/", index))

    middleware = []
    if settings.cors:
        middleware.append(
            Middleware(
                CORSMiddleware,
                allow_origins=list(settings.cors),
                allow_methods=["GET", "POST", "OPTIONS"],
                allow_headers=["content-type"],
            )
        )

    app = Starlette(routes=routes, middleware=middleware)
    app.state.settings = settings
    return app


def serve(
    *,
    host: str = "127.0.0.1",
    port: int = 8777,
    runner: str = "auto",
    cors: tuple[str, ...] = (),
    allow_shell: bool = False,
    allow_remote_exec: bool = False,
    allowed_hosts: tuple[str, ...] = (),
    timeout: float = DEFAULT_TIMEOUT,
    log_level: str = "warning",
) -> None:
    import uvicorn

    settings = Settings(
        runner=runner,
        host=host,
        cors=cors,
        allow_shell=allow_shell,
        allow_remote_exec=allow_remote_exec,
        allowed_hosts=allowed_hosts,
        timeout=timeout,
    )
    uvicorn.run(create_app(settings), host=host, port=port, log_level=log_level)
