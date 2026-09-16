#ifndef P0_MOTION_SCHEDULER_H
#define P0_MOTION_SCHEDULER_H

#include <stdbool.h>
#include <stdint.h>

typedef enum {
    P0_MOTION_SCHEDULE_PRIME = 0,
    P0_MOTION_SCHEDULE_WAIT = 1,
    P0_MOTION_SCHEDULE_STEP = 2,
    P0_MOTION_SCHEDULE_LATE = 3
} p0_motion_schedule_result_t;

typedef struct {
    bool active;
    bool late_latched;
    uint32_t last_step_ms;
} p0_motion_scheduler_t;

void p0_motion_scheduler_reset(p0_motion_scheduler_t *scheduler);
p0_motion_schedule_result_t p0_motion_scheduler_poll(
    p0_motion_scheduler_t *scheduler,
    uint32_t now_ms);

#endif
