#include "p0_usb_motion.h"
#include "p0_usb_motion_trace.h"

p0_motion_config_t p0_usb_motion_config(void)
{
    /* 269是已记录范围的下端工程换算，非有效轮周测量/标定值。 */
    const p0_motion_config_t config = {
        .control_period_ms = 10,
        .encoder_counts_per_revolution = {2926, 2923, 2929, 2922},
        .maximum_encoder_delta_counts = {12, 12, 12, 12},
        .wheel_circumference_mm = {269, 269, 269, 269},
        .encoder_counter_bits = {32, 16, 32, 16},
        .encoder_polarity = {1, -1, 1, -1},
        .maximum_target_mm_s = P0_UM_TARGET_LIMIT,
        .acceleration_mm_s2 = 100,
        .deceleration_mm_s2 = 100,
        .reversal_zero_hold_ms = 300,
        .zero_speed_threshold_mm_s = 0,
        .maximum_output_permille = P0_UM_OUTPUT_LIMIT,
        .kp_q10 = P0_UM_KP_Q10,
        .ki_q10_per_s = P0_UM_KI_Q10,
    };
    return config;
}

void p0_usb_motion_init(p0_usb_motion_guard_t *g)
{ *g = (p0_usb_motion_guard_t){0}; }
void p0_usb_motion_stop(p0_usb_motion_guard_t *g) { g->armed = false; }

bool p0_usb_motion_arm(p0_usb_motion_guard_t *g, uint32_t now, uint32_t generation)
{
    if (g->spent) return false;
    g->spent = g->armed = true;
    g->armed_ms = g->target_ms = now;
    g->stop_generation = generation;
    return true;
}

bool p0_usb_motion_fresh(const p0_usb_motion_guard_t *g, uint32_t now, uint32_t generation)
{
    return g != 0 && g->armed && g->stop_generation == generation &&
        (uint32_t)(now - g->target_ms) < P0_UM_TARGET_LEASE_MS &&
        (uint32_t)(now - g->armed_ms) < P0_UM_MAX_ARMED_MS;
}

p0_usb_action_t p0_usb_motion_accept(p0_usb_quiet_t *s, const p0_packet_t *p, uint32_t now)
{
#if P0_USB_INTEGRATED_BUILD != 0
    static const uint8_t magic[] = {'P','0','U','I','1'};
#elif P0_USB_VELOCITY_DIAG_BUILD != 0
    static const uint8_t magic[] = {'P','0','U','V','1'};
#elif P0_USB_CONTROL_DIAG_BUILD != 0
    static const uint8_t magic[] = {'P','0','U','C','1'};
#elif P0_USB_RX_DIAG_BUILD != 0
    static const uint8_t magic[] = {'P','0','U','D','1'};
#elif P0_USB_ENCODER_FILTER_BUILD != 0
    static const uint8_t magic[] = {'P','0','U','E','1'};
#elif P0_USB_LINK_RECOVERY_BUILD != 0
    static const uint8_t magic[] = {'P','0','U','R','1'};
#elif P0_USB_FOUR_WHEEL_CANDIDATE_BUILD != 0
    static const uint8_t magic[] = {'P','0','U','F','1'};
#elif P0_USB_STARTUP_CANDIDATE_BUILD != 0
    static const uint8_t magic[] = {'P','0','U','S','1'};
#elif P0_USB_MOTION_TRACE_BUILD != 0
    static const uint8_t magic[] = {'P','0','U','T','1'};
#else
    static const uint8_t magic[] = {'P','0','U','M','1'};
#endif
    size_t i;
    uint16_t length = p->type == P0_MSG_WHEEL_TARGET ? UINT16_C(8) : 0;
#if P0_USB_MOTION_TRACE_BUILD != 0
    if (p->type == P0_TRACE_SELECT) length = 1;
    if (p->type == P0_TRACE_READ) length = 2;
#endif
    p0_usb_quiet_tick(s, now);
    if (s->phase == P0_USB_CLOSED) return P0_USB_IGNORE;
    if (s->phase == P0_USB_WAIT) {
        if (p->type != P0_USB_HELLO) return P0_USB_IGNORE;
        if (!p->session_id || p->sequence != 1 || p->payload_length != sizeof(magic))
            goto reject;
        for (i = 0; i < sizeof(magic); ++i)
            if (p->payload[i] != magic[i]) goto reject;
        s->phase = P0_USB_ACTIVE;
        s->session = p->session_id;
        s->sequence = 1;
        s->heartbeat_ms = now;
        return P0_USB_OPEN;
    }
    if (p->session_id != s->session || s->sequence == UINT32_MAX ||
        p->sequence != s->sequence + 1 || p->payload_length != length)
        goto reject;
    if (p->type != P0_MSG_HEARTBEAT && p->type != P0_MSG_STOP &&
        p->type != P0_MSG_DISARM && p->type != P0_MSG_ARM &&
        p->type != P0_MSG_WHEEL_TARGET && p->type != P0_USB_QUIET
#if P0_USB_MOTION_TRACE_BUILD != 0
        && p->type != P0_TRACE_SELECT && p->type != P0_TRACE_READ
#endif
        )
        goto reject;
    s->sequence = p->sequence;
    if (p->type == P0_MSG_HEARTBEAT) s->heartbeat_ms = now;
    return p->type == P0_USB_QUIET ? P0_USB_CLOSE : P0_USB_PASS;
reject:
    p0_usb_quiet_stop(s);
    return P0_USB_IGNORE;
}
