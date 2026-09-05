#include "p0_m2a_calibration.h"

#include <stddef.h>

static void clear_output(int16_t output_permille[4])
{
    uint8_t i;

    if (output_permille == NULL) {
        return;
    }
    for (i = 0; i < P0_M2A_CHANNEL_COUNT; ++i) {
        output_permille[i] = 0;
    }
}

void p0_m2a_calibration_reset(p0_m2a_calibration_t *calibration)
{
    if (calibration == NULL) {
        return;
    }
    calibration->armed = false;
    calibration->output_active = false;
    calibration->armed_at_ms = 0;
    calibration->last_hold_ms = 0;
    calibration->channel = 0;
    calibration->direction = 0;
    calibration->duty_permille = 0;
}

bool p0_m2a_calibration_arm(
    p0_m2a_calibration_t *calibration,
    uint32_t now_ms)
{
    if (calibration == NULL) {
        return false;
    }
    p0_m2a_calibration_reset(calibration);
    calibration->armed = true;
    calibration->armed_at_ms = now_ms;
    calibration->last_hold_ms = now_ms;
    return true;
}

bool p0_m2a_calibration_hold(
    p0_m2a_calibration_t *calibration,
    uint8_t channel,
    int8_t direction,
    uint16_t duty_permille,
    uint32_t now_ms,
    int16_t output_permille[4])
{
    clear_output(output_permille);
    if ((calibration == NULL) || (output_permille == NULL) ||
        !calibration->armed || (channel >= P0_M2A_CHANNEL_COUNT) ||
        ((direction != INT8_C(-1)) && (direction != INT8_C(0)) &&
         (direction != INT8_C(1))) ||
        ((direction == 0) && (duty_permille != 0)) ||
        ((direction != 0) &&
         ((duty_permille < P0_M2A_MIN_DUTY_PERMILLE) ||
          (duty_permille > P0_M2A_MAX_DUTY_PERMILLE)))) {
        if (calibration != NULL) {
            p0_m2a_calibration_reset(calibration);
        }
        return false;
    }

    calibration->last_hold_ms = now_ms;
    calibration->channel = channel;
    calibration->direction = direction;
    calibration->duty_permille = duty_permille;
    calibration->output_active = direction != 0;
    if (direction != 0) {
        output_permille[channel] =
            (int16_t)((int32_t)direction * (int32_t)duty_permille);
    }
    return true;
}

p0_m2a_service_result_t p0_m2a_calibration_service(
    p0_m2a_calibration_t *calibration,
    uint32_t now_ms,
    int16_t output_permille[4])
{
    clear_output(output_permille);
    if ((calibration == NULL) || !calibration->armed) {
        return P0_M2A_SERVICE_OK;
    }
    if ((uint32_t)(now_ms - calibration->armed_at_ms) >
        P0_M2A_MAX_ARMED_MS) {
        p0_m2a_calibration_reset(calibration);
        return P0_M2A_SERVICE_SESSION_EXPIRED;
    }
    if (calibration->output_active &&
        ((uint32_t)(now_ms - calibration->last_hold_ms) >
         P0_M2A_HOLD_LEASE_MS)) {
        p0_m2a_calibration_reset(calibration);
        return P0_M2A_SERVICE_HOLD_EXPIRED;
    }
    return P0_M2A_SERVICE_OK;
}
