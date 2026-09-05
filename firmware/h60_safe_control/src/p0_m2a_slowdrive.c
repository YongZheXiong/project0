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
        (uint32_t)(now - s->armed_at_ms) <= P0_M2A_MAX_ARMED_MS &&
        ((s->phase != P0_SLOW_WAKING && s->phase != P0_SLOW_ACTIVE) ||
         (uint32_t)(now - s->last_hold_ms) <= P0_M2A_HOLD_LEASE_MS);
}

static p0_slow_action_t reject(p0_m2a_slowdrive_t *s)
{
    s->armed = false;
    s->phase = P0_SLOW_ENDED;
    return P0_SLOW_REJECT;
}

p0_slow_action_t p0_slow_hold(p0_m2a_slowdrive_t *s, uint8_t channel,
    int8_t direction, uint16_t duty, uint32_t now, uint32_t generation)
{
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
}

p0_slow_action_t p0_slow_service(p0_m2a_slowdrive_t *s, uint32_t now,
    uint32_t generation)
{
    if (!s->armed) return P0_SLOW_NONE;
    /* 零命令已撤销的生命周期不再提交动作；绝对会话期限仍有效。 */
    if (s->phase == P0_SLOW_ENDED) {
        if ((uint32_t)(now - s->armed_at_ms) > P0_M2A_MAX_ARMED_MS)
            return reject(s);
        return P0_SLOW_NONE;
    }
    if (!p0_slow_fresh(s, now, generation)) return reject(s);
    if (s->phase == P0_SLOW_WAKING &&
        (uint32_t)(now - s->wake_at_ms) >= P0_SLOW_WAKE_MS) {
        s->phase = P0_SLOW_ACTIVE;
        return P0_SLOW_RUN;
    }
    return P0_SLOW_NONE;
}
