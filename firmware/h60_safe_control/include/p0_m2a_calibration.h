#ifndef P0_M2A_CALIBRATION_H
#define P0_M2A_CALIBRATION_H

#include <stdbool.h>
#include <stdint.h>

#define P0_M2A_CHANNEL_COUNT UINT8_C(4)
#define P0_M2A_HOLD_LEASE_MS UINT32_C(75)
#define P0_M2A_MAX_ARMED_MS UINT32_C(1000)
#define P0_M2A_MIN_DUTY_PERMILLE UINT16_C(50)
#define P0_M2A_MAX_DUTY_PERMILLE UINT16_C(120)

typedef enum {
    P0_M2A_SERVICE_OK = 0,
    P0_M2A_SERVICE_HOLD_EXPIRED = 1,
    P0_M2A_SERVICE_SESSION_EXPIRED = 2
} p0_m2a_service_result_t;

typedef struct {
    bool armed;
    bool output_active;
    uint32_t armed_at_ms;
    uint32_t last_hold_ms;
    uint8_t channel;
    int8_t direction;
    uint16_t duty_permille;
} p0_m2a_calibration_t;

void p0_m2a_calibration_reset(p0_m2a_calibration_t *calibration);
bool p0_m2a_calibration_arm(
    p0_m2a_calibration_t *calibration,
    uint32_t now_ms);
bool p0_m2a_calibration_hold(
    p0_m2a_calibration_t *calibration,
    uint8_t channel,
    int8_t direction,
    uint16_t duty_permille,
    uint32_t now_ms,
    int16_t output_permille[4]);
p0_m2a_service_result_t p0_m2a_calibration_service(
    p0_m2a_calibration_t *calibration,
    uint32_t now_ms,
    int16_t output_permille[4]);

#endif
