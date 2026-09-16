#!/usr/bin/env python3
"""Validate H6 single-wheel evidence and summarize startup-window metrics.

The report is deliberately not a production-parameter generator. A 600 ms
open-loop run can falsify channel isolation, direction and stopping claims, but
cannot by itself freeze steady-state speed, ramp limits or PI gains.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import importlib.util
import json
from pathlib import Path


CHANNELS = {"MA": 0, "MB": 1, "MC": 2, "MD": 3}
CPR = {"MA": 2926, "MB": 2923, "MC": 2929, "MD": 2922}
COUNTER_BITS = {"MA": 32, "MB": 16, "MC": 32, "MD": 16}
DUTIES = (50, 80, 120)
DIRECTIONS = ("plus", "minus")
PROFILE = "h6-single-wheel-r1"
VERSION = [0, 2, 11]


class H6EvidenceError(ValueError):
    pass


_RUN_REVIEW = None


def _wrapped_delta(before, after, bits, channel):
    minimum = -(1 << 31) if bits == 32 else 0
    maximum = (1 << 31) - 1 if bits == 32 else (1 << bits) - 1
    if type(before) is not int or type(after) is not int:
        raise H6EvidenceError(f"{channel}: encoder count is not an integer")
    if not minimum <= before <= maximum or not minimum <= after <= maximum:
        raise H6EvidenceError(f"{channel}: encoder count outside {bits}-bit telemetry range")
    modulus = 1 << bits
    half_range = modulus >> 1
    delta = ((after & (modulus - 1)) - (before & (modulus - 1))) & (modulus - 1)
    if delta == half_range:
        raise H6EvidenceError(f"{channel}: encoder delta is exactly half-range and ambiguous")
    return delta - modulus if delta > half_range else delta


def _load(path):
    path = Path(path).expanduser().resolve()
    return path, json.loads(path.read_text(encoding="utf-8"))


def _load_run_review():
    """Load the sibling raw-log reviewer without depending on PYTHONPATH."""
    global _RUN_REVIEW
    if _RUN_REVIEW is None:
        path = Path(__file__).with_name("m2a_run_review.py")
        spec = importlib.util.spec_from_file_location("project0_m2a_run_review", path)
        if spec is None or spec.loader is None:
            raise H6EvidenceError(f"cannot load raw-log reviewer: {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _RUN_REVIEW = module
    return _RUN_REVIEW


def _transient_from_telemetry(result, telemetry, channel):
    """Summarize observed frame-to-frame motion without declaring steady state."""
    trace = result.get("run_trace", {})
    first = trace.get("first_nonzero_tx_monotonic")
    stop = trace.get("stop_attempt_monotonic")
    if not isinstance(first, (int, float)) or not isinstance(stop, (int, float)) or stop <= first:
        raise H6EvidenceError("nonzero/STOP timestamps are missing or invalid")
    selected = [item for item in telemetry if first <= item.get("time", -1) <= stop]
    index = CHANNELS[channel]
    rates = []
    for before, after in zip(selected, selected[1:]):
        duration = after["time"] - before["time"]
        if duration <= 0:
            raise H6EvidenceError(f"{channel}: transient telemetry time is not increasing")
        delta = _wrapped_delta(before["count"][index], after["count"][index],
                               COUNTER_BITS[channel], channel)
        rates.append(delta / duration)
    nonzero_signs = {(value > 0) - (value < 0) for value in rates if value}
    return {
        "telemetry_frame_count": len(selected),
        "interval_count": len(rates),
        "observed_span_ms": (
            (selected[-1]["time"] - selected[0]["time"]) * 1000.0
            if len(selected) >= 2 else 0.0),
        "interval_counts_per_second": rates,
        "latest_interval_counts_per_second": rates[-1] if rates else None,
        "latest_interval_magnitude_exceeds_previous": (
            abs(rates[-1]) > abs(rates[-2]) if len(rates) >= 2 else None),
        "observed_nonzero_direction_consistent": len(nonzero_signs) <= 1,
        "steady_state_classification": "NOT_ESTABLISHED_STARTUP_INCLUSIVE_WINDOW",
    }


def _transient_from_retained_log(path, result, channel):
    serial_path = path.parent / "serial.jsonl"
    if not serial_path.is_file():
        return {
            "raw_serial_available": False,
            "reason": "serial.jsonl was not retained with this copied result",
            "steady_state_classification": "NOT_ESTABLISHED_NO_RAW_TRANSIENT",
        }
    try:
        review = _load_run_review().review_run(path.parent)
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise H6EvidenceError(f"{path}: raw serial review failed: {error}") from error
    if review.get("digital_audit_pass") is not True:
        raise H6EvidenceError(f"{path}: raw serial review reports digital issues")
    summary = _transient_from_telemetry(result, review.get("telemetry", []), channel)
    summary["raw_serial_available"] = True
    summary["serial_jsonl"] = str(serial_path.resolve())
    return summary


def _validate_result(path, result):
    arguments = result.get("arguments", {})
    channel = result.get("channel")
    direction = result.get("direction")
    duty = result.get("duty_permille")
    trace = result.get("run_trace", {})
    initial = result.get("initial_telemetry", {})
    final = result.get("final_telemetry", {})
    parser = result.get("parser_stats", {})

    if (arguments.get("one_shot_profile") != PROFILE or
            arguments.get("trigger_mode") != "one-shot"):
        raise H6EvidenceError(f"{path}: not the H6 one-shot profile")
    if channel not in CHANNELS or direction not in DIRECTIONS or duty not in DUTIES:
        raise H6EvidenceError(f"{path}: run is outside the frozen H6 matrix")
    if not (result.get("digital_run_pass") and result.get("serial_opened") and
            result.get("serial_closed") and result.get("stop_confirmed") and
            result.get("output_requested")):
        raise H6EvidenceError(f"{path}: digital run/STOP/serial closeout incomplete")
    if any(parser.get(key) != 0 for key in
           ("discarded_bytes", "length_errors", "version_errors", "crc_errors")):
        raise H6EvidenceError(f"{path}: parser error present")
    if initial.get("firmware_version") != VERSION or final.get("firmware_version") != VERSION:
        raise H6EvidenceError(f"{path}: firmware version is not 0.2.11")
    before = initial.get("encoder_count")
    after = final.get("encoder_count")
    if not (isinstance(before, list) and isinstance(after, list) and
            len(before) == len(after) == 4):
        raise H6EvidenceError(f"{path}: encoder vectors malformed")
    selected = CHANNELS[channel]
    if any(after[index] != before[index] for index in range(4) if index != selected):
        raise H6EvidenceError(f"{path}: non-selected encoder changed")
    duration = trace.get("nonzero_tx_to_stop_attempt_ms")
    if not isinstance(duration, (int, float)) or not 0 < duration <= 600:
        raise H6EvidenceError(f"{path}: nonzero-to-STOP duration is outside 0..600 ms")
    if trace.get("nonzero_commands", 0) < 1 or not trace.get("stop_confirmed"):
        raise H6EvidenceError(f"{path}: nonzero command or STOP trace missing")
    net = _wrapped_delta(before[selected], after[selected],
                         COUNTER_BITS[channel], channel)
    return channel, direction, duty, net, float(duration)


def _validate_observation(path, observation, key):
    expected = dict(zip(("channel", "direction", "duty_permille"), key))
    if any(observation.get(name) != value for name, value in expected.items()):
        raise H6EvidenceError(f"{path}: physical observation does not match its run")
    if observation.get("wheel_top_direction") not in ("toward_front", "toward_rear", "not_moved"):
        raise H6EvidenceError(f"{path}: physical direction is missing")
    for field in ("physical_stop_normal", "support_unchanged", "no_anomaly"):
        if observation.get(field) is not True:
            raise H6EvidenceError(f"{path}: {field} is not confirmed")


def analyze(result_paths, circumference_mm=None, observation_paths=()):
    circumference_mm = circumference_mm or {}
    observations = {}
    for item in observation_paths:
        path, observation = _load(item)
        key = (observation.get("channel"), observation.get("direction"),
               observation.get("duty_permille"))
        _validate_observation(path, observation, key)
        if key in observations:
            raise H6EvidenceError(f"{path}: duplicate physical observation for {key}")
        observations[key] = str(path)

    rows = []
    seen = defaultdict(int)
    for item in result_paths:
        path, result = _load(item)
        channel, direction, duty, net, duration_ms = _validate_result(path, result)
        key = (channel, direction, duty)
        seen[key] += 1
        counts_per_second = net * 1000.0 / duration_ms
        row = {
            "result": str(path), "channel": channel, "direction": direction,
            "duty_permille": duty, "net_counts": net,
            "nonzero_to_stop_ms": duration_ms,
            "startup_window_counts_per_second": counts_per_second,
            "startup_window_revolutions_per_second": counts_per_second / CPR[channel],
            "physical_observation": observations.get(key),
            "transient": _transient_from_retained_log(path, result, channel),
        }
        if channel in circumference_mm:
            row["startup_window_mm_per_second"] = (
                counts_per_second / CPR[channel] * circumference_mm[channel])
        rows.append(row)

    expected = [(channel, direction, duty) for channel in CHANNELS
                for direction in DIRECTIONS for duty in DUTIES]
    missing_digital = [list(key) for key in expected if seen[key] == 0]
    missing_physical = [list(key) for key in expected if key not in observations]
    duplicate_runs = [list(key) + [count] for key, count in sorted(seen.items()) if count > 1]
    invalid_circumference = [channel for channel, value in circumference_mm.items()
                             if channel not in CHANNELS or not isinstance(value, (int, float))
                             or value <= 0]
    if invalid_circumference:
        raise H6EvidenceError(f"invalid measured circumference: {invalid_circumference}")

    blockers = []
    if missing_digital:
        blockers.append("24-cell MA..MD / plus-minus / 50-80-120 matrix incomplete")
    if missing_physical:
        blockers.append("matching physical direction/stop observations incomplete")
    if set(circumference_mm) != set(CHANNELS):
        blockers.append("four measured effective wheel circumferences incomplete")
    blockers.extend([
        "600 ms open-loop samples are startup-inclusive, not steady-state speed calibration",
        "ramp, reversal-zero, saturation recovery and Kp/Ki remain unmeasured",
        "VIN multi-point calibration remains separate",
        "final-load and final-tire-pressure revalidation remains required",
    ])
    raw_rows = [row for row in rows if row["transient"].get("raw_serial_available")]
    target_rows = [row for row in raw_rows if row["duty_permille"] in (80, 120)]
    target_spans = [row["transient"]["observed_span_ms"] for row in target_rows]
    target_intervals = [row["transient"]["interval_count"] for row in target_rows]
    target_increasing = sum(
        row["transient"]["latest_interval_magnitude_exceeds_previous"] is True
        for row in target_rows)
    return {
        "schema": "project0.h6.single-wheel-analysis.v1",
        "evidence_class": "OPEN_LOOP_STARTUP_WINDOW_CANDIDATE_ONLY",
        "production_parameters_frozen": False,
        "engineering_cpr_profile": "p2-e160-h60-engineering-cpr-v1",
        "engineering_cpr": CPR,
        "engineering_counter_bits": COUNTER_BITS,
        "measured_wheel_circumference_mm": circumference_mm,
        "runs": sorted(rows, key=lambda row: (row["channel"], row["direction"],
                                               row["duty_permille"], row["result"])),
        "missing_digital_cells": missing_digital,
        "missing_physical_cells": missing_physical,
        "duplicate_run_cells": duplicate_runs,
        "matrix_complete": not missing_digital and not missing_physical,
        "transient_coverage": {
            "raw_serial_runs": len(raw_rows),
            "runs_without_raw_serial": len(rows) - len(raw_rows),
            "duty_80_120_raw_runs": len(target_rows),
            "duty_80_120_interval_count_range": (
                [min(target_intervals), max(target_intervals)] if target_intervals else []),
            "duty_80_120_observed_span_ms_range": (
                [min(target_spans), max(target_spans)] if target_spans else []),
            "duty_80_120_latest_interval_magnitude_increased": target_increasing,
            "steady_state_status": "NOT_ESTABLISHED",
            "reason": (
                "Retained 80/120 permille runs are startup-inclusive and have no "
                "pre-frozen late-window stability criterion; interval facts are routing "
                "evidence only, not production speed calibration."),
        },
        "blockers": blockers,
    }


def _parse_circumference(items):
    values = {}
    for item in items:
        try:
            channel, raw = item.split("=", 1)
            values[channel] = float(raw)
        except ValueError as exc:
            raise H6EvidenceError(f"bad circumference {item!r}; use MA=number") from exc
    return values


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", action="append", default=[], required=True)
    parser.add_argument("--observation", action="append", default=[])
    parser.add_argument("--circumference-mm", action="append", default=[])
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = analyze(args.result, _parse_circumference(args.circumference_mm),
                     args.observation)
    Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                                 encoding="utf-8")


if __name__ == "__main__":
    main()
