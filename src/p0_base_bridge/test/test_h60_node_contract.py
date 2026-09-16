import re
import unittest
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[3]
NODE = REPOSITORY / "src/p0_base_bridge/p0_base_bridge/node.py"
MESSAGE = REPOSITORY / "src/p0_interfaces/msg/ChassisStatus.msg"
CONFIG = REPOSITORY / "src/p0_bringup/config/base_control.yaml"

ENGINEERING_FIELDS = {
    "engineering_encoder_ready",
    "engineering_encoder_profile",
    "engineering_forward_count_lf",
    "engineering_forward_count_lr",
    "engineering_forward_count_rf",
    "engineering_forward_count_rr",
    "engineering_revolutions_lf",
    "engineering_revolutions_lr",
    "engineering_revolutions_rf",
    "engineering_revolutions_rr",
}


class H60NodeContractTest(unittest.TestCase):
    def test_read_only_engineering_fields_and_motion_locks_stay_explicit(self):
        node = NODE.read_text(encoding="utf-8")
        message = MESSAGE.read_text(encoding="utf-8")
        config = CONFIG.read_text(encoding="utf-8")

        declared_fields = []
        for line in message.splitlines():
            content = line.split("#", 1)[0].strip()
            if content:
                self.assertRegex(content, r"^[A-Za-z0-9_/]+\s+[a-z0-9_]+$")
                declared_fields.append(content.split()[1])

        self.assertEqual(len(declared_fields), len(set(declared_fields)))
        self.assertTrue(ENGINEERING_FIELDS.issubset(declared_fields))
        for field in ENGINEERING_FIELDS:
            self.assertEqual(
                len(re.findall(rf"message\.{re.escape(field)}\s*=", node)),
                1,
                field,
            )

        self.assertIn("_last_engineering_encoder_time", node)
        self.assertIn("self._engineering_encoder.status(", node)
        self.assertNotIn("nav_msgs", node)
        self.assertNotIn("Odometry", node)
        self.assertRegex(config, r"(?m)^\s*motion_commands_enabled:\s*false\s*$")
        self.assertRegex(config, r"(?m)^\s*wheel_mapping_confirmed:\s*false\s*$")
        self.assertRegex(config, r"(?m)^\s*wheel_target_limit_mmps:\s*0\s*$")


if __name__ == "__main__":
    unittest.main()
