#ifndef P0_USB_QUIET_H
#define P0_USB_QUIET_H
#include "p0_protocol.h"
#define P0_USB_HELLO UINT8_C(0x08)
#define P0_USB_QUIET UINT8_C(0x09)
#define P0_USB_LEASE_MS UINT32_C(250)
typedef enum { P0_USB_WAIT, P0_USB_ACTIVE, P0_USB_CLOSED } p0_usb_phase_t;
typedef struct {
    p0_usb_phase_t phase;
    uint32_t session, sequence, heartbeat_ms;
} p0_usb_quiet_t;
typedef enum { P0_USB_IGNORE, P0_USB_OPEN, P0_USB_PASS, P0_USB_CLOSE } p0_usb_action_t;
void p0_usb_quiet_init(p0_usb_quiet_t *s);
void p0_usb_quiet_stop(p0_usb_quiet_t *s);
void p0_usb_quiet_tick(p0_usb_quiet_t *s, uint32_t now);
p0_usb_action_t p0_usb_quiet_accept(p0_usb_quiet_t *s, const p0_packet_t *p, uint32_t now);
#endif
