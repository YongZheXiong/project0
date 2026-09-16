#include "p0_m2a_slowdrive.h"

#include <assert.h>
#include <stdio.h>

static p0_m2a_slowdrive_t armed_state(void)
{
    p0_m2a_slowdrive_t state;
    p0_slow_arm(&state, UINT32_C(100), UINT32_C(7));
    return state;
}

int main(void)
{
    p0_m2a_slowdrive_t state;

    assert(P0_W2_FOUR_WHEEL_PROFILE_BUILD == 1);
    assert(P0_W2_PROFILE_CHANNEL == UINT8_C(0xF0));
    assert(P0_W2_TARGET_DUTY_PERMILLE == UINT16_C(80));
    assert(P0_M2A_HOLD_LEASE_MS == UINT32_C(75));
    assert(P0_SLOW_MAX_ARMED_MS == UINT32_C(1000));

    state = armed_state();
    assert(p0_slow_hold(&state, P0_W2_PROFILE_CHANNEL,
        P0_W2_PROFILE_FORWARD_DIRECTION, P0_W2_TARGET_DUTY_PERMILLE,
        UINT32_C(100), UINT32_C(7)) == P0_SLOW_WAKE);
    assert(state.channel == P0_W2_PROFILE_CHANNEL);
    assert(state.direction == P0_W2_PROFILE_FORWARD_DIRECTION);
    assert(state.duty_permille == P0_W2_TARGET_DUTY_PERMILLE);
    assert(p0_slow_service(&state, UINT32_C(103), UINT32_C(7)) == P0_SLOW_RUN);
    assert(p0_slow_hold(&state, P0_W2_PROFILE_CHANNEL,
        P0_W2_PROFILE_FORWARD_DIRECTION, P0_W2_TARGET_DUTY_PERMILLE,
        UINT32_C(150), UINT32_C(7)) == P0_SLOW_NONE);
    assert(p0_slow_hold(&state, P0_W2_PROFILE_CHANNEL,
        P0_W2_PROFILE_REVERSE_DIRECTION, P0_W2_TARGET_DUTY_PERMILLE,
        UINT32_C(151), UINT32_C(7)) == P0_SLOW_REJECT);
    assert(!state.armed);

    state = armed_state();
    assert(p0_slow_hold(&state, P0_W2_PROFILE_CHANNEL,
        P0_W2_PROFILE_REVERSE_DIRECTION, P0_W2_TARGET_DUTY_PERMILLE,
        UINT32_C(100), UINT32_C(7)) == P0_SLOW_WAKE);
    assert(p0_slow_hold(&state, P0_W2_PROFILE_CHANNEL, 0, 0,
        UINT32_C(120), UINT32_C(7)) == P0_SLOW_OFF);
    assert(state.phase == P0_SLOW_ENDED);

    state = armed_state();
    assert(p0_slow_hold(&state, 0, P0_W2_PROFILE_FORWARD_DIRECTION,
        P0_W2_TARGET_DUTY_PERMILLE, UINT32_C(100), UINT32_C(7)) ==
        P0_SLOW_REJECT);
    state = armed_state();
    assert(p0_slow_hold(&state, P0_W2_PROFILE_CHANNEL,
        P0_W2_PROFILE_FORWARD_DIRECTION, UINT16_C(50), UINT32_C(100),
        UINT32_C(7)) == P0_SLOW_REJECT);

    state = armed_state();
    assert(p0_slow_hold(&state, P0_W2_PROFILE_CHANNEL,
        P0_W2_PROFILE_FORWARD_DIRECTION, P0_W2_TARGET_DUTY_PERMILLE,
        UINT32_C(100), UINT32_C(7)) == P0_SLOW_WAKE);
    assert(p0_slow_service(&state, UINT32_C(176), UINT32_C(7)) ==
        P0_SLOW_REJECT);
    state = armed_state();
    assert(p0_slow_service(&state, UINT32_C(1101), UINT32_C(7)) ==
        P0_SLOW_REJECT);

    puts("PASS: W2 four-wheel profile admission, lease and re-arm gates");
    return 0;
}
