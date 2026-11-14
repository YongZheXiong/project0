"""Static safety contract for the Orin return smoke launch."""

from pathlib import Path
import unittest


class OrinReturnLaunchContractTests(unittest.TestCase):
    def test_physical_endpoints_and_motion_are_isolated(self):
        text = (
            Path(__file__).resolve().parents[1]
            / "launch"
            / "orin_return_no_motion.launch.py"
        ).read_text(encoding="utf-8")
        required = (
            "/dev/project0_h60_isolated",
            "/dev/project0_joystick_isolated",
            '"motion_commands_enabled": False',
            '"wheel_mapping_confirmed": False',
            '"wheel_target_limit_mmps": 0',
            '"autonomy_enabled": False',
            '"mapping_confirmed": False',
        )
        for marker in required:
            self.assertIn(marker, text)
        self.assertNotIn("/dev/ttyTHS1", text)


if __name__ == "__main__":
    unittest.main()
