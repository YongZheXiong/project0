#include "p0_usb_manual.h"

void p0_usb_manual_init(p0_usb_manual_t *m)
{
    *m = (p0_usb_manual_t){0};
}

p0_usb_action_t p0_usb_manual_accept(p0_usb_manual_t *m,
    p0_usb_quiet_t *s, p0_usb_motion_guard_t *g,
    const p0_packet_t *p, uint32_t now, bool disarmed)
{
    static const uint8_t magic[] = {'P','0','U','M','2'};
    p0_usb_quiet_tick(s, now);
    if (s->phase == P0_USB_CLOSED) return P0_USB_IGNORE;
    if (p->type == P0_USB_HELLO) {
        if (!disarmed || (s->phase == P0_USB_ACTIVE && !m->stopped) ||
            m->count >= P0_USB_MANUAL_SESSIONS || !p->session_id ||
            p->sequence != 1 || p->payload_length != sizeof(magic)) goto reject;
        for (size_t i = 0; i < sizeof(magic); ++i)
            if (p->payload[i] != magic[i]) goto reject;
        for (uint8_t i = 0; i < m->count; ++i)
            if (m->sessions[i] == p->session_id) goto reject;
        /* 仅在前一正常STOP已使控制器失能后，交付一个新的一次性ARM。 */
        m->sessions[m->count++] = p->session_id;
        m->stopped = false;
        p0_usb_motion_init(g);
        s->phase = P0_USB_ACTIVE;
        s->session = p->session_id;
        s->sequence = 1;
        s->heartbeat_ms = now;
        return P0_USB_OPEN;
    }
    if (s->phase != P0_USB_ACTIVE) return P0_USB_IGNORE;
    if (p->session_id != s->session || s->sequence == UINT32_MAX ||
        p->sequence != s->sequence + 1 ||
        p->payload_length != (p->type == P0_MSG_WHEEL_TARGET ? 8 : 0)) goto reject;
    if (p->type != P0_MSG_HEARTBEAT && p->type != P0_MSG_STOP &&
        p->type != P0_MSG_DISARM && p->type != P0_MSG_ARM &&
        p->type != P0_MSG_WHEEL_TARGET && p->type != P0_USB_QUIET) goto reject;
    if (m->stopped && (p->type == P0_MSG_ARM || p->type == P0_MSG_WHEEL_TARGET)) goto reject;
    s->sequence = p->sequence;
    if (p->type == P0_MSG_HEARTBEAT) s->heartbeat_ms = now;
    if (p->type == P0_MSG_STOP || p->type == P0_MSG_DISARM) m->stopped = true;
    return p->type == P0_USB_QUIET ? P0_USB_CLOSE : P0_USB_PASS;
reject:
    p0_usb_quiet_stop(s);
    return P0_USB_IGNORE;
}
