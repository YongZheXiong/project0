#include "p0_motion.h"

#include <limits.h>
#include <stddef.h>

static uint32_t magnitude_i32(int32_t value)
{
    return (value < 0) ? (uint32_t)(-(int64_t)value) : (uint32_t)value;
}

static int8_t sign_i32(int32_t value)
{
    if (value > 0) {
        return INT8_C(1);
    }
    if (value < 0) {
        return INT8_C(-1);
    }
    return INT8_C(0);
}

static int32_t clamp_i64_to_i32(int64_t value)
{
    if (value > INT32_MAX) {
        return INT32_MAX;
    }
    if (value < INT32_MIN) {
        return INT32_MIN;
    }
    return (int32_t)value;
}

static int32_t move_towards(int32_t value, int32_t target, int32_t step)
{
    if (value < target) {
        int64_t next = (int64_t)value + step;
        return (next > target) ? target : (int32_t)next;
    }
    if (value > target) {
        int64_t next = (int64_t)value - step;
        return (next < target) ? target : (int32_t)next;
    }
    return value;
}

static int32_t rate_step(uint16_t rate_mm_s2, uint32_t period_ms)
{
    uint32_t step = ((uint32_t)rate_mm_s2 * period_ms) / UINT32_C(1000);

    if ((step == 0) && (rate_mm_s2 != 0)) {
        step = 1;
    }
    return (int32_t)step;
}

static int32_t encoder_delta(uint8_t bits, int32_t now, int32_t before)
{
    uint64_t modulus = (bits == UINT8_C(16)) ?
                           (UINT64_C(1) << 16) :
                           (UINT64_C(1) << 32);
    uint64_t mask = modulus - UINT64_C(1);
    uint64_t delta = ((uint64_t)(uint32_t)now -
                      (uint64_t)(uint32_t)before) & mask;

    if (delta >= (modulus >> 1)) {
        return (int32_t)((int64_t)delta - (int64_t)modulus);
    }
    return (int32_t)delta;
}

static int32_t estimate_speed(
    const p0_motion_config_t *config,
    uint8_t channel,
    int32_t delta)
{
    int64_t numerator = (int64_t)delta *
                        (int64_t)config->wheel_circumference_mm[channel] *
                        INT64_C(1000) *
                        (int64_t)config->encoder_polarity[channel];
    int64_t denominator =
        (int64_t)config->encoder_counts_per_revolution[channel] *
        (int64_t)config->control_period_ms;

    return clamp_i64_to_i32(numerator / denominator);
}

bool p0_motion_config_is_valid(const p0_motion_config_t *config)
{
    uint8_t i;

    if ((config == NULL) ||
        (config->control_period_ms == 0) ||
        (config->control_period_ms > UINT32_C(1000)) ||
        (config->maximum_target_mm_s == 0) ||
        (config->acceleration_mm_s2 == 0) ||
        (config->deceleration_mm_s2 == 0) ||
        (config->reversal_zero_hold_ms < config->control_period_ms) ||
        (config->maximum_output_permille == 0) ||
        (config->maximum_output_permille >
         (uint16_t)P0_MOTION_OUTPUT_PERMILLE_MAX) ||
        (config->kp_q10 < 0) ||
        (config->kp_q10 > INT32_C(1000000)) ||
        (config->ki_q10_per_s < 0) ||
        (config->ki_q10_per_s > INT32_C(1000000))) {
        return false;
    }

    for (i = 0; i < P0_MOTION_CHANNEL_COUNT; ++i) {
        if ((config->encoder_counts_per_revolution[i] == 0) ||
            (config->encoder_counts_per_revolution[i] >
             UINT32_C(100000000)) ||
            (config->maximum_encoder_delta_counts[i] == 0) ||
            ((config->encoder_counter_bits[i] == UINT8_C(16)) &&
             (config->maximum_encoder_delta_counts[i] > UINT32_C(32767))) ||
            ((config->encoder_counter_bits[i] == UINT8_C(32)) &&
             (config->maximum_encoder_delta_counts[i] >
              UINT32_C(2147483647))) ||
            (config->wheel_circumference_mm[i] == 0) ||
            (config->wheel_circumference_mm[i] > UINT32_C(100000)) ||
            ((config->encoder_counter_bits[i] != UINT8_C(16)) &&
             (config->encoder_counter_bits[i] != UINT8_C(32))) ||
            ((config->encoder_polarity[i] != INT8_C(1)) &&
             (config->encoder_polarity[i] != INT8_C(-1)))) {
            return false;
        }
    }
    return true;
}

