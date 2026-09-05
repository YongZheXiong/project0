#include "p0_motion.h"

#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHECK(condition)                                                       \
    do {                                                                       \
        if (!(condition)) {                                                    \
            fprintf(stderr, "FAIL %s:%d: %s\n", __FILE__, __LINE__,          \
                    #condition);                                               \
            exit(EXIT_FAILURE);                                                \
        }                                                                      \
    } while (0)

static p0_motion_config_t synthetic_config(void)
{
    p0_motion_config_t config;
    size_t i;

    memset(&config, 0, sizeof(config));
    config.control_period_ms = UINT32_C(10);
    config.maximum_target_mm_s = UINT16_C(1500);
    config.acceleration_mm_s2 = UINT16_C(1000);
    config.deceleration_mm_s2 = UINT16_C(1000);
    config.reversal_zero_hold_ms = UINT16_C(30);
    config.zero_speed_threshold_mm_s = UINT16_C(20);
    config.maximum_output_permille = UINT16_C(700);
    config.kp_q10 = INT32_C(2048);
    config.ki_q10_per_s = INT32_C(1024);
    for (i = 0; i < 4; ++i) {
        config.encoder_counts_per_revolution[i] = UINT32_C(1000);
        config.maximum_encoder_delta_counts[i] = UINT32_C(200);
        config.wheel_circumference_mm[i] = UINT32_C(1000);
        config.encoder_counter_bits[i] = UINT8_C(32);
        config.encoder_polarity[i] = INT8_C(1);
    }
    return config;
}

static void step_counts(
    p0_motion_controller_t *controller,
    int32_t count[4],
    int32_t delta,
    int16_t output[4])
{
    size_t i;
    for (i = 0; i < 4; ++i) {
        count[i] += delta;
    }
    CHECK(p0_motion_step(controller, count, output));
}

static void test_invalid_configuration_fails_closed(void)
{
    p0_motion_config_t config;
    p0_motion_controller_t controller;
    int16_t target[4] = {1, 1, 1, 1};
    int16_t output[4] = {7, 7, 7, 7};
    int32_t count[4] = {0, 0, 0, 0};

    memset(&config, 0, sizeof(config));
    CHECK(!p0_motion_init(&controller, &config));
    CHECK(!controller.config_valid);
    CHECK(!p0_motion_set_targets(&controller, target));
    CHECK(!p0_motion_step(&controller, count, output));
    CHECK(controller.output_permille[0] == 0);
}

static void test_speed_estimation_and_counter_wrap(void)
{
    p0_motion_config_t config = synthetic_config();
    p0_motion_controller_t controller;
    int32_t count[4] = {0, 65530, 0, 0};
    int16_t output[4];

    config.encoder_counter_bits[1] = UINT8_C(16);
    config.encoder_polarity[1] = INT8_C(-1);
    CHECK(p0_motion_init(&controller, &config));
    CHECK(p0_motion_step(&controller, count, output));
    count[0] = 10;
    count[1] = 4;
    count[2] = -10;
    count[3] = 0;
    CHECK(p0_motion_step(&controller, count, output));
    CHECK(controller.measured_speed_mm_s[0] == 1000);
    CHECK(controller.measured_speed_mm_s[1] == -1000);
    CHECK(controller.measured_speed_mm_s[2] == -1000);
    CHECK(controller.measured_speed_mm_s[3] == 0);
}

static void test_ramp_limit_and_anti_windup(void)
{
    p0_motion_config_t config = synthetic_config();
    p0_motion_controller_t controller;
    int32_t count[4] = {0, 0, 0, 0};
    int16_t target[4] = {1500, 0, 0, 0};
    int16_t output[4];
    size_t i;

    CHECK(p0_motion_init(&controller, &config));
    CHECK(p0_motion_step(&controller, count, output));
    CHECK(p0_motion_set_targets(&controller, target));
    step_counts(&controller, count, 0, output);
    CHECK(controller.ramped_target_mm_s[0] == 10);
    CHECK(output[0] > 0);

    for (i = 0; i < 300U; ++i) {
        step_counts(&controller, count, 0, output);
        CHECK(output[0] >= 0);
        CHECK(output[0] <= (int16_t)config.maximum_output_permille);
        CHECK(controller.integrator_q10[0] <=
              (int32_t)config.maximum_output_permille *
                  P0_MOTION_GAIN_SCALE);
    }
    CHECK(output[0] == (int16_t)config.maximum_output_permille);

    target[0] = 0;
    CHECK(p0_motion_set_targets(&controller, target));
    for (i = 0; i < 160U; ++i) {
        step_counts(&controller, count, 0, output);
    }
    CHECK(controller.ramped_target_mm_s[0] == 0);
    CHECK(controller.integrator_q10[0] == 0);
    CHECK(output[0] == 0);
}

static void test_reversal_requires_zero_hold(void)
{
    p0_motion_config_t config = synthetic_config();
    p0_motion_controller_t controller;
    int32_t count[4] = {0, 0, 0, 0};
    int16_t target[4] = {30, 0, 0, 0};
    int16_t output[4];
    int16_t previous;
    bool saw_zero = false;
    bool saw_reverse = false;
    size_t i;

    CHECK(p0_motion_init(&controller, &config));
    CHECK(p0_motion_step(&controller, count, output));
    CHECK(p0_motion_set_targets(&controller, target));
    for (i = 0; i < 3U; ++i) {
        step_counts(&controller, count, 0, output);
    }
    CHECK(controller.ramped_target_mm_s[0] == 30);
    CHECK(output[0] > 0);

    target[0] = -30;
    CHECK(p0_motion_set_targets(&controller, target));
    previous = output[0];
    for (i = 0; i < 10U; ++i) {
        step_counts(&controller, count, 0, output);
        CHECK(!((previous > 0) && (output[0] < 0)));
        if (output[0] == 0) {
            saw_zero = true;
        }
        if (output[0] < 0) {
            CHECK(saw_zero);
            saw_reverse = true;
        }
        previous = output[0];
    }
    CHECK(saw_reverse);
}

static void test_reset_and_target_range_are_fail_safe(void)
{
    p0_motion_config_t config = synthetic_config();
    p0_motion_controller_t controller;
    int32_t count[4] = {0, 0, 0, 0};
    int16_t target[4] = {100, 0, 0, 0};
    int16_t output[4];
    int16_t invalid[4] = {INT16_MIN, 0, 0, 0};

    CHECK(p0_motion_init(&controller, &config));
    CHECK(p0_motion_step(&controller, count, output));
    CHECK(p0_motion_set_targets(&controller, target));
    step_counts(&controller, count, 0, output);
    CHECK(output[0] > 0);
    CHECK(!p0_motion_set_targets(&controller, invalid));
    CHECK(controller.requested_target_mm_s[0] == 0);

    p0_motion_reset(&controller);
    CHECK(!controller.encoder_ready);
    CHECK(controller.requested_target_mm_s[0] == 0);
    CHECK(controller.ramped_target_mm_s[0] == 0);
    CHECK(controller.integrator_q10[0] == 0);
    CHECK(controller.output_permille[0] == 0);
    CHECK(controller.active_direction[0] == 0);
    CHECK(controller.pending_direction[0] == 0);
}

static void test_encoder_delta_fault_clears_control_state(void)
{
    p0_motion_config_t config = synthetic_config();
    p0_motion_controller_t controller;
    int32_t count[4] = {0, 0, 0, 0};
    int16_t target[4] = {100, 0, 0, 0};
    int16_t output[4];

    CHECK(p0_motion_init(&controller, &config));
    CHECK(p0_motion_step(&controller, count, output));
    CHECK(p0_motion_set_targets(&controller, target));
    step_counts(&controller, count, 0, output);
    CHECK(output[0] > 0);
    count[0] += 201;
    CHECK(!p0_motion_step(&controller, count, output));
    CHECK(output[0] == 0);
    CHECK(controller.requested_target_mm_s[0] == 0);
    CHECK(controller.integrator_q10[0] == 0);
    CHECK(controller.output_permille[0] == 0);
}

static void test_signed_output_pair_never_drives_both_inputs(void)
{
    uint16_t input_1;
    uint16_t input_2;

    p0_motion_output_pair(600, &input_1, &input_2);
    CHECK(input_1 == 600);
    CHECK(input_2 == 0);
    p0_motion_output_pair(-450, &input_1, &input_2);
    CHECK(input_1 == 0);
    CHECK(input_2 == 450);
    p0_motion_output_pair(0, &input_1, &input_2);
    CHECK(input_1 == 0);
    CHECK(input_2 == 0);
    p0_motion_output_pair(1500, &input_1, &input_2);
    CHECK(input_1 == 1000);
    CHECK(input_2 == 0);
}

static void test_deterministic_command_changes_never_reverse_directly(void)
{
    p0_motion_config_t config = synthetic_config();
    p0_motion_controller_t controller;
    int32_t count[4] = {0, 0, 0, 0};
    int16_t target[4] = {0, 0, 0, 0};
    int16_t output[4];
    int16_t previous[4] = {0, 0, 0, 0};
    uint32_t random_value = UINT32_C(0x13579BDF);
    size_t i;
    size_t channel;

    CHECK(p0_motion_init(&controller, &config));
    CHECK(p0_motion_step(&controller, count, output));
    for (i = 0; i < 50000U; ++i) {
        for (channel = 0; channel < 4U; ++channel) {
            random_value = random_value * UINT32_C(1664525) +
                           UINT32_C(1013904223);
            target[channel] =
                (int16_t)((int32_t)(random_value % UINT32_C(3001)) - 1500);
        }
        CHECK(p0_motion_set_targets(&controller, target));
        step_counts(&controller, count, 0, output);
        for (channel = 0; channel < 4U; ++channel) {
            CHECK(output[channel] >=
                  -(int16_t)config.maximum_output_permille);
            CHECK(output[channel] <=
                  (int16_t)config.maximum_output_permille);
            CHECK(!((previous[channel] > 0) && (output[channel] < 0)));
            CHECK(!((previous[channel] < 0) && (output[channel] > 0)));
            previous[channel] = output[channel];
        }
    }
}

int main(void)
{
    test_invalid_configuration_fails_closed();
    test_speed_estimation_and_counter_wrap();
    test_ramp_limit_and_anti_windup();
    test_reversal_requires_zero_hold();
    test_reset_and_target_range_are_fail_safe();
    test_encoder_delta_fault_clears_control_state();
    test_signed_output_pair_never_drives_both_inputs();
    test_deterministic_command_changes_never_reverse_directly();
    puts("PASS: H60 M1 motion-control host tests");
    return EXIT_SUCCESS;
}
