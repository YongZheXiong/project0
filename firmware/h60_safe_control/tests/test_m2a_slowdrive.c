#include "p0_m2a_slowdrive.h"
#include <assert.h>
#include <stdio.h>

static void lifecycle(uint32_t t)
{
    p0_m2a_slowdrive_t s;
    p0_slow_arm(&s, t, 7);
    assert(p0_slow_service(&s, t + 1, 7) == P0_SLOW_NONE);
    assert(p0_slow_hold(&s, 1, 0, 0, t + 1, 7) == P0_SLOW_NONE);
    assert(p0_slow_hold(&s, 1, 1, 50, t + 2, 7) == P0_SLOW_WAKE);
    s.wake_at_ms = t + 3; /* 引脚接管后的时间 */
    assert(p0_slow_hold(&s, 1, 1, 50, t + 4, 7) == P0_SLOW_NONE);
    assert(s.wake_at_ms == t + 3 && s.armed_at_ms == t);
    assert(p0_slow_service(&s, t + 5, 7) == P0_SLOW_NONE);
    assert(p0_slow_service(&s, t + 6, 7) == P0_SLOW_RUN);
    assert(p0_slow_service(&s, t + 7, 7) == P0_SLOW_NONE);
    assert(p0_slow_hold(&s, 1, 0, 0, t + 8, 7) == P0_SLOW_OFF);
    assert(p0_slow_service(&s, t + 9, 8) == P0_SLOW_NONE);
    assert(p0_slow_hold(&s, 1, 1, 50, t + 10, 8) == P0_SLOW_REJECT);
    assert(!s.armed);
}

int main(void)
{
    p0_m2a_slowdrive_t s;
    lifecycle(0); lifecycle(UINT32_MAX - 5);
    unsigned cases = 0;
    for (unsigned ch = 0; ch < 5; ++ch)
        for (int dir = -2; dir <= 2; ++dir)
            for (unsigned duty = 0; duty <= 121; ++duty) {
                p0_slow_arm(&s, 0, 7);
                p0_slow_action_t a = p0_slow_hold(&s, ch, dir, duty, 1, 7);
                bool valid = ch == 1 && ((dir == 0 && duty == 0) ||
                                        (dir == 1 && duty == 50));
                assert((a != P0_SLOW_REJECT) == valid);
                ++cases;
            }
    for (unsigned phase = 0; phase < 3; ++phase) {
        p0_slow_arm(&s, 0, 7);
        if (phase > 0) assert(p0_slow_hold(&s, 1, 1, 50, 1, 7) == P0_SLOW_WAKE);
        if (phase > 1) assert(p0_slow_service(&s, 4, 7) == P0_SLOW_RUN);
        assert(p0_slow_service(&s, 5, 8) == P0_SLOW_REJECT);
        assert(p0_slow_hold(&s, 1, 1, 50, 6, 8) == P0_SLOW_REJECT);
    }
    p0_slow_arm(&s, 0, 7);
    assert(p0_slow_hold(&s, 1, 1, 50, 900, 7) == P0_SLOW_WAKE);
    assert(p0_slow_service(&s, 975, 7) == P0_SLOW_RUN); /* 原75ms含边界 */
    assert(p0_slow_hold(&s, 1, 1, 50, 976, 7) == P0_SLOW_REJECT);
    p0_slow_arm(&s, 0, 7);
    assert(p0_slow_hold(&s, 1, 1, 50, 999, 7) == P0_SLOW_WAKE);
    assert(p0_slow_service(&s, 1000, 7) == P0_SLOW_NONE);
    assert(p0_slow_service(&s, 1001, 7) == P0_SLOW_REJECT);
    /* 多次有效续租不延长绝对会话，也不会重复RUN动作。 */
    p0_slow_arm(&s, 0, 7);
    assert(p0_slow_hold(&s, 1, 1, 50, 1, 7) == P0_SLOW_WAKE);
    assert(p0_slow_service(&s, 4, 7) == P0_SLOW_RUN);
    for (uint32_t t = 25; t <= 1000; t += 25)
        assert(p0_slow_hold(&s, 1, 1, 50, t, 7) == P0_SLOW_NONE);
    assert(p0_slow_service(&s, 1001, 7) == P0_SLOW_REJECT);
    printf("PASS: slowdrive %u admission cases, wake/cancel/expiry/wrap\n", cases);
}
