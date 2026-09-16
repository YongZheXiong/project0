import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "h6_field_batch", ROOT / "tools" / "h6_field_batch.py")
batch = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(batch)


class H6FieldBatchTests(unittest.TestCase):
    def arguments(self, root):
        firmware = root / "h6.bin"
        firmware.write_bytes(batch.profile.H6_MANIFEST)
        digest = batch.console.sha256_file(firmware)
        retained_result = root / "retained_run_01_result.json"
        retained_observation = root / "retained_run_01_physical.json"
        retained_result.write_text('{"retained":"result"}\n')
        retained_observation.write_text('{"retained":"observation"}\n')
        retained_result_sha = hashlib.sha256(retained_result.read_bytes()).hexdigest()
        retained_observation_sha = hashlib.sha256(
            retained_observation.read_bytes()).hexdigest()
        predecessor = root / "predecessor_manifest.json"
        predecessor.write_text(json.dumps({
            "schema": "project0.h6.visible-resume-predecessor.v1",
            "plan_id": batch.PREDECESSOR_PLAN_ID,
            "status": "STOPPED_NO_RETRY",
            "retained_completed_cells": [dict(batch.MATRIX[0])],
            "resume_start_index": batch.START_INDEX,
            "flow_result_sha256": batch.PREDECESSOR_FLOW_SHA256,
            "batch_result_sha256": batch.PREDECESSOR_BATCH_SHA256,
            "retained_result_sha256": retained_result_sha,
            "retained_observation_sha256": retained_observation_sha,
            "retained_result_file": retained_result.name,
            "retained_observation_file": retained_observation.name,
            "excluded_run_02_result_sha256": batch.EXCLUDED_RUN_02_RESULT_SHA256,
            "excluded_run_02_reason": "target wheel physical observation unavailable",
        }))
        approval = root / "package_approval.json"
        approval.write_text(json.dumps({
            "approved": True,
            "plan_id": batch.PLAN_ID,
            "profile": batch.profile.H6_PROFILE,
            "firmware_sha256": digest,
            "matrix": list(batch.MATRIX),
            "resume_start_index": batch.START_INDEX,
            "predecessor_plan_id": batch.PREDECESSOR_PLAN_ID,
            "predecessor_manifest_sha256": hashlib.sha256(
                predecessor.read_bytes()).hexdigest(),
            "user_message": "OFFLINE TEST ONLY; no device authorization",
        }))
        return argparse.Namespace(port="/dev/fake", firmware_bin=str(firmware),
            expected_sha256=digest, package_approval=str(approval),
            predecessor_manifest=str(predecessor), evidence_root=str(root),
            test_retained_result_sha=retained_result_sha,
            test_retained_observation_sha=retained_observation_sha)

    def predecessor_bindings(self, args):
        return mock.patch.multiple(
            batch,
            RETAINED_RESULT_SHA256=args.test_retained_result_sha,
            RETAINED_OBSERVATION_SHA256=args.test_retained_observation_sha,
        )

    def test_exact_package_binding_and_tty(self):
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(batch.sys.stdin, "isatty", return_value=True):
            root = Path(tmp)
            args = self.arguments(root)
            with self.predecessor_bindings(args):
                self.assertEqual(batch.validate(args)[3], args.expected_sha256)
            record = json.loads(Path(args.package_approval).read_text())
            for key, value in [("plan_id", "wrong"), ("matrix", []),
                               ("approved", False), ("resume_start_index", 1),
                               ("predecessor_plan_id", "wrong")]:
                changed = dict(record)
                changed[key] = value
                Path(args.package_approval).write_text(json.dumps(changed))
                with self.subTest(key=key), self.predecessor_bindings(args), \
                        self.assertRaises(batch.H6BatchError):
                    batch.validate(args)
            Path(args.package_approval).write_text(json.dumps(record))
            with mock.patch.object(batch.sys.stdin, "isatty", return_value=False), \
                    self.predecessor_bindings(args), \
                    self.assertRaises(batch.H6BatchError):
                batch.validate(args)

    def test_predecessor_hash_drift_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(batch.sys.stdin, "isatty", return_value=True):
            args = self.arguments(Path(tmp))
            manifest = json.loads(Path(args.predecessor_manifest).read_text())
            retained = Path(args.predecessor_manifest).parent / manifest["retained_result_file"]
            retained.write_text("changed\n")
            with self.predecessor_bindings(args), self.assertRaises(batch.H6BatchError):
                batch.validate(args)

    def test_complete_successor_is_one_consumption_and_23_exact_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args = self.arguments(root)
            tokens = ["H6_FIELD_READY"] + ["FRONT_OK"] * 23 + ["CLOSEOUT_OK"]
            runs = []
            def fake_run(run_args):
                number = len(runs) + 1
                run_root = Path(run_args.evidence_root) / f"m2a_run_{number:02d}"
                run_root.mkdir()
                (run_root / "result.json").write_text("{}")
                runs.append((run_args.channel, run_args.direction,
                             run_args.duty_permille, run_args.max_session_ms,
                             json.loads(Path(run_args.run_approval).read_text())))
                return run_root
            with mock.patch.object(batch.sys.stdin, "isatty", return_value=True), \
                    mock.patch("builtins.input", side_effect=tokens), \
                    mock.patch.object(batch.console, "run_console", side_effect=fake_run), \
                    self.predecessor_bindings(args), io.StringIO() as printed, \
                    contextlib.redirect_stdout(printed):
                output = batch.run_batch(args)
                visible_output = printed.getvalue()
            self.assertEqual([(a, b, c) for a, b, c, _, _ in runs],
                             [(cell["channel"], cell["direction"],
                               cell["duty_permille"]) for cell in batch.MATRIX[1:]])
            self.assertTrue(all(max_ms == 600 for _, _, _, max_ms, _ in runs))
            self.assertTrue(all(record["firmware_sha256"] == args.expected_sha256
                                for *_, record in runs))
            summary = json.loads((output / "batch_result.json").read_text())
            self.assertEqual(summary["status"], "PASS_DIGITAL_AND_OPERATOR_OBSERVATIONS")
            self.assertTrue(summary["closeout_confirmed"])
            self.assertEqual(len(summary["completed"]), 23)
            self.assertEqual(summary["resume_start_index"], 2)
            self.assertEqual(summary["predecessor"]["retained_completed_cells"],
                             [dict(batch.MATRIX[0])])
            self.assertIn("[02/24] MA=右前(RF)", visible_output)
            self.assertIn("请先把视线移到 右前(RF)", visible_output)
            self.assertIn("[07/24] MB=左前(LF)", visible_output)
            self.assertIn("[13/24] MC=右后(RR)", visible_output)
            self.assertIn("[19/24] MD=左后(LR)", visible_output)
            self.assertTrue(Path(args.package_approval + ".consumed").is_file())

    def test_cancel_consumes_package_and_never_opens_device(self):
        with tempfile.TemporaryDirectory() as tmp:
            args = self.arguments(Path(tmp))
            with mock.patch.object(batch.sys.stdin, "isatty", return_value=True), \
                    mock.patch("builtins.input", return_value="cancel"), \
                    mock.patch.object(batch.console, "run_console") as run, \
                    self.predecessor_bindings(args):
                with self.assertRaises(batch.H6BatchError):
                    batch.run_batch(args)
                run.assert_not_called()
            self.assertTrue(Path(args.package_approval + ".consumed").is_file())
            outputs = list(Path(tmp).glob("h6_batch_*/batch_result.json"))
            self.assertEqual(len(outputs), 1)
            self.assertEqual(json.loads(outputs[0].read_text())["status"],
                             "STOPPED_NO_RETRY")


if __name__ == "__main__":
    unittest.main()
