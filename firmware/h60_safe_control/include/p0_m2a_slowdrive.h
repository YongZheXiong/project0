#ifndef P0_M2A_SLOWDRIVE_H
#define P0_M2A_SLOWDRIVE_H

#include "p0_m2a_calibration.h"

#define P0_SLOW_WAKE_MS UINT32_C(3)
typedef enum {
    P0_SLOW_IDLE, P0_SLOW_WAKING, P0_SLOW_ACTIVE, P0_SLOW_ENDED
} p0_slow_phase_t;
typedef enum {
    P0_SLOW_NONE, P0_SLOW_WAKE, P0_SLOW_RUN, P0_SLOW_OFF, P0_SLOW_REJECT
} p0_slow_action_t;
typedef struct {
    bool armed;
    p0_slow_phase_t phase;
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
