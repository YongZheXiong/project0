#include "p0_motion.h"
#include "p0_motion_scheduler.h"

#include <assert.h>
#include <limits.h>
#include <stdio.h>

static void test_exact_period_only(void)
{
    p0_motion_scheduler_t scheduler = {0};

    assert(p0_motion_scheduler_poll(&scheduler, UINT32_C(100)) ==
           P0_MOTION_SCHEDULE_PRIME);
    assert(p0_motion_scheduler_poll(&scheduler, UINT32_C(109)) ==
           P0_MOTION_SCHEDULE_WAIT);
    assert(p0_motion_scheduler_poll(&scheduler, UINT32_C(110)) ==
           P0_MOTION_SCHEDULE_STEP);
    assert(p0_motion_scheduler_poll(&scheduler, UINT32_C(119)) ==
           P0_MOTION_SCHEDULE_WAIT);
    assert(p0_motion_scheduler_poll(&scheduler, UINT32_C(120)) ==
           P0_MOTION_SCHEDULE_STEP);
}

static void test_lateness_latches_until_reset(void)
{
    p0_motion_scheduler_t scheduler = {0};

    assert(p0_motion_scheduler_poll(&scheduler, UINT32_C(50)) ==
           P0_MOTION_SCHEDULE_PRIME);
    assert(p0_motion_scheduler_poll(
               &scheduler,
               UINT32_C(50) + P0_MOTION_CONTROL_PERIOD_MS + UINT32_C(1)) ==
           P0_MOTION_SCHEDULE_LATE);
    assert(scheduler.late_latched);
    assert(p0_motion_scheduler_poll(&scheduler, UINT32_C(61)) ==
           P0_MOTION_SCHEDULE_LATE);

    p0_motion_scheduler_reset(&scheduler);
    assert(!scheduler.late_latched);
    assert(p0_motion_scheduler_poll(&scheduler, UINT32_C(61)) ==
           P0_MOTION_SCHEDULE_PRIME);
}

static void test_millisecond_counter_wrap(void)
{
    p0_motion_scheduler_t scheduler = {0};
    uint32_t start = UINT32_MAX - UINT32_C(4);

    assert(p0_motion_scheduler_poll(&scheduler, start) ==
           P0_MOTION_SCHEDULE_PRIME);
    assert(p0_motion_scheduler_poll(&scheduler, UINT32_C(4)) ==
           P0_MOTION_SCHEDULE_WAIT);
    assert(p0_motion_scheduler_poll(&scheduler, UINT32_C(5)) ==
           P0_MOTION_SCHEDULE_STEP);
}

int main(void)
{
    test_exact_period_only();
    test_lateness_latches_until_reset();
    test_millisecond_counter_wrap();
    assert(p0_motion_scheduler_poll(NULL, 0) == P0_MOTION_SCHEDULE_LATE);
    puts("PASS: fixed-10-ms motion scheduler fail-safe tests");
    return 0;
}
