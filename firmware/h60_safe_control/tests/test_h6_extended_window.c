#include "p0_m2a_slowdrive.h"
#include <assert.h>
#include <stdio.h>

static uint16_t expected_duty(uint32_t elapsed_ms)
{
    if (elapsed_ms < P0_H6_R2_RAMP_UP_MS) {
        return (uint16_t)((P0_H6_R2_TARGET_DUTY_PERMILLE *
            (elapsed_ms + UINT32_C(1)) + P0_H6_R2_RAMP_UP_MS - UINT32_C(1)) /
            P0_H6_R2_RAMP_UP_MS);
    }
    if (elapsed_ms < P0_H6_R2_RAMP_UP_MS + P0_H6_R2_HOLD_MS) {
        return P0_H6_R2_TARGET_DUTY_PERMILLE;
    }
    return (uint16_t)((P0_H6_R2_TARGET_DUTY_PERMILLE *
        (P0_H6_R2_NONZERO_WINDOW_MS - elapsed_ms) +
        P0_H6_R2_RAMP_DOWN_MS - UINT32_C(1)) / P0_H6_R2_RAMP_DOWN_MS);
}

static void run_envelope(uint32_t start)
{
    p0_m2a_slowdrive_t state;
    uint32_t envelope_start;
    uint16_t previous = 0;

    p0_slow_arm(&state, start, 9);
    assert(p0_slow_hold(&state, P0_H6_R2_CHANNEL, P0_H6_R2_DIRECTION,
                        P0_H6_R2_TARGET_DUTY_PERMILLE, start + 1, 9) ==
           P0_SLOW_WAKE);
    assert(state.target_duty_permille == P0_H6_R2_TARGET_DUTY_PERMILLE);
    assert(state.duty_permille == 0);
    state.wake_at_ms = start + 1;
    envelope_start = start + 1 + P0_SLOW_WAKE_MS;

    for (uint32_t elapsed = 0; elapsed < P0_H6_R2_NONZERO_WINDOW_MS;
         ++elapsed) {
        uint32_t now = envelope_start + elapsed;
        p0_slow_action_t action;
        uint16_t expected = expected_duty(elapsed);

        if (elapsed % UINT32_C(25) == 0) {
            assert(p0_slow_hold(&state, P0_H6_R2_CHANNEL,
                                P0_H6_R2_DIRECTION,
                                P0_H6_R2_TARGET_DUTY_PERMILLE, now, 9) ==
                   P0_SLOW_NONE);
        }
        action = p0_slow_service(&state, now, 9);
        assert(state.duty_permille == expected);
        assert(action == ((elapsed == 0 || expected != previous) ?
                          P0_SLOW_RUN : P0_SLOW_NONE));
        previous = expected;
    }
    assert(previous == 1);
    assert(p0_slow_hold(&state, P0_H6_R2_CHANNEL, P0_H6_R2_DIRECTION,
                        P0_H6_R2_TARGET_DUTY_PERMILLE,
                        envelope_start + P0_H6_R2_NONZERO_WINDOW_MS, 9) ==
           P0_SLOW_NONE);
    assert(p0_slow_service(&state,
                           envelope_start + P0_H6_R2_NONZERO_WINDOW_MS, 9) ==
           P0_SLOW_OFF);
    assert(state.duty_permille == 0 && state.phase == P0_SLOW_ENDED);
}

int main(void)
{
    p0_m2a_slowdrive_t state;
    unsigned cases = 0;

    assert(P0_H6_CHARACTERIZATION_BUILD == 1);
    assert(P0_H6_EXTENDED_WINDOW_BUILD == 1);
    assert(P0_SLOW_MAX_ARMED_MS == 2500);
    assert(P0_M2A_HOLD_LEASE_MS == 75);
    assert(P0_H6_R2_NONZERO_WINDOW_MS == 1800);

    for (unsigned channel = 0; channel < 5; ++channel) {
        for (int direction = -2; direction <= 2; ++direction) {
            for (unsigned duty = 0; duty <= 121; ++duty) {
                bool valid = channel < 4 &&
                    ((direction == 0 && duty == 0) ||
                     (channel == P0_H6_R2_CHANNEL &&
                      direction == P0_H6_R2_DIRECTION &&
                      duty == P0_H6_R2_TARGET_DUTY_PERMILLE));
                p0_slow_arm(&state, 0, 9);
                assert((p0_slow_hold(&state, (uint8_t)channel,
                                     (int8_t)direction, (uint16_t)duty,
                                     1, 9) != P0_SLOW_REJECT) == valid);
                ++cases;
            }
        }
    }

    run_envelope(0);
    run_envelope(UINT32_MAX - UINT32_C(900));

    p0_slow_arm(&state, 0, 9);
    assert(p0_slow_hold(&state, P0_H6_R2_CHANNEL, P0_H6_R2_DIRECTION,
                        P0_H6_R2_TARGET_DUTY_PERMILLE, 1, 9) == P0_SLOW_WAKE);
    assert(p0_slow_service(&state, 77, 9) == P0_SLOW_REJECT);

    p0_slow_arm(&state, 0, 9);
    assert(p0_slow_service(&state, 2500, 9) == P0_SLOW_NONE);
    assert(p0_slow_service(&state, 2501, 9) == P0_SLOW_REJECT);

    p0_slow_arm(&state, 0, 9);
    assert(p0_slow_hold(&state, P0_H6_R2_CHANNEL, P0_H6_R2_DIRECTION,
                        P0_H6_R2_TARGET_DUTY_PERMILLE, 1, 9) == P0_SLOW_WAKE);
    state.wake_at_ms = 1;
    state.last_hold_ms = 1 + P0_SLOW_WAKE_MS + P0_H6_R2_NONZERO_WINDOW_MS;
    assert(p0_slow_service(&state,
                           1 + P0_SLOW_WAKE_MS +
                           P0_H6_R2_NONZERO_WINDOW_MS, 9) == P0_SLOW_OFF);
    assert(state.duty_permille == 0);

    printf("PASS: H6-R2 %u admission cases and 300/1200/300 ms envelope\n",
           cases);
}
