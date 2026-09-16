import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "h6_parameter_analysis", ROOT / "tools" / "h6_parameter_analysis.py")
analysis = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(analysis)


def result(channel="MA", direction="plus", duty=50, net=146, duration=500.0):
    index = analysis.CHANNELS[channel]
    initial = [100, 200, 300, 400]
    final = list(initial)
    final[index] += net
    telemetry = lambda counts: {
        "firmware_version": [0, 2, 11], "encoder_count": counts,
        "encoder_delta": [0, 0, 0, 0], "state": 1, "fault": 0,
        "motion_output_available": True, "self_test_ok": True,
        "boot_fault_code": 0, "capabilities": 2, "session_id": 0,
        "sequence": 1,
    }
    return {
        "arguments": {"one_shot_profile": analysis.PROFILE,
                      "trigger_mode": "one-shot"},
        "digital_run_pass": True, "serial_opened": True,
        "serial_closed": True, "stop_confirmed": True,
        "output_requested": True, "channel": channel,
        "direction": direction, "duty_permille": duty,
        "initial_telemetry": telemetry(initial),
        "final_telemetry": telemetry(final),
        "parser_stats": {"discarded_bytes": 0, "length_errors": 0,
                         "version_errors": 0, "crc_errors": 0},
        "run_trace": {"nonzero_tx_to_stop_attempt_ms": duration,
                      "nonzero_commands": 18, "stop_confirmed": True},
    }


def observation(channel, direction, duty):
    return {"channel": channel, "direction": direction,
            "duty_permille": duty, "wheel_top_direction": "toward_front",
            "physical_stop_normal": True, "support_unchanged": True,
            "no_anomaly": True}


