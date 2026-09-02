"""API behaviour, with emphasis on the boundaries that keep it safe."""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from nishachar.runners import ExecutionError
from nishachar.server import Settings, create_app, is_loopback

# TestClient sends Host: testserver, so it has to be an accepted name.
TEST_HOSTS = ("testserver",)


@pytest.fixture
def client():
    app = create_app(Settings(runner="local", allowed_hosts=TEST_HOSTS))
    with TestClient(app) as test_client:
        yield test_client


def test_health_reports_the_registry_size(client):
    body = client.get("/api/health").json()
    assert body["languages"] >= 60
    assert body["shell"] is False, "the terminal must be off unless asked for"


def test_languages_are_listed_with_local_availability(client):
    body = client.get("/api/languages").json()
    assert body["count"] == len(body["languages"])
    python = next(x for x in body["languages"] if x["id"] == "python")
    assert python["localToolchain"] is True
    assert python["template"]


def test_run_executes_and_returns_output(client):
    body = client.post("/api/run", json={"language": "python", "code": 'print("api")'}).json()
    assert body["stdout"] == "api\n"
    assert body["exitCode"] == 0
    assert body["ok"] is True


def test_run_accepts_an_alias(client):
    body = client.post("/api/run", json={"language": "py", "code": "print(1)"}).json()
    assert body["stdout"] == "1\n"


def test_run_honours_a_timeout(client):
    body = client.post(
        "/api/run", json={"language": "py", "code": "while True: pass", "timeout": 1}
    ).json()
    assert body["timedOut"] is True
    assert body["exitCode"] == 124


def test_unknown_language_is_a_404(client):
    response = client.post("/api/run", json={"language": "klingon", "code": "x"})
    assert response.status_code == 404


@pytest.mark.parametrize(
    "payload",
    [
        {"language": "py", "code": 123},
        {"language": "py", "code": "x", "stdin": []},
        {"language": "py", "code": "x", "timeout": "soon"},
    ],
)
def test_malformed_payloads_are_rejected(client, payload):
    assert client.post("/api/run", json=payload).status_code == 400


def test_non_json_body_is_rejected(client):
    response = client.post(
        "/api/run", content=b"not json", headers={"content-type": "application/json"}
    )
    assert response.status_code == 400


def test_oversized_source_is_rejected(client):
    response = client.post("/api/run", json={"language": "py", "code": "#" * (2 * 1024 * 1024)})
    assert response.status_code == 413


def test_a_forged_host_header_is_refused(client):
    """Blocks DNS rebinding: a hostile page resolving its domain to 127.0.0.1."""
    response = client.post(
        "/api/run", json={"language": "py", "code": "print(1)"}, headers={"host": "evil.example"}
    )
    assert response.status_code == 421


def test_host_check_is_not_enforced_on_a_deliberately_exposed_server():
    """An exposed server is reached by hostnames we cannot predict."""
    app = create_app(Settings(runner="docker", host="0.0.0.0"))
    with TestClient(app) as exposed:
        response = exposed.get("/api/health", headers={"host": "build-box.internal"})
        assert response.status_code == 200


def test_cors_is_closed_unless_configured(client):
    response = client.get("/api/languages", headers={"origin": "https://evil.example"})
    assert "access-control-allow-origin" not in response.headers


def test_cors_opens_only_for_the_configured_origin():
    app = create_app(
        Settings(runner="local", cors=("https://trusted.example",), allowed_hosts=TEST_HOSTS)
    )
    with TestClient(app) as configured:
        allowed = configured.get("/api/languages", headers={"origin": "https://trusted.example"})
        assert allowed.headers.get("access-control-allow-origin") == "https://trusted.example"

        denied = configured.get("/api/languages", headers={"origin": "https://evil.example"})
        assert denied.headers.get("access-control-allow-origin") != "https://evil.example"


def test_terminal_is_refused_when_the_shell_is_disabled(client):
    from starlette.websockets import WebSocketDisconnect

    with pytest.raises(WebSocketDisconnect), client.websocket_connect("/api/pty"):
        pass


def test_local_runner_is_refused_on_a_public_address():
    """Unsandboxed execution reachable from a network is a remote shell."""
    with pytest.raises(ExecutionError, match="Refusing to serve"):
        Settings(runner="local", host="0.0.0.0")


def test_public_address_is_allowed_with_docker_or_an_explicit_override():
    Settings(runner="docker", host="0.0.0.0")
    Settings(runner="local", host="0.0.0.0", allow_remote_exec=True)


@pytest.mark.parametrize(
    ("host", "expected"),
    [("127.0.0.1", True), ("localhost", True), ("::1", True), ("0.0.0.0", False), ("10.0.0.5", False)],
)
def test_loopback_detection(host, expected):
    assert is_loopback(host) is expected
