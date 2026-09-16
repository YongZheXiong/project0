#!/usr/bin/env python3
"""One-consumption operator shell for the visible H6 matrix successor.

This wrapper never discovers ports and never flashes firmware. It retains the
accepted first cell from the consumed predecessor, then derives strict records
for cells 2..24 from one reviewed successor approval. Every motion interval is
delegated to m2a_calibration_console. Any invalid input or failed run ends the
batch without retrying.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m2a_calibration_console as console
import m2a_slowdrive_profile as profile


PLAN_ID = "H60-H6-SINGLE-WHEEL-MATRIX-VISIBLE-RESUME-20260910-002"
PREDECESSOR_PLAN_ID = "H60-H6-SINGLE-WHEEL-MATRIX-20260910-001"
START_INDEX = 2
RETAINED_RESULT_SHA256 = "a79d0dd3bf231b8a2d80ccffd54bd551a1fe690869a0f7f12c1a2159983c0b32"
RETAINED_OBSERVATION_SHA256 = "070d7dee0016722b81deab76a36355c35351933f1922e23dcb2a6fe13f63d5ac"
PREDECESSOR_FLOW_SHA256 = "db3e2671ff81caeb59ba7c8851a25d27c008b034de439f75b458df884f1d525f"
PREDECESSOR_BATCH_SHA256 = "fad919ffcbdf5bac901a3b1a3562f0070011e26fe2c55b99f3978ae2cbc9aec6"
EXCLUDED_RUN_02_RESULT_SHA256 = "2eeeac631a2184ed48e4195fd2f72754253246ca07b164cd6f142212d0458163"
MATRIX = tuple(
    {"channel": channel, "direction": direction, "duty_permille": duty}
    for channel in ("MA", "MB", "MC", "MD")
    for direction in ("plus", "minus")
    for duty in (50, 80, 120)
)
WHEEL_LABELS = {
    "MA": "右前(RF)",
    "MB": "左前(LF)",
    "MC": "右后(RR)",
    "MD": "左后(LR)",
}
OBSERVATION_TOKENS = {
    "FRONT_OK": "toward_front",
    "REAR_OK": "toward_rear",
    "NO_MOVE_OK": "not_moved",
}


class H6BatchError(RuntimeError):
    pass


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _validate_predecessor_manifest(path):
    manifest_path = Path(path).expanduser().resolve()
    if not manifest_path.is_file():
        raise H6BatchError("predecessor manifest is missing")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = {
        "schema": "project0.h6.visible-resume-predecessor.v1",
        "plan_id": PREDECESSOR_PLAN_ID,
        "status": "STOPPED_NO_RETRY",
        "retained_completed_cells": [dict(MATRIX[0])],
        "resume_start_index": START_INDEX,
        "flow_result_sha256": PREDECESSOR_FLOW_SHA256,
        "batch_result_sha256": PREDECESSOR_BATCH_SHA256,
        "retained_result_sha256": RETAINED_RESULT_SHA256,
        "retained_observation_sha256": RETAINED_OBSERVATION_SHA256,
        "excluded_run_02_result_sha256": EXCLUDED_RUN_02_RESULT_SHA256,
        "excluded_run_02_reason": "target wheel physical observation unavailable",
    }
    if any(manifest.get(key) != value for key, value in expected.items()):
        raise H6BatchError("predecessor manifest does not bind the accepted prefix")
    result_name = manifest.get("retained_result_file")
    observation_name = manifest.get("retained_observation_file")
    if (not isinstance(result_name, str) or Path(result_name).name != result_name
            or not isinstance(observation_name, str)
            or Path(observation_name).name != observation_name):
        raise H6BatchError("predecessor evidence filenames are invalid")
    root = manifest_path.parent
    retained_result = root / result_name
    retained_observation = root / observation_name
    if not retained_result.is_file() or not retained_observation.is_file():
        raise H6BatchError("retained predecessor evidence is missing")
    if (_sha256(retained_result) != RETAINED_RESULT_SHA256
            or _sha256(retained_observation) != RETAINED_OBSERVATION_SHA256):
        raise H6BatchError("retained predecessor evidence hash mismatch")
    return manifest_path, manifest, retained_result, retained_observation


def validate(args):
    firmware = Path(args.firmware_bin).expanduser().resolve()
    evidence_root = Path(args.evidence_root).expanduser().resolve()
    approval = Path(args.package_approval).expanduser().resolve()
    predecessor_path, predecessor, retained_result, retained_observation = (
        _validate_predecessor_manifest(args.predecessor_manifest))
    if not firmware.is_file() or profile.H6_MANIFEST not in firmware.read_bytes():
        raise H6BatchError("firmware is not the exact H6 R1 artifact")
    actual_sha = console.sha256_file(firmware)
    if actual_sha != args.expected_sha256.lower():
        raise H6BatchError("firmware SHA-256 mismatch")
    if not evidence_root.is_dir():
        raise H6BatchError("evidence root must already exist")
    if not sys.stdin.isatty():
        raise H6BatchError("interactive TTY is required")
    record = json.loads(approval.read_text(encoding="utf-8"))
    expected = {
        "approved": True,
        "plan_id": PLAN_ID,
        "profile": profile.H6_PROFILE,
        "firmware_sha256": actual_sha,
        "matrix": list(MATRIX),
        "resume_start_index": START_INDEX,
        "predecessor_plan_id": PREDECESSOR_PLAN_ID,
        "predecessor_manifest_sha256": _sha256(predecessor_path),
    }
    if any(record.get(key) != value for key, value in expected.items()):
        raise H6BatchError("package approval does not exactly bind plan, matrix and firmware")
    if not isinstance(record.get("user_message"), str) or not record["user_message"].strip():
        raise H6BatchError("package approval lacks the user's exact authorization message")
    return (firmware, evidence_root, approval, actual_sha, record["user_message"],
            predecessor_path, predecessor, retained_result, retained_observation)


def _consume(approval):
    with approval.with_name(approval.name + ".consumed").open("x", encoding="utf-8") as stream:
        stream.write("H6 field batch invocation consumed; no automatic retry.\n")


def _run_args(args, firmware, actual_sha, root, run_approval, cell):
    return argparse.Namespace(
        port=args.port,
        channel=cell["channel"],
        direction=cell["direction"],
        duty_permille=cell["duty_permille"],
        max_session_ms=600,
        trigger_mode="one-shot",
        one_shot_profile=profile.H6_PROFILE,
        firmware_bin=str(firmware),
        expected_sha256=actual_sha,
        approval_code=profile.H6_APPROVAL_CODE,
        run_approval=str(run_approval),
        evidence_root=str(root),
        batch_managed_closeout=True,
    )


def run_batch(args):
    (firmware, evidence_root, approval, actual_sha, user_message,
     predecessor_path, predecessor, retained_result, retained_observation) = validate(args)
    _consume(approval)
    root = Path(tempfile.mkdtemp(prefix="h6_batch_", dir=evidence_root))
    summary = {
        "schema": "project0.h6.field-batch.v2",
        "plan_id": PLAN_ID,
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "firmware_sha256": actual_sha,
        "predecessor": {
            "plan_id": PREDECESSOR_PLAN_ID,
            "manifest": str(predecessor_path),
            "retained_completed_cells": predecessor["retained_completed_cells"],
            "retained_result": str(retained_result),
            "retained_observation": str(retained_observation),
            "excluded_run_02_result_sha256": EXCLUDED_RUN_02_RESULT_SHA256,
        },
        "resume_start_index": START_INDEX,
        "completed": [],
        "closeout_confirmed": False,
        "status": "RUNNING",
    }
    error = None
    try:
        print("本包仅允许H60-only、四轮稳固架空、轮周净空、四路最终线束固定，"
              "Orin/Mid360隔离，主开关随手可达；当前静止、无异响/异味/发热/松动。")
        if input("实时条件全部满足输入 H6_FIELD_READY，否则取消：").strip() != "H6_FIELD_READY":
            raise H6BatchError("operator did not confirm the live field gate")
        for number, cell in enumerate(MATRIX[START_INDEX - 1:], START_INDEX):
            run_approval = root / f"run_{number:02d}_approval.json"
            run_approval.write_text(json.dumps({
                "approved": True,
                "profile": profile.H6_PROFILE,
                **cell,
                "max_session_ms": 600,
                "firmware_sha256": actual_sha,
                "user_message": f"Umbrella authorization {PLAN_ID}: {user_message}",
            }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            wheel = WHEEL_LABELS[cell["channel"]]
            other_wheels = " / ".join(
                label for channel, label in WHEEL_LABELS.items()
                if channel != cell["channel"])
            print(f"[{number:02d}/24] {cell['channel']}={wheel} / "
                  f"{cell['direction']} / {cell['duty_permille']}‰")
            print(f"本段只允许 {wheel} 动；其余 {other_wheels} 均不得活动。")
            print(f"请先把视线移到 {wheel}，确认能连续看完整个约0.6秒窗口，再按回车触发。")
            run_path = console.run_console(
                _run_args(args, firmware, actual_sha, root, run_approval, cell))
            token = input("轮已物理停止、支撑/线束无变化且无异常；"
                          "输入 FRONT_OK / REAR_OK / NO_MOVE_OK：").strip()
            if token not in OBSERVATION_TOKENS:
                raise H6BatchError(f"run {number}: physical observation not accepted")
            observation = {
                **cell,
                "wheel_top_direction": OBSERVATION_TOKENS[token],
                "physical_stop_normal": True,
                "support_unchanged": True,
                "no_anomaly": True,
                "operator_token": token,
                "result": str(Path(run_path) / "result.json"),
            }
            observation_path = root / f"run_{number:02d}_physical.json"
            observation_path.write_text(json.dumps(observation, ensure_ascii=False,
                                                   indent=2) + "\n", encoding="utf-8")
            summary["completed"].append({
                **cell, "result": observation["result"],
                "observation": str(observation_path),
            })
        print("续跑第2--24段已结束。现在拔COM、关主开关、物理断开电池，"
              "确认H60灯灭且支撑/板卡/轮毂/线束无异常。")
        if input("完成后输入 CLOSEOUT_OK：").strip() != "CLOSEOUT_OK":
            raise H6BatchError("final physical closeout not confirmed")
        summary["closeout_confirmed"] = True
        summary["status"] = "PASS_DIGITAL_AND_OPERATOR_OBSERVATIONS"
    except BaseException as exc:
        error = exc
        summary["status"] = "STOPPED_NO_RETRY"
        summary["error"] = f"{type(exc).__name__}: {exc}"
        print("批次已停止，不会自动重试。拔COM、关主开关、物理断开电池并检查异常。",
              file=sys.stderr)
    finally:
        summary["finished_utc"] = datetime.now(timezone.utc).isoformat()
        (root / "batch_result.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if error is not None:
        raise error
    return root


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", required=True)
    parser.add_argument("--firmware-bin", required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--package-approval", required=True)
    parser.add_argument("--predecessor-manifest", required=True)
    parser.add_argument("--evidence-root", required=True)
    return parser


def main():
    try:
        run_batch(build_parser().parse_args())
    except (H6BatchError, console.CalibrationConsoleError, OSError, ValueError,
            KeyboardInterrupt) as exc:
        print(f"H6 batch refused/stopped: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
