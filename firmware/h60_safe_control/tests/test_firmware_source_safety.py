import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class WatchdogSourceSafetyTests(unittest.TestCase):
    def test_iwdg_starts_lsi_before_update_wait(self):
        source = (ROOT / "src" / "p0_hw_stm32f407.c").read_text(
            encoding="utf-8"
        )
        start = source.index("void p0_hw_watchdog_start(void)")
        end = source.index("void p0_hw_watchdog_feed(void)", start)
        function = source[start:end]

        self.assertLess(function.index("0xCCCC"), function.index("0x5555"))
        self.assertIn("IWDG_SR_UPDATE_MASK", function)
        self.assertIn("timeout != 0", function)
        self.assertIn("P0_HW_ASSERT(timeout != 0)", function)


if __name__ == "__main__":
    unittest.main()
