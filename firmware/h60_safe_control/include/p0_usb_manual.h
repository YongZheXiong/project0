#ifndef P0_USB_MANUAL_H
#define P0_USB_MANUAL_H
#include "p0_usb_motion.h"

/* 仅28隔离候选使用；正常STOP后换新session，故障CLOSED永不恢复。 */
#define P0_USB_MANUAL_SESSIONS 8
typedef struct {
    uint32_t sessions[P0_USB_MANUAL_SESSIONS];
    uint8_t count;
    bool stopped;
} p0_usb_manual_t;

void p0_usb_manual_init(p0_usb_manual_t *manual);
p0_usb_action_t p0_usb_manual_accept(p0_usb_manual_t *manual,
    p0_usb_quiet_t *usb, p0_usb_motion_guard_t *motion,
    const p0_packet_t *packet, uint32_t now, bool disarmed);
#endif
