#include "p0_m2a_slowdrive.h"

void p0_slow_reset(p0_m2a_slowdrive_t *s)
{
    *s = (p0_m2a_slowdrive_t){0};
}

void p0_slow_arm(p0_m2a_slowdrive_t *s, uint32_t now, uint32_t generation)
{
    p0_slow_reset(s);
    s->armed = true;
    s->armed_at_ms = s->last_hold_ms = now;
    s->generation = generation;
}

bool p0_slow_fresh(const p0_m2a_slowdrive_t *s, uint32_t now, uint32_t generation)
{
    return s->armed && s->generation == generation &&
        (uint32_t)(now - s->armed_at_ms) <= P0_SLOW_MAX_ARMED_MS &&
        ((s->phase != P0_SLOW_WAKING && s->phase != P0_SLOW_ACTIVE) ||
         (uint32_t)(now - s->last_hold_ms) <= P0_M2A_HOLD_LEASE_MS);
}

static p0_slow_action_t reject(p0_m2a_slowdrive_t *s)
{
    s->armed = false;
    s->phase = P0_SLOW_ENDED;
    return P0_SLOW_REJECT;
}

#if P0_H6_EXTENDED_WINDOW_BUILD != 0
static uint16_t h6_r2_envelope_duty(uint32_t elapsed_ms)
{
    uint32_t remaining_ms;

    if (elapsed_ms < P0_H6_R2_RAMP_UP_MS) {
        return (uint16_t)((P0_H6_R2_TARGET_DUTY_PERMILLE *
            (elapsed_ms + UINT32_C(1)) + P0_H6_R2_RAMP_UP_MS - UINT32_C(1)) /
            P0_H6_R2_RAMP_UP_MS);
    }
    if (elapsed_ms < P0_H6_R2_RAMP_UP_MS + P0_H6_R2_HOLD_MS) {
        return P0_H6_R2_TARGET_DUTY_PERMILLE;
    }
    remaining_ms = P0_H6_R2_NONZERO_WINDOW_MS - elapsed_ms;
    return (uint16_t)((P0_H6_R2_TARGET_DUTY_PERMILLE * remaining_ms +
        P0_H6_R2_RAMP_DOWN_MS - UINT32_C(1)) / P0_H6_R2_RAMP_DOWN_MS);
}
#endif

