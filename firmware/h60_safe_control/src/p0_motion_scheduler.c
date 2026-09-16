#include "p0_motion_scheduler.h"

#include "p0_motion.h"

#include <stddef.h>

void p0_motion_scheduler_reset(p0_motion_scheduler_t *scheduler)
{
    if (scheduler == NULL) {
        return;
    }
    scheduler->active = false;
    scheduler->late_latched = false;
    scheduler->last_step_ms = 0;
}

p0_motion_schedule_result_t p0_motion_scheduler_poll(
    p0_motion_scheduler_t *scheduler,
    uint32_t now_ms)
{
    uint32_t elapsed_ms;

    if (scheduler == NULL) {
        return P0_MOTION_SCHEDULE_LATE;
    }
    if (scheduler->late_latched) {
        return P0_MOTION_SCHEDULE_LATE;
    }
    if (!scheduler->active) {
        scheduler->active = true;
        scheduler->last_step_ms = now_ms;
        return P0_MOTION_SCHEDULE_PRIME;
    }

    elapsed_ms = (uint32_t)(now_ms - scheduler->last_step_ms);
    if (elapsed_ms < P0_MOTION_CONTROL_PERIOD_MS) {
        return P0_MOTION_SCHEDULE_WAIT;
    }
    if (elapsed_ms > P0_MOTION_CONTROL_PERIOD_MS) {
        scheduler->active = false;
        scheduler->late_latched = true;
        return P0_MOTION_SCHEDULE_LATE;
    }

    scheduler->last_step_ms = now_ms;
    return P0_MOTION_SCHEDULE_STEP;
}
