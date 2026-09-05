#ifndef P0_MOTION_H
#define P0_MOTION_H

#include <stdbool.h>
#include <stdint.h>

#define P0_MOTION_CHANNEL_COUNT UINT8_C(4)
#define P0_MOTION_CONTROL_PERIOD_MS UINT32_C(10)
#define P0_MOTION_OUTPUT_PERMILLE_MAX INT16_C(1000)
#define P0_MOTION_GAIN_SCALE INT32_C(1024)

typedef struct {
    uint32_t control_period_ms;
    uint32_t encoder_counts_per_revolution[4];
    uint32_t maximum_encoder_delta_counts[4];
    uint32_t wheel_circumference_mm[4];
    uint8_t encoder_counter_bits[4];
    int8_t encoder_polarity[4];
    uint16_t maximum_target_mm_s;
    uint16_t acceleration_mm_s2;
    uint16_t deceleration_mm_s2;
    uint16_t reversal_zero_hold_ms;
    uint16_t zero_speed_threshold_mm_s;
    uint16_t maximum_output_permille;
    int32_t kp_q10;
    int32_t ki_q10_per_s;
} p0_motion_config_t;

typedef struct {
    p0_motion_config_t config;
    bool config_valid;
    bool encoder_ready;
    int32_t previous_encoder_count[4];
    int16_t requested_target_mm_s[4];
    int32_t ramped_target_mm_s[4];
    int32_t measured_speed_mm_s[4];
    int32_t integrator_q10[4];
    int16_t output_permille[4];
    int8_t active_direction[4];
    int8_t pending_direction[4];
    uint32_t zero_hold_elapsed_ms[4];
} p0_motion_controller_t;

bool p0_motion_config_is_valid(const p0_motion_config_t *config);
bool p0_motion_init(
    p0_motion_controller_t *controller,
    const p0_motion_config_t *config);
void p0_motion_reset(p0_motion_controller_t *controller);
bool p0_motion_set_targets(
    p0_motion_controller_t *controller,
    const int16_t target_mm_s[4]);
bool p0_motion_step(
    p0_motion_controller_t *controller,
    const int32_t encoder_count[4],
    int16_t output_permille[4]);
void p0_motion_output_pair(
    int16_t signed_output_permille,
    uint16_t *input_1_permille,
    uint16_t *input_2_permille);

#endif