p0_slow_action_t p0_slow_hold(p0_m2a_slowdrive_t *s, uint8_t channel,
    int8_t direction, uint16_t duty, uint32_t now, uint32_t generation)
{
#if P0_H6_CHARACTERIZATION_BUILD != 0
    bool zero_request;
    bool nonzero_request;
    bool same_duty;

    /* 先检查旧租约，再接收续租；不能用迟到命令延长旧权限。 */
#if P0_W2_FOUR_WHEEL_PROFILE_BUILD != 0
    zero_request = channel == P0_W2_PROFILE_CHANNEL &&
        direction == 0 && duty == 0;
    nonzero_request = channel == P0_W2_PROFILE_CHANNEL &&
        (direction == P0_W2_PROFILE_FORWARD_DIRECTION ||
         direction == P0_W2_PROFILE_REVERSE_DIRECTION) &&
        duty == P0_W2_TARGET_DUTY_PERMILLE;
    same_duty = duty == s->duty_permille;
#elif P0_H6_EXTENDED_WINDOW_BUILD != 0
    zero_request = channel < P0_M2A_CHANNEL_COUNT &&
        direction == 0 && duty == 0;
    nonzero_request = channel == P0_H6_R2_CHANNEL &&
        direction == P0_H6_R2_DIRECTION &&
        duty == P0_H6_R2_TARGET_DUTY_PERMILLE;
    same_duty = duty == s->target_duty_permille;
#else
    zero_request = channel < P0_M2A_CHANNEL_COUNT &&
        direction == 0 && duty == 0;
    nonzero_request = channel < P0_M2A_CHANNEL_COUNT &&
        (direction == INT8_C(-1) || direction == INT8_C(1)) &&
        duty >= P0_M2A_MIN_DUTY_PERMILLE &&
        duty <= P0_M2A_MAX_DUTY_PERMILLE;
    same_duty = duty == s->duty_permille;
#endif
#else
    /* 先检查旧租约，再接收续租；不能用迟到命令延长旧权限。 */
    if (!p0_slow_fresh(s, now, generation) || channel != 1 ||
        !((direction == 0 && duty == 0) || (direction == 1 && duty == 50))) {
        return reject(s);
    }
    if (direction == 0) {
        if (s->phase == P0_SLOW_IDLE || s->phase == P0_SLOW_ENDED)
            return P0_SLOW_NONE;
        s->phase = P0_SLOW_ENDED;
        return P0_SLOW_OFF;
    }
    if (s->phase == P0_SLOW_ENDED) return reject(s);
    s->last_hold_ms = now;
    if (s->phase == P0_SLOW_IDLE) {
        s->phase = P0_SLOW_WAKING;
        s->wake_at_ms = now; /* 硬件接管成功后用新的毫秒读数覆盖。 */
        return P0_SLOW_WAKE;
    }
    return P0_SLOW_NONE;
#endif
#if P0_H6_CHARACTERIZATION_BUILD != 0
    if (!p0_slow_fresh(s, now, generation) ||
        !(zero_request || nonzero_request) ||
        (zero_request && s->phase != P0_SLOW_IDLE && channel != s->channel) ||
        (nonzero_request && s->phase != P0_SLOW_IDLE &&
         (channel != s->channel || direction != s->direction || !same_duty))) {
        return reject(s);
    }
    if (zero_request) {
        if (s->phase == P0_SLOW_IDLE || s->phase == P0_SLOW_ENDED)
            return P0_SLOW_NONE;
        s->phase = P0_SLOW_ENDED;
        return P0_SLOW_OFF;
    }
    if (s->phase == P0_SLOW_ENDED) return reject(s);
    s->last_hold_ms = now;
    if (s->phase == P0_SLOW_IDLE) {
        s->channel = channel;
        s->direction = direction;
#if P0_H6_EXTENDED_WINDOW_BUILD != 0
        s->duty_permille = 0;
        s->target_duty_permille = duty;
#else
        s->duty_permille = duty;
#endif
        s->phase = P0_SLOW_WAKING;
        s->wake_at_ms = now; /* 硬件接管成功后用新的毫秒读数覆盖。 */
        return P0_SLOW_WAKE;
    }
    return P0_SLOW_NONE;
#endif
}

p0_slow_action_t p0_slow_service(p0_m2a_slowdrive_t *s, uint32_t now,
    uint32_t generation)
{
    if (!s->armed) return P0_SLOW_NONE;
    /* 零命令已撤销的生命周期不再提交动作；绝对会话期限仍有效。 */
    if (s->phase == P0_SLOW_ENDED) {
        if ((uint32_t)(now - s->armed_at_ms) > P0_SLOW_MAX_ARMED_MS)
            return reject(s);
        return P0_SLOW_NONE;
    }
    if (!p0_slow_fresh(s, now, generation)) return reject(s);
    if (s->phase == P0_SLOW_WAKING &&
        (uint32_t)(now - s->wake_at_ms) >= P0_SLOW_WAKE_MS) {
        s->phase = P0_SLOW_ACTIVE;
#if P0_H6_EXTENDED_WINDOW_BUILD != 0
        uint32_t elapsed_ms;

        s->envelope_started_at_ms = s->wake_at_ms + P0_SLOW_WAKE_MS;
        elapsed_ms = (uint32_t)(now - s->envelope_started_at_ms);
        if (elapsed_ms >= P0_H6_R2_NONZERO_WINDOW_MS) {
            s->phase = P0_SLOW_ENDED;
            return P0_SLOW_OFF;
        }
        s->duty_permille = h6_r2_envelope_duty(elapsed_ms);
#endif
        return P0_SLOW_RUN;
    }
#if P0_H6_EXTENDED_WINDOW_BUILD != 0
    if (s->phase == P0_SLOW_ACTIVE) {
        uint32_t elapsed_ms = (uint32_t)(now - s->envelope_started_at_ms);
        uint16_t duty;

        if (elapsed_ms >= P0_H6_R2_NONZERO_WINDOW_MS) {
            s->duty_permille = 0;
            s->phase = P0_SLOW_ENDED;
            return P0_SLOW_OFF;
        }
        duty = h6_r2_envelope_duty(elapsed_ms);
        if (duty != s->duty_permille) {
            s->duty_permille = duty;
            return P0_SLOW_RUN;
        }
    }
#endif
    return P0_SLOW_NONE;
}
