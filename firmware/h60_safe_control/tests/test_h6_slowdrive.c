#include "p0_m2a_slowdrive.h"
#include <assert.h>
#include <stdio.h>

static void lifecycle(uint8_t channel, int8_t direction, uint16_t duty,
    uint32_t start)
{
    p0_m2a_slowdrive_t s;
    p0_slow_arm(&s, start, 9);
    assert(p0_slow_hold(&s, channel, direction, duty, start + 1, 9) ==
           P0_SLOW_WAKE);
    assert(s.channel == channel && s.direction == direction &&
           s.duty_permille == duty);
    s.wake_at_ms = start + 2;
    assert(p0_slow_service(&s, start + 4, 9) == P0_SLOW_NONE);
    assert(p0_slow_service(&s, start + 5, 9) == P0_SLOW_RUN);
    assert(p0_slow_hold(&s, channel, direction, duty, start + 6, 9) ==
           P0_SLOW_NONE);
    assert(p0_slow_hold(&s, channel, 0, 0, start + 7, 9) == P0_SLOW_OFF);
    assert(p0_slow_hold(&s, channel, direction, duty, start + 8, 9) ==
           P0_SLOW_REJECT);
}

int main(void)
{
    p0_m2a_slowdrive_t s;
    unsigned cases = 0;

    assert(P0_H6_CHARACTERIZATION_BUILD == 1);
    for (uint8_t channel = 0; channel < 4; ++channel) {
        lifecycle(channel, INT8_C(1), UINT16_C(50), 0);
        lifecycle(channel, INT8_C(-1), UINT16_C(120), UINT32_MAX - 5);
    }
    for (unsigned channel = 0; channel < 5; ++channel) {
        for (int direction = -2; direction <= 2; ++direction) {
            for (unsigned duty = 0; duty <= 121; ++duty) {
                bool valid = channel < 4 &&
                    ((direction == 0 && duty == 0) ||
                     ((direction == -1 || direction == 1) &&
                      duty >= 50 && duty <= 120));
                p0_slow_arm(&s, 0, 9);
                p0_slow_action_t action = p0_slow_hold(&s, (uint8_t)channel,
                    (int8_t)direction, (uint16_t)duty, 1, 9);
                assert((action != P0_SLOW_REJECT) == valid);
                ++cases;
            }
        }
    }

    /* 首个非零命令锁定通道、方向和档位，同一ARM内不得改选。 */
    for (uint8_t channel = 0; channel < 4; ++channel) {
        p0_slow_arm(&s, 0, 9);
        assert(p0_slow_hold(&s, channel, -1, 80, 1, 9) == P0_SLOW_WAKE);
        assert(p0_slow_hold(&s, (uint8_t)((channel + 1) % 4), -1, 80, 2, 9) ==
               P0_SLOW_REJECT);
        p0_slow_arm(&s, 0, 9);
        assert(p0_slow_hold(&s, channel, 1, 80, 1, 9) == P0_SLOW_WAKE);
        assert(p0_slow_hold(&s, channel, -1, 80, 2, 9) == P0_SLOW_REJECT);
        p0_slow_arm(&s, 0, 9);
        assert(p0_slow_hold(&s, channel, 1, 80, 1, 9) == P0_SLOW_WAKE);
        assert(p0_slow_hold(&s, channel, 1, 81, 2, 9) == P0_SLOW_REJECT);
    }

    p0_slow_arm(&s, 0, 9);
    assert(p0_slow_hold(&s, 3, 1, 50, 900, 9) == P0_SLOW_WAKE);
    assert(p0_slow_service(&s, 975, 9) == P0_SLOW_RUN);
    assert(p0_slow_hold(&s, 3, 1, 50, 976, 9) == P0_SLOW_REJECT);
    p0_slow_arm(&s, 0, 9);
    assert(p0_slow_hold(&s, 0, -1, 120, 999, 9) == P0_SLOW_WAKE);
    assert(p0_slow_service(&s, 1000, 9) == P0_SLOW_NONE);
    assert(p0_slow_service(&s, 1001, 9) == P0_SLOW_REJECT);

    printf("PASS: H6 slowdrive %u admission cases and four-channel latch/expiry\n",
           cases);
}
