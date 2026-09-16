#ifndef P0_M2A_SLOWDRIVE_H
#define P0_M2A_SLOWDRIVE_H

#include "p0_build_config.h"
#include "p0_m2a_calibration.h"

#define P0_SLOW_WAKE_MS UINT32_C(3)
#define P0_W2_PROFILE_CHANNEL UINT8_C(0xF0)
#define P0_W2_PROFILE_FORWARD_DIRECTION INT8_C(1)
#define P0_W2_PROFILE_REVERSE_DIRECTION INT8_C(-1)
#define P0_W2_TARGET_DUTY_PERMILLE UINT16_C(80)
#if P0_W2_FIVE_SECOND_LINK_LOSS_BUILD != 0
#define P0_SLOW_MAX_ARMED_MS UINT32_C(5000)
#elif P0_H6_EXTENDED_WINDOW_BUILD != 0
#define P0_SLOW_MAX_ARMED_MS UINT32_C(2500)
#define P0_H6_R2_RAMP_UP_MS UINT32_C(300)
#define P0_H6_R2_HOLD_MS UINT32_C(1200)
#define P0_H6_R2_RAMP_DOWN_MS UINT32_C(300)
#define P0_H6_R2_NONZERO_WINDOW_MS \
    (P0_H6_R2_RAMP_UP_MS + P0_H6_R2_HOLD_MS + P0_H6_R2_RAMP_DOWN_MS)
#define P0_H6_R2_CHANNEL UINT8_C(2)
#define P0_H6_R2_DIRECTION INT8_C(1)
#define P0_H6_R2_TARGET_DUTY_PERMILLE UINT16_C(80)
#else
#define P0_SLOW_MAX_ARMED_MS P0_M2A_MAX_ARMED_MS
#endif
typedef enum {
    P0_SLOW_IDLE, P0_SLOW_WAKING, P0_SLOW_ACTIVE, P0_SLOW_ENDED
} p0_slow_phase_t;
typedef enum {
    P0_SLOW_NONE, P0_SLOW_WAKE, P0_SLOW_RUN, P0_SLOW_OFF, P0_SLOW_REJECT
} p0_slow_action_t;
typedef struct {
    bool armed;
    p0_slow_phase_t phase;
#if P0_H6_CHARACTERIZATION_BUILD != 0
    uint8_t channel;
    int8_t direction;
    uint16_t duty_permille;
#if P0_H6_EXTENDED_WINDOW_BUILD != 0
    uint16_t target_duty_permille;
    uint32_t envelope_started_at_ms;
#endif
#endif
    uint32_t generation;
    uint32_t armed_at_ms;
    uint32_t last_hold_ms;
    uint32_t wake_at_ms;
} p0_m2a_slowdrive_t;

void p0_slow_reset(p0_m2a_slowdrive_t *s);
void p0_slow_arm(p0_m2a_slowdrive_t *s, uint32_t now, uint32_t generation);
bool p0_slow_fresh(const p0_m2a_slowdrive_t *s, uint32_t now, uint32_t generation);
p0_slow_action_t p0_slow_hold(p0_m2a_slowdrive_t *s, uint8_t channel,
    int8_t direction, uint16_t duty, uint32_t now, uint32_t generation);
p0_slow_action_t p0_slow_service(p0_m2a_slowdrive_t *s, uint32_t now,
    uint32_t generation);

#endif
