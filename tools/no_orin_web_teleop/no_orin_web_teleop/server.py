"""Localhost-only HTTP server for the Project0 W0 fake-serial teleop tool."""

from __future__ import annotations

from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
from typing import Any

from .controller import ControllerConfig, WebTeleopController
from .fake_serial import FakeH60Serial, VALID_SCENARIOS
from .safety import build_safety_panel_state


LOCAL_BIND_HOSTS = {"127.0.0.1", "localhost", "::1"}
STATIC_ROOT = Path(__file__).resolve().parents[1] / "static"


def validate_bind_host(host: str) -> str:
    value = (host or "127.0.0.1").strip()
    if value not in LOCAL_BIND_HOSTS:
        raise ValueError("W0 backend may only bind to localhost/127.0.0.1/::1")
    return "127.0.0.1" if value == "localhost" else value


class W0HTTPServer(ThreadingHTTPServer):
    def __init__(
        self,
        server_address: tuple[str, int],
        handler_class: type[BaseHTTPRequestHandler],
        *,
        controller: WebTeleopController,
        log_jsonl: Path | None,
        safety_builder: Any = build_safety_panel_state,
        allow_fake_scenarios: bool = True,
    ) -> None:
        super().__init__(server_address, handler_class)
        self.controller = controller
        self.log_jsonl = log_jsonl
        self.safety_builder = safety_builder
        self.allow_fake_scenarios = bool(allow_fake_scenarios)
        self.controller_lock = threading.RLock()
        self.log_lock = threading.Lock()

    def serve_forever(self, poll_interval: float = 0.02) -> None:
        super().serve_forever(poll_interval=poll_interval)

    def service_actions(self) -> None:
        # The browser may vanish without delivering /api/disconnect or another GET.
        with self.controller_lock:
            result = self.controller.tick()
            if result.reason != "tick":
                self.persist_event({
                    "endpoint": "backend_watchdog",
                    "result": result.as_dict(),
                    "state": self.controller.export_state(),
                })

    def persist_event(self, payload: dict[str, Any]) -> None:
        if self.log_jsonl is None:
            return
        with self.log_lock:
            try:
                self.log_jsonl.parent.mkdir(parents=True, exist_ok=True)
                with self.log_jsonl.open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps(payload, ensure_ascii=False) + "\n")
            except OSError:
                self.controller.audit_failure()
                raise


class W0RequestHandler(BaseHTTPRequestHandler):
    server: W0HTTPServer

    def log_message(self, fmt: str, *args: Any) -> None:
        return

    def do_GET(self) -> None:
        if self.path in ("/", "/index.html"):
            self._send_file(STATIC_ROOT / "index.html", "text/html; charset=utf-8")
            return
        if self.path == "/app.js":
            self._send_file(STATIC_ROOT / "app.js", "text/javascript; charset=utf-8")
            return
        if self.path == "/styles.css":
            self._send_file(STATIC_ROOT / "styles.css", "text/css; charset=utf-8")
            return
        if self.path == "/api/state":
            with self.server.controller_lock:
                self._send_json(self.server.controller.export_state())
            return
        if self.path == "/api/safety":
            with self.server.controller_lock:
                state = self.server.controller.export_state()
                self._send_json(self.server.safety_builder(state))
            return
        self.send_error(404)

    def do_POST(self) -> None:
        try:
            payload = self._read_json()
            if self.path == "/api/intent":
                with self.server.controller_lock:
                    result = self.server.controller.handle_intent(
                        str(payload.get("intent", "")),
                        client_id=str(payload.get("client_id", "browser")),
                        sequence=payload.get("sequence"),
                    )
                    body = {"result": result.as_dict(), "state": self.server.controller.export_state()}
                    self.server.persist_event({"endpoint": self.path, **body})
                self._send_json(body)
                return
            if self.path == "/api/disconnect":
                with self.server.controller_lock:
                    result = self.server.controller.client_disconnect(
                        client_id=str(payload.get("client_id", "browser"))
                    )
                    body = {"result": result.as_dict(), "state": self.server.controller.export_state()}
                    self.server.persist_event({"endpoint": self.path, **body})
                self._send_json(body)
                return
            if self.path == "/api/fake_serial/scenario":
                if not self.server.allow_fake_scenarios:
                    self._send_json({"ok": False, "error": "fake scenarios disabled"}, status=403)
                    return
                scenario = str(payload.get("scenario", ""))
                if scenario not in VALID_SCENARIOS:
                    self._send_json({"ok": False, "error": "unknown scenario"}, status=400)
                    return
                with self.server.controller_lock:
                    self.server.controller.set_fake_scenario(scenario)
                    state = self.server.controller.export_state()
                    body = {"ok": True, "state": state}
                    self.server.persist_event({"endpoint": self.path, **body})
                self._send_json(body)
                return
            self.send_error(404)
        except (json.JSONDecodeError, ValueError, TypeError) as error:
            self._send_json({"ok": False, "error": str(error)}, status=400)
        except OSError:
            with self.server.controller_lock:
                state = self.server.controller.export_state()
            self._send_json(
                {"ok": False, "error": "audit_log_failure", "state": state},
                status=503,
            )

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        if not raw:
            return {}
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("JSON payload must be an object")
        return payload

    def _send_file(self, path: Path, content_type: str) -> None:
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, payload: dict[str, Any], *, status: int = 200) -> None:
        data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)


def make_server(
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
    log_jsonl: Path | None = None,
    h60: Any | None = None,
    safety_builder: Any = build_safety_panel_state,
    allow_fake_scenarios: bool = True,
    controller_config: ControllerConfig | None = None,
) -> W0HTTPServer:
    safe_host = validate_bind_host(host)
    controller = WebTeleopController(
        h60 if h60 is not None else FakeH60Serial(), config=controller_config
    )
    handler = partial(W0RequestHandler)
    return W0HTTPServer(
        (safe_host, port),
        handler,
        controller=controller,
        log_jsonl=log_jsonl,
        safety_builder=safety_builder,
        allow_fake_scenarios=allow_fake_scenarios,
    )


def run_server(
    *, host: str = "127.0.0.1", port: int = 8765, log_jsonl: Path | None = None
) -> None:
    with make_server(host=host, port=port, log_jsonl=log_jsonl) as server:
        server.serve_forever()