class H6ParameterAnalysisTests(unittest.TestCase):
    def test_complete_matrix_is_still_candidate_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            results, observations = [], []
            for channel in analysis.CHANNELS:
                for direction in analysis.DIRECTIONS:
                    for duty in analysis.DUTIES:
                        result_path = root / f"{channel}-{direction}-{duty}.json"
                        obs_path = root / f"{channel}-{direction}-{duty}-physical.json"
                        result_path.write_text(json.dumps(result(channel, direction, duty)))
                        obs_path.write_text(json.dumps(observation(channel, direction, duty)))
                        results.append(result_path)
                        observations.append(obs_path)
            report = analysis.analyze(results,
                {channel: 205.0 for channel in analysis.CHANNELS}, observations)
            self.assertTrue(report["matrix_complete"])
            self.assertFalse(report["production_parameters_frozen"])
            self.assertEqual(len(report["runs"]), 24)
            self.assertAlmostEqual(report["runs"][0]["startup_window_counts_per_second"],
                                   292.0)
            self.assertIn("Kp/Ki", " ".join(report["blockers"]))
            self.assertEqual(report["transient_coverage"]["raw_serial_runs"], 0)
            self.assertEqual(report["transient_coverage"]["steady_state_status"],
                             "NOT_ESTABLISHED")

    def test_missing_and_corrupt_evidence_are_refused_or_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "one.json"
            path.write_text(json.dumps(result()))
            report = analysis.analyze([path])
            self.assertFalse(report["matrix_complete"])
            self.assertEqual(len(report["missing_digital_cells"]), 23)
            corrupt = result()
            corrupt["final_telemetry"]["encoder_count"][1] += 1
            path.write_text(json.dumps(corrupt))
            with self.assertRaises(analysis.H6EvidenceError):
                analysis.analyze([path])

    def test_bad_version_duration_or_observation_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for field, value in [("version", [0, 2, 8]), ("duration", 601.0)]:
                data = result()
                if field == "version":
                    data["final_telemetry"]["firmware_version"] = value
                else:
                    data["run_trace"]["nonzero_tx_to_stop_attempt_ms"] = value
                path = root / f"{field}.json"
                path.write_text(json.dumps(data))
                with self.subTest(field=field), self.assertRaises(analysis.H6EvidenceError):
                    analysis.analyze([path])
            good = root / "good.json"
            bad_observation = root / "bad-observation.json"
            good.write_text(json.dumps(result()))
            obs = observation("MA", "plus", 50)
            obs["physical_stop_normal"] = False
            bad_observation.write_text(json.dumps(obs))
            with self.assertRaises(analysis.H6EvidenceError):
                analysis.analyze([good], observation_paths=[bad_observation])

    def test_mixed_width_counter_wrap_is_unwrapped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cases = (
                ("MB", "plus", 50, 0, 65535, -1),
                ("MB", "minus", 120, 65095, 18, 459),
                ("MD", "plus", 50, 0, 65534, -2),
                ("MA", "plus", 80, -130, -555, -425),
            )
            paths = []
            for channel, direction, duty, before, after, expected in cases:
                data = result(channel, direction, duty, net=0)
                index = analysis.CHANNELS[channel]
                data["initial_telemetry"]["encoder_count"][index] = before
                data["final_telemetry"]["encoder_count"][index] = after
                path = root / f"{channel}-{direction}-{duty}.json"
                path.write_text(json.dumps(data))
                paths.append(path)
            report = analysis.analyze(paths)
            actual = {
                (row["channel"], row["direction"], row["duty_permille"]):
                    row["net_counts"]
                for row in report["runs"]
            }
            for channel, direction, duty, _before, _after, expected in cases:
                self.assertEqual(actual[(channel, direction, duty)], expected)
            self.assertEqual(report["engineering_counter_bits"],
                             {"MA": 32, "MB": 16, "MC": 32, "MD": 16})

    def test_half_range_or_out_of_range_counter_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ambiguous = result("MB", "plus", 50, net=0)
            ambiguous["initial_telemetry"]["encoder_count"][1] = 0
            ambiguous["final_telemetry"]["encoder_count"][1] = 32768
            ambiguous_path = root / "ambiguous.json"
            ambiguous_path.write_text(json.dumps(ambiguous))
            with self.assertRaises(analysis.H6EvidenceError):
                analysis.analyze([ambiguous_path])

            invalid = result("MD", "plus", 50, net=0)
            invalid["final_telemetry"]["encoder_count"][3] = 65536
            invalid_path = root / "invalid.json"
            invalid_path.write_text(json.dumps(invalid))
            with self.assertRaises(analysis.H6EvidenceError):
                analysis.analyze([invalid_path])

    def test_transient_summary_reports_frame_facts_without_steady_pass(self):
        data = result("MB", "plus", 80, net=-60, duration=500.0)
        data["run_trace"].update({
            "first_nonzero_tx_monotonic": 10.0,
            "stop_attempt_monotonic": 10.5,
        })
        telemetry = [
            {"time": 10.05, "count": [0, 100, 0, 0]},
            {"time": 10.15, "count": [0, 90, 0, 0]},
            {"time": 10.25, "count": [0, 70, 0, 0]},
            {"time": 10.35, "count": [0, 40, 0, 0]},
            {"time": 10.45, "count": [0, 0, 0, 0]},
        ]
        summary = analysis._transient_from_telemetry(data, telemetry, "MB")
        self.assertEqual(summary["telemetry_frame_count"], 5)
        self.assertEqual(summary["interval_count"], 4)
        self.assertAlmostEqual(summary["observed_span_ms"], 400.0)
        for actual, expected in zip(summary["interval_counts_per_second"],
                                    [-100.0, -200.0, -300.0, -400.0]):
            self.assertAlmostEqual(actual, expected)
        self.assertTrue(summary["latest_interval_magnitude_exceeds_previous"])
        self.assertTrue(summary["observed_nonzero_direction_consistent"])
        self.assertEqual(summary["steady_state_classification"],
                         "NOT_ESTABLISHED_STARTUP_INCLUSIVE_WINDOW")

    def test_transient_summary_rejects_non_increasing_time(self):
        data = result()
        data["run_trace"].update({
            "first_nonzero_tx_monotonic": 1.0,
            "stop_attempt_monotonic": 2.0,
        })
        telemetry = [
            {"time": 1.5, "count": [0, 0, 0, 0]},
            {"time": 1.5, "count": [1, 0, 0, 0]},
        ]
        with self.assertRaises(analysis.H6EvidenceError):
            analysis._transient_from_telemetry(data, telemetry, "MA")


if __name__ == "__main__":
    unittest.main()