void p0_motion_reset(p0_motion_controller_t *controller)
{
    uint8_t i;

    controller->encoder_ready = false;
    for (i = 0; i < P0_MOTION_CHANNEL_COUNT; ++i) {
        controller->previous_encoder_count[i] = 0;
        controller->requested_target_mm_s[i] = 0;
        controller->ramped_target_mm_s[i] = 0;
        controller->measured_speed_mm_s[i] = 0;
        controller->integrator_q10[i] = 0;
        controller->output_permille[i] = 0;
        controller->active_direction[i] = 0;
        controller->pending_direction[i] = 0;
        controller->zero_hold_elapsed_ms[i] = 0;
    }
}

bool p0_motion_init(
    p0_motion_controller_t *controller,
    const p0_motion_config_t *config)
{
    uint8_t i;

    if ((controller == NULL) || (config == NULL)) {
        return false;
    }
    controller->config = *config;
    controller->config_valid = p0_motion_config_is_valid(config);
    p0_motion_reset(controller);

    if (!controller->config_valid) {
        for (i = 0; i < P0_MOTION_CHANNEL_COUNT; ++i) {
            controller->config.encoder_counts_per_revolution[i] = 0;
        }
    }
    return controller->config_valid;
}

bool p0_motion_set_targets(
    p0_motion_controller_t *controller,
    const int16_t target_mm_s[4])
{
    uint8_t i;

    if (controller == NULL) {
        return false;
    }
    if ((target_mm_s == NULL) || !controller->config_valid) {
        p0_motion_reset(controller);
        return false;
    }
    for (i = 0; i < P0_MOTION_CHANNEL_COUNT; ++i) {
        int32_t target = target_mm_s[i];
        if (magnitude_i32(target) > controller->config.maximum_target_mm_s) {
            p0_motion_reset(controller);
            return false;
        }
    }
    for (i = 0; i < P0_MOTION_CHANNEL_COUNT; ++i) {
        controller->requested_target_mm_s[i] = target_mm_s[i];
    }
    return true;
}

static int16_t calculate_pi_output(
    p0_motion_controller_t *controller,
    uint8_t channel)
{
    const p0_motion_config_t *config = &controller->config;
    int64_t error = (int64_t)controller->ramped_target_mm_s[channel] -
                    controller->measured_speed_mm_s[channel];
    int64_t output_limit_q10 =
        (int64_t)config->maximum_output_permille * P0_MOTION_GAIN_SCALE;
    int64_t p_term_q10 = (int64_t)config->kp_q10 * error;
    int64_t integral_delta =
        ((int64_t)config->ki_q10_per_s * error *
         (int64_t)config->control_period_ms) /
        INT64_C(1000);
    int64_t candidate_integral =
        (int64_t)controller->integrator_q10[channel] + integral_delta;
    int64_t candidate_output;
    int64_t output;

    if (candidate_integral > output_limit_q10) {
        candidate_integral = output_limit_q10;
    } else if (candidate_integral < -output_limit_q10) {
        candidate_integral = -output_limit_q10;
    }

    candidate_output = p_term_q10 + candidate_integral;
    if (!((candidate_output > output_limit_q10 && error > 0) ||
          (candidate_output < -output_limit_q10 && error < 0))) {
        controller->integrator_q10[channel] = (int32_t)candidate_integral;
    }

    output = p_term_q10 + controller->integrator_q10[channel];
    if (output > output_limit_q10) {
        output = output_limit_q10;
    } else if (output < -output_limit_q10) {
        output = -output_limit_q10;
    }
    output /= P0_MOTION_GAIN_SCALE;

    if ((controller->active_direction[channel] > 0) && (output < 0)) {
        output = 0;
    } else if ((controller->active_direction[channel] < 0) && (output > 0)) {
        output = 0;
    }
    return (int16_t)output;
}

