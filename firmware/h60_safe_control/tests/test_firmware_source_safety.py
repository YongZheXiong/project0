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

    def test_iwdg_reset_reason_is_captured_then_cleared(self):
        source = (ROOT / "src" / "p0_hw_stm32f407.c").read_text(
            encoding="utf-8"
        )
        start = source.index("uint32_t p0_hw_take_retained_fault(void)")
        end = source.index("void p0_hw_fault_trap", start)
        function = source[start:end]

        self.assertIn("RCC_CSR_IWDGRSTF", function)
        self.assertIn("P0_HW_FAULT_IWDG_RESET", function)
        self.assertIn("reset_observer_valid", function)
        self.assertIn("P0_RESET_OBSERVER_MAGIC", function)
        self.assertIn("RCC_CSR |= RCC_CSR_RMVF", function)

    def test_iwdg_diagnostic_is_motion_locked_and_force_safe(self):
        config = (ROOT / "include" / "p0_build_config.h").read_text(
            encoding="utf-8"
        )
        hardware = (ROOT / "src" / "p0_hw_stm32f407.c").read_text(
            encoding="utf-8"
        )
        main = (ROOT / "src" / "main.c").read_text(encoding="utf-8")

        self.assertIn("IWDG diagnostic requires a motion-locked isolated build", config)
        self.assertIn("P0_MOTION_OUTPUT_COMPILED != 0", config)
        stall_start = hardware.index("void p0_hw_iwdg_diagnostic_stall(void)")
        stall_end = hardware.index("uint32_t p0_hw_take_retained_fault", stall_start)
        stall = hardware[stall_start:stall_end]
        self.assertLess(stall.index("p0_hw_motor_force_safe(0)"), stall.index("for (;;)"))
        self.assertIn("p0_iwdg_diagnostic_should_stall", main)
        self.assertIn("p0_iwdg_diagnostic_should_trigger_exception", main)
        self.assertIn("P0_HW_FAULT_IWDG_RESET", main)
        trigger_start = hardware.index(
            "void p0_hw_exception_diagnostic_trigger(void)"
        )
        trigger_end = hardware.index(
            "uint32_t p0_hw_take_retained_fault", trigger_start
        )
        trigger = hardware[trigger_start:trigger_end]
        force_safe = trigger.index("p0_hw_motor_force_safe(0)")
        wait_tc = trigger.index("USART_SR_TC")
        timeout_assert = trigger.index("P0_HW_ASSERT(timeout != 0)")
        exception = trigger.index("udf #0")
        self.assertLess(
            force_safe,
            wait_tc,
        )
        self.assertLess(wait_tc, timeout_assert)
        self.assertLess(timeout_assert, exception)
        self.assertIn("USART_TX_COMPLETE_TIMEOUT_CYCLES", trigger)

        uart_start = hardware.index(
            "void p0_hw_uart_write(const uint8_t *data, size_t length)"
        )
        uart_end = hardware.index("void p0_hw_encoder_read", uart_start)
        uart_write = hardware[uart_start:uart_end]
        self.assertIn("USART_SR_TXE", uart_write)
        self.assertNotIn("USART_SR_TC", uart_write)


class MotionSourceSafetyTests(unittest.TestCase):
    def test_default_build_keeps_motion_and_calibration_disabled(self):
        config = (ROOT / "include" / "p0_build_config.h").read_text(
            encoding="utf-8"
        )
        makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

        self.assertIn("#define P0_MOTION_OUTPUT_COMPILED 0", config)
        self.assertIn("#define P0_MOTION_CALIBRATION_VALID 0", config)
        self.assertIn("#define P0_M2A_CALIBRATION_BUILD 0", config)
        self.assertIn("#define P0_H6_EXTENDED_WINDOW_BUILD 0", config)
        self.assertIn("#define P0_W2_FOUR_WHEEL_PROFILE_BUILD 0", config)
        self.assertIn("#define P0_W2_FIVE_SECOND_LINK_LOSS_BUILD 0", config)
        self.assertIn("M1 has no frozen H60 channel", config)
        self.assertIn("-DP0_MOTION_OUTPUT_COMPILED=0", makefile)
        self.assertIn("-DP0_MOTION_CALIBRATION_VALID=0", makefile)

    def test_w2_four_wheel_profile_is_default_off_fixed_and_isolated(self):
        config = (ROOT / "include" / "p0_build_config.h").read_text(
            encoding="utf-8"
        )
        slow = (ROOT / "include" / "p0_m2a_slowdrive.h").read_text(
            encoding="utf-8"
        )
        sequence = (ROOT / "include" / "p0_m2a_slowdrive_sequence.h").read_text(
            encoding="utf-8"
        )
        manifest = (ROOT / "src" / "p0_manifest.c").read_text(encoding="utf-8")
        makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

        self.assertIn("W2 four-wheel profile requires", config)
        self.assertIn('"0.2.13-W2-FWDREV-R1"', config)
        self.assertIn("P0_W2_PROFILE_CHANNEL UINT8_C(0xF0)", slow)
        self.assertIn("P0_W2_TARGET_DUTY_PERMILLE UINT16_C(80)", slow)
        self.assertIn("MA/MB/MC/MD", sequence)
        self.assertIn("(int8_t)-s->direction", sequence)
        self.assertIn("FOUR_CHANNEL_PROFILE=1", manifest)
        self.assertIn("FORWARD_SIGNS=-1,+1,-1,+1", manifest)
        self.assertIn("DIRECTION_CHANGE_REARM=1", manifest)
        self.assertIn("w2-four-wheel-profile-firmware", makefile)
        self.assertIn("-DP0_W2_FOUR_WHEEL_PROFILE_BUILD=1", makefile)
        self.assertIn("w2-five-second-link-loss-firmware", makefile)
        self.assertIn('"0.2.14-W2-LINK5-OFFLINE-R1"', config)
        self.assertIn("LINK_LOSS_CANDIDATE=1", manifest)

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

    def test_h6_r2_is_a_separate_default_off_build_with_fixed_limits(self):
        config = (ROOT / "include" / "p0_build_config.h").read_text(
            encoding="utf-8"
        )
        slow = (ROOT / "include" / "p0_m2a_slowdrive.h").read_text(
            encoding="utf-8"
        )
        manifest = (ROOT / "src" / "p0_manifest.c").read_text(
            encoding="utf-8"
        )
        makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

        self.assertIn("H6 extended window requires", config)
        self.assertIn('"0.2.12-H6-SINGLE-R2"', config)
        self.assertIn("P0_SLOW_MAX_ARMED_MS UINT32_C(2500)", slow)
        self.assertIn("P0_H6_R2_RAMP_UP_MS UINT32_C(300)", slow)
        self.assertIn("P0_H6_R2_HOLD_MS UINT32_C(1200)", slow)
        self.assertIn("P0_H6_R2_RAMP_DOWN_MS UINT32_C(300)", slow)
        self.assertIn("P0_H6_R2_CHANNEL UINT8_C(2)", slow)
        self.assertIn("P0_H6_R2_TARGET_DUTY_PERMILLE UINT16_C(80)", slow)
        self.assertIn("HOLD_LEASE_MS=75;MAX_ARMED_MS=2500", manifest)
        self.assertIn("h6-extended-window-firmware", makefile)
        self.assertIn("-DP0_H6_EXTENDED_WINDOW_BUILD=1", makefile)

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
