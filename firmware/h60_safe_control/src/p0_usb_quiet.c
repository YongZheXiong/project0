#include "p0_usb_quiet.h"
void p0_usb_quiet_init(p0_usb_quiet_t *s)
{ s->phase = P0_USB_WAIT; s->session = 0; s->sequence = 0; s->heartbeat_ms = 0; }
void p0_usb_quiet_stop(p0_usb_quiet_t *s) { s->phase = P0_USB_CLOSED; }
void p0_usb_quiet_tick(p0_usb_quiet_t *s, uint32_t now)
{
    if (s->phase == P0_USB_ACTIVE && (uint32_t)(now - s->heartbeat_ms) >= P0_USB_LEASE_MS)
        p0_usb_quiet_stop(s);
}
p0_usb_action_t p0_usb_quiet_accept(p0_usb_quiet_t *s, const p0_packet_t *p, uint32_t now)
{
    static const uint8_t magic[5] = {'P','0','U','Q','1'};
    size_t i;
    p0_usb_quiet_tick(s, now); /* queued commands cannot revive an expired lease */
    if (s->phase == P0_USB_CLOSED) return P0_USB_IGNORE;
    if (s->phase == P0_USB_WAIT) {
        if (p->type != P0_USB_HELLO) return P0_USB_IGNORE;
        if (!p->session_id || p->sequence != 1 || p->payload_length != sizeof(magic))
            goto reject;
        for (i=0; i<sizeof(magic); ++i) if (p->payload[i] != magic[i]) goto reject;
        s->phase = P0_USB_ACTIVE; s->session = p->session_id;
        s->sequence = 1; s->heartbeat_ms = now;
        return P0_USB_OPEN;
    }
    if (p->session_id != s->session || s->sequence == UINT32_MAX ||
        p->sequence != s->sequence + 1 || p->payload_length != 0) goto reject;
    if (p->type != P0_MSG_HEARTBEAT && p->type != P0_MSG_STOP &&
        p->type != P0_MSG_DISARM && p->type != P0_USB_QUIET) goto reject;
    s->sequence = p->sequence;
    if (p->type == P0_MSG_HEARTBEAT) s->heartbeat_ms = now;
    if (p->type == P0_USB_QUIET) return P0_USB_CLOSE;
    return P0_USB_PASS;
reject:
    p0_usb_quiet_stop(s);
    return P0_USB_IGNORE;
}
