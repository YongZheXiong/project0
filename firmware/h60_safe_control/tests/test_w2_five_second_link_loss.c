#include "p0_m2a_slowdrive.h"

#include <assert.h>
#include <stdio.h>

static p0_m2a_slowdrive_t start(uint32_t at_ms)
{
    p0_m2a_slowdrive_t state;
    p0_slow_arm(&state, at_ms, UINT32_C(7));
    assert(p0_slow_hold(&state, P0_W2_PROFILE_CHANNEL,
        P0_W2_PROFILE_FORWARD_DIRECTION, P0_W2_TARGET_DUTY_PERMILLE,
        at_ms, UINT32_C(7)) == P0_SLOW_WAKE);
    assert(p0_slow_service(&state, at_ms + UINT32_C(3), UINT32_C(7)) ==
        P0_SLOW_RUN);
    return state;
}

int main(void)
{
    p0_m2a_slowdrive_t state;
    uint32_t at_ms;

    assert(P0_W2_FIVE_SECOND_LINK_LOSS_BUILD == 1);
    assert(P0_SLOW_MAX_ARMED_MS == UINT32_C(5000));
    assert(P0_M2A_HOLD_LEASE_MS == UINT32_C(75));
    assert(P0_W2_TARGET_DUTY_PERMILLE == UINT16_C(80));

    /* 75 ms 失联租约保持原值；迟到 HOLD 不能复活输出。 */
    state = start(UINT32_C(100));
    assert(p0_slow_service(&state, UINT32_C(175), UINT32_C(7)) == P0_SLOW_NONE);
    assert(p0_slow_service(&state, UINT32_C(176), UINT32_C(7)) == P0_SLOW_REJECT);
    assert(p0_slow_hold(&state, P0_W2_PROFILE_CHANNEL,
        P0_W2_PROFILE_FORWARD_DIRECTION, P0_W2_TARGET_DUTY_PERMILLE,
        UINT32_C(177), UINT32_C(7)) == P0_SLOW_REJECT);

    /* 正常续租不能越过 ARM 绝对五秒门。 */
    state = start(UINT32_C(100));
    for (at_ms = UINT32_C(150); at_ms <= UINT32_C(5100);
         at_ms += UINT32_C(50)) {
        assert(p0_slow_hold(&state, P0_W2_PROFILE_CHANNEL,
            P0_W2_PROFILE_FORWARD_DIRECTION, P0_W2_TARGET_DUTY_PERMILLE,
            at_ms, UINT32_C(7)) == P0_SLOW_NONE);
    }
    assert(p0_slow_service(&state, UINT32_C(5100), UINT32_C(7)) == P0_SLOW_NONE);
    assert(p0_slow_service(&state, UINT32_C(5101), UINT32_C(7)) == P0_SLOW_REJECT);
    assert(!state.armed);

    /* 主动 STOP 或换向仍终结本次许可，必须显式重新 ARM。 */
    state = start(UINT32_C(100));
    assert(p0_slow_hold(&state, P0_W2_PROFILE_CHANNEL, 0, 0,
        UINT32_C(130), UINT32_C(7)) == P0_SLOW_OFF);
    assert(p0_slow_hold(&state, P0_W2_PROFILE_CHANNEL,
        P0_W2_PROFILE_FORWARD_DIRECTION, P0_W2_TARGET_DUTY_PERMILLE,
        UINT32_C(131), UINT32_C(7)) == P0_SLOW_REJECT);
    state = start(UINT32_C(100));
    assert(p0_slow_hold(&state, P0_W2_PROFILE_CHANNEL,
        P0_W2_PROFILE_REVERSE_DIRECTION, P0_W2_TARGET_DUTY_PERMILLE,
        UINT32_C(130), UINT32_C(7)) == P0_SLOW_REJECT);

    puts("PASS: W2 link-loss candidate keeps 75 ms lease and 5 s absolute ARM limit");
    return 0;
}