static void update_channel(p0_motion_controller_t *controller, uint8_t channel)
{
    const p0_motion_config_t *config = &controller->config;
    int32_t requested = controller->requested_target_mm_s[channel];
    int8_t requested_direction = sign_i32(requested);
    int8_t active_direction = controller->active_direction[channel];
    int32_t effective_target;
    int32_t current = controller->ramped_target_mm_s[channel];
    int32_t step;

    if ((active_direction == 0) && (requested_direction != 0)) {
        controller->active_direction[channel] = requested_direction;
        active_direction = requested_direction;
    } else if ((active_direction != 0) &&
               (requested_direction != 0) &&
               (requested_direction != active_direction)) {
        controller->pending_direction[channel] = requested_direction;
    } else if ((requested_direction == active_direction) &&
               (controller->pending_direction[channel] != 0)) {
        controller->pending_direction[channel] = 0;
        controller->zero_hold_elapsed_ms[channel] = 0;
    }

    effective_target =
        ((requested_direction == controller->active_direction[channel]) &&
         (controller->pending_direction[channel] == 0)) ? requested : 0;

    if ((effective_target == 0) ||
        (sign_i32(current) != sign_i32(effective_target)) ||
        (magnitude_i32(effective_target) < magnitude_i32(current))) {
        step = rate_step(config->deceleration_mm_s2,
                         config->control_period_ms);
    } else {
        step = rate_step(config->acceleration_mm_s2,
                         config->control_period_ms);
    }
    controller->ramped_target_mm_s[channel] =
        move_towards(current, effective_target, step);

    if (controller->ramped_target_mm_s[channel] == 0) {
        controller->output_permille[channel] = 0;
        controller->integrator_q10[channel] = 0;

        if ((controller->active_direction[channel] != 0) &&
            ((requested_direction == 0) ||
             (controller->pending_direction[channel] != 0))) {
            if (magnitude_i32(controller->measured_speed_mm_s[channel]) <=
                config->zero_speed_threshold_mm_s) {
                uint32_t elapsed = controller->zero_hold_elapsed_ms[channel];
                if (elapsed <= UINT32_MAX - config->control_period_ms) {
                    elapsed += config->control_period_ms;
                }
                controller->zero_hold_elapsed_ms[channel] = elapsed;
            } else {
                controller->zero_hold_elapsed_ms[channel] = 0;
            }

            if (controller->zero_hold_elapsed_ms[channel] >=
                config->reversal_zero_hold_ms) {
                if ((controller->pending_direction[channel] != 0) &&
                    (requested_direction ==
                     controller->pending_direction[channel])) {
                    controller->active_direction[channel] =
                        controller->pending_direction[channel];
                    controller->pending_direction[channel] = 0;
                } else if (requested_direction == 0) {
                    controller->active_direction[channel] = 0;
                    controller->pending_direction[channel] = 0;
                }
                controller->zero_hold_elapsed_ms[channel] = 0;
            }
        }
        return;
    }

    controller->zero_hold_elapsed_ms[channel] = 0;
    controller->output_permille[channel] =
        calculate_pi_output(controller, channel);
}

bool p0_motion_step(
    p0_motion_controller_t *controller,
    const int32_t encoder_count[4],
    int16_t output_permille[4])
{
    uint8_t i;
    int32_t delta[4];

    if (controller == NULL) {
        return false;
    }
    if ((encoder_count == NULL) || (output_permille == NULL) ||
        !controller->config_valid) {
        p0_motion_reset(controller);
        return false;
    }

    if (!controller->encoder_ready) {
        for (i = 0; i < P0_MOTION_CHANNEL_COUNT; ++i) {
            controller->previous_encoder_count[i] = encoder_count[i];
            controller->output_permille[i] = 0;
            output_permille[i] = 0;
        }
        controller->encoder_ready = true;
        return true;
    }

    for (i = 0; i < P0_MOTION_CHANNEL_COUNT; ++i) {
        delta[i] = encoder_delta(
            controller->config.encoder_counter_bits[i],
            encoder_count[i],
            controller->previous_encoder_count[i]);
        if (magnitude_i32(delta[i]) >
            controller->config.maximum_encoder_delta_counts[i]) {
            uint8_t j;
            p0_motion_reset(controller);
            for (j = 0; j < P0_MOTION_CHANNEL_COUNT; ++j) {
                output_permille[j] = 0;
            }
            return false;
        }
    }

    for (i = 0; i < P0_MOTION_CHANNEL_COUNT; ++i) {
        controller->previous_encoder_count[i] = encoder_count[i];
        controller->measured_speed_mm_s[i] =
            estimate_speed(&controller->config, i, delta[i]);
        update_channel(controller, i);
        output_permille[i] = controller->output_permille[i];
    }
    return true;
}

void p0_motion_output_pair(
    int16_t signed_output_permille,
    uint16_t *input_1_permille,
    uint16_t *input_2_permille)
{
    int32_t value = signed_output_permille;

    if (value > P0_MOTION_OUTPUT_PERMILLE_MAX) {
        value = P0_MOTION_OUTPUT_PERMILLE_MAX;
    } else if (value < -P0_MOTION_OUTPUT_PERMILLE_MAX) {
        value = -P0_MOTION_OUTPUT_PERMILLE_MAX;
    }

    if (value > 0) {
        *input_1_permille = (uint16_t)value;
        *input_2_permille = 0;
    } else if (value < 0) {
        *input_1_permille = 0;
        *input_2_permille = (uint16_t)(-value);
    } else {
        *input_1_permille = 0;
        *input_2_permille = 0;
    }
}
