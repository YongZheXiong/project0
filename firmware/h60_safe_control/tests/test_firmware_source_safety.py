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


class MotionSourceSafetyTests(unittest.TestCase):
    def test_default_build_keeps_motion_and_calibration_disabled(self):
        config = (ROOT / "include" / "p0_build_config.h").read_text(
            encoding="utf-8"
        )
        makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

        self.assertIn("#define P0_MOTION_OUTPUT_COMPILED 0", config)
        self.assertIn("#define P0_MOTION_CALIBRATION_VALID 0", config)
        self.assertIn("#define P0_M2A_CALIBRATION_BUILD 0", config)
        self.assertIn("M1 has no frozen H60 channel", config)
        self.assertIn("-DP0_MOTION_OUTPUT_COMPILED=0", makefile)
        self.assertIn("-DP0_MOTION_CALIBRATION_VALID=0", makefile)

    def test_m2a_build_is_explicit_and_keeps_closed_loop_calibration_invalid(self):
        config = (ROOT / "include" / "p0_build_config.h").read_text(
            encoding="utf-8"
        )
        makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
        calibration = (ROOT / "include" / "p0_m2a_calibration.h").read_text(
            encoding="utf-8"
        )

        self.assertIn("P0_M2A_CALIBRATION_BUILD", config)
        self.assertIn("P0_MOTION_CALIBRATION_VALID == 0", config)
        self.assertIn("m2a-calibration-firmware", makefile)
        self.assertIn("-DP0_M2A_CALIBRATION_BUILD=1", makefile)
        self.assertIn("P0_M2A_HOLD_LEASE_MS UINT32_C(75)", calibration)
        self.assertIn("P0_M2A_MAX_ARMED_MS UINT32_C(1000)", calibration)
        self.assertIn("P0_M2A_MAX_DUTY_PERMILLE UINT16_C(120)", calibration)

    def test_pwm_path_is_compile_guarded_and_force_safe_clears_every_ccr(self):
        source = (ROOT / "src" / "p0_hw_stm32f407.c").read_text(
            encoding="utf-8"
        )
        guard = source.index("#if P0_MOTION_OUTPUT_COMPILED != 0")
        pwm_init = source.index("static void motor_pwm_timer_init(void)")
        fallback = source.index("#else", pwm_init)
        force_start = source.index("void p0_hw_motor_force_safe(void *unused)")
        force_end = source.index("#if P0_MOTION_OUTPUT_COMPILED", force_start)
        force = source[force_start:force_end]

        self.assertLess(guard, pwm_init)
        self.assertLess(pwm_init, fallback)
        for register in (
            "TIM9->CCR1 = 0",
            "TIM9->CCR2 = 0",
            "TIM1->CCR1 = 0",
            "TIM1->CCR2 = 0",
            "TIM1->CCR3 = 0",
            "TIM1->CCR4 = 0",
            "TIM12->CCR1 = 0",
            "TIM12->CCR2 = 0",
        ):
            self.assertIn(register, force)

    def test_runtime_availability_requires_compiled_output_and_calibration(self):
        source = (ROOT / "src" / "main.c").read_text(encoding="utf-8")
        self.assertIn(
            "P0_MOTION_RUNTIME_AVAILABLE && motion_config_valid", source
        )
        self.assertIn("p0_motion_reset(&g_motion)", source)
        self.assertIn("p0_hw_motor_force_safe(0)", source)

    def test_pwm_channel_order_matches_ma_through_md_schematic_order(self):
        source = (ROOT / "src" / "p0_hw_stm32f407.c").read_text(
            encoding="utf-8"
        )
        start = source.index("void p0_hw_motor_apply_pwm", source.index("#if"))
        end = source.index("\n}\n\n#else", start) + 2
        function = source[start:end]
        expected = (
            "apply_pair(0, output_permille[0], &TIM1->CCR1, &TIM1->CCR2)",
            "apply_pair(1, output_permille[1], &TIM1->CCR3, &TIM1->CCR4)",
            "apply_pair(2, output_permille[2], &TIM9->CCR1, &TIM9->CCR2)",
            "apply_pair(3, output_permille[3], &TIM12->CCR1, &TIM12->CCR2)",
        )
        positions = [function.index(item) for item in expected]
        self.assertEqual(positions, sorted(positions))

    def test_m2a_hardware_guard_rejects_multichannel_or_excess_duty(self):
        source = (ROOT / "src" / "p0_hw_stm32f407.c").read_text(
            encoding="utf-8"
        )
        start = source.index("void p0_hw_motor_apply_pwm", source.index("#if"))
        end = source.index("\n}\n\n#else", start) + 2
        function = source[start:end]
        self.assertIn("P0_M2A_CALIBRATION_BUILD", function)
        self.assertIn("P0_M2A_MAX_DUTY_PERMILLE", function)
        self.assertIn("nonzero > UINT8_C(1)", function)
        self.assertGreaterEqual(function.count("p0_hw_motor_force_safe(0)"), 2)


if __name__ == "__main__":
    unittest.main()
