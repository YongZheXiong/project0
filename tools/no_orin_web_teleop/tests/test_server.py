import json
from pathlib import Path
from tempfile import TemporaryDirectory
import threading
import time
import unittest
from urllib.error import HTTPError
from urllib import request

from no_orin_web_teleop.fake_serial import FakeH60Serial
from no_orin_web_teleop.controller import ControllerConfig
from no_orin_web_teleop.server import make_server, validate_bind_host


class ServerTests(unittest.TestCase):
    def test_watchdog_stops_motion_when_browser_sends_nothing_else(self):
        with TemporaryDirectory() as directory:
            log_path = Path(directory) / "watchdog.jsonl"
            server = make_server(
                host="127.0.0.1", port=0, log_jsonl=log_path,
                controller_config=ControllerConfig(
                    command_lease_ms=80, max_loop_gap_ms=1000
                ),
            )
            thread = threading.Thread(target=server.serve_forever)
            thread.start()
            try:
                with server.controller_lock:
                    server.controller.handle_intent("ARM_REQUEST", client_id="old", sequence=1)
                    server.controller.handle_intent("FORWARD_LOW", client_id="old", sequence=2)
                deadline = time.monotonic() + 1.0
                while time.monotonic() < deadline:
                    if any(item["reason"] == "lease_expired"
                           for item in server.controller.h60.commands):
                        break
                    time.sleep(0.01)
                with server.controller_lock:
                    self.assertEqual(server.controller.state.value, "DISARMED")
                    self.assertIn("lease_expired", [item["reason"]
                                  for item in server.controller.h60.commands])
                    events = [json.loads(line) for line in log_path.read_text().splitlines()]
                self.assertTrue(any(item["endpoint"] == "backend_watchdog"
                                    and item["result"]["reason"] == "lease_expired_stop"
                                    for item in events))
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2.0)

    def test_validate_bind_host_refuses_network_addresses(self):
        self.assertEqual(validate_bind_host("localhost"), "127.0.0.1")
        self.assertEqual(validate_bind_host("127.0.0.1"), "127.0.0.1")
        with self.assertRaises(ValueError):
            validate_bind_host("0.0.0.0")
        with self.assertRaises(ValueError):
            validate_bind_host("192.168.1.20")

    def test_http_intent_round_trip_uses_fake_serial_only(self):
        server = make_server(host="127.0.0.1", port=0)
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        try:
            host, port = server.server_address
            body = json.dumps(
                {"intent": "ARM_REQUEST", "client_id": "test", "sequence": 1}
            ).encode("utf-8")
            req = request.Request(
                f"http://{host}:{port}/api/intent",
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with request.urlopen(req, timeout=2.0) as response:
                payload = json.loads(response.read().decode("utf-8"))
            self.assertTrue(payload["result"]["accepted"])
            self.assertEqual(payload["state"]["h60"]["identity"], "FAKE-H60-W0")
            self.assertEqual(server.controller.h60.commands[-1]["command"], "ARM")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2.0)

    def test_http_safety_endpoint_exports_w1_5_lock_state(self):
        server = make_server(host="127.0.0.1", port=0)
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        try:
            host, port = server.server_address
            with request.urlopen(f"http://{host}:{port}/api/safety", timeout=2.0) as response:
                payload = json.loads(response.read().decode("utf-8"))
            self.assertEqual(payload["gate"], "W1.5")
            self.assertEqual(payload["mode"], "OFFLINE_FAKE_SERIAL_ONLY")
            self.assertEqual(payload["next_gate"]["status"], "LOCKED")
            self.assertIn("w2_w3_field_run", payload["prohibited_actions"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2.0)

    def test_static_page_uses_chinese_operator_labels(self):
        server = make_server(host="127.0.0.1", port=0)
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        try:
            host, port = server.server_address
            with request.urlopen(f"http://{host}:{port}/", timeout=2.0) as response:
                html = response.read().decode("utf-8")

            for expected in (
                "无 Orin 本机安全控制台",
                "停止",
                "解除使能",
                "申请使能",
                "按住前进",
                "按住后退",
                "假串口场景",
                "安全边界",
                "当前允许",
                "保持锁定",
            ):
                self.assertIn(expected, html)

            for stale_label in (
                ">STOP<",
                ">DISARM<",
                ">ARM<",
                ">Lease<",
                ">Direction<",
                ">Allowed<",
                ">Locked<",
                ">Fake H60<",
            ):
                self.assertNotIn(stale_label, html)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2.0)

    def test_injected_field_link_disables_fake_scenario_endpoint(self):
        link = FakeH60Serial(identity="H60-COM-TEST")
        server = make_server(
            host="127.0.0.1",
            port=0,
            h60=link,
            allow_fake_scenarios=False,
            safety_builder=lambda state: {"mode": "REAL_H60_W2_FIELD_PACKAGE"},
        )
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        try:
            host, port = server.server_address
            body = json.dumps({"scenario": "fault"}).encode("utf-8")
            req = request.Request(
                f"http://{host}:{port}/api/fake_serial/scenario",
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with self.assertRaises(HTTPError) as caught:
                request.urlopen(req, timeout=2.0)
            self.assertEqual(caught.exception.code, 403)
            with request.urlopen(f"http://{host}:{port}/api/safety", timeout=2.0) as response:
                payload = json.loads(response.read().decode("utf-8"))
            self.assertEqual(payload["mode"], "REAL_H60_W2_FIELD_PACKAGE")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2.0)

    def test_audit_write_failure_after_profile_forces_stop_and_fault(self):
        with TemporaryDirectory() as directory:
            server = make_server(host="127.0.0.1", port=0)
            link = server.controller.h60
            server.controller.handle_intent("ARM_REQUEST", now_ms=1, sequence=1)
            server.controller.handle_intent("FORWARD_LOW", now_ms=2, sequence=2)
            self.assertEqual(link.commands[-1]["command"], "PROFILE_FORWARD_LOW")
            server.log_jsonl = Path(directory)  # a directory cannot be opened as a log file
            try:
                with self.assertRaises(OSError):
                    server.persist_event({"intent": "FORWARD_LOW"})
                self.assertEqual(link.commands[-1]["command"], "STOP")
                self.assertEqual(server.controller.state.value, "FAULT")
                self.assertEqual(server.controller.fault_reason, "audit_log_failure")
            finally:
                server.server_close()


if __name__ == "__main__":
    unittest.main()
