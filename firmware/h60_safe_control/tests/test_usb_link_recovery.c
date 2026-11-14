#include "p0_usb_link_recovery.h"
#include "p0_usb_motion.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

int main(void)
{
    volatile p0_usb_boot_retained_t retained = {0};
    bool previous = true;
    assert(!p0_usb_boot_valid(&retained));
    assert(p0_usb_boot_advance(&retained, &previous) == 1 && !previous);
    assert(p0_usb_boot_advance(&retained, &previous) == 2 && previous);
    retained.inverse ^= 1;
    assert(p0_usb_boot_advance(&retained, &previous) == 1 && !previous);
    retained.magic = P0_USB_BOOT_MAGIC;
    retained.epoch = UINT32_MAX;
    retained.inverse = 0;
    assert(p0_usb_boot_advance(&retained, &previous) == 1 && previous);
    retained.magic = 0; /* 模拟写到一半复位。 */
    assert(p0_usb_boot_advance(&retained, &previous) == 1 && !previous);

    p0_packet_t hello = {0}, reply;
    uint32_t uid[3] = {1, 2, 3};
    hello.type = P0_USB_HELLO; hello.session_id = 123; hello.sequence = 1;
    hello.payload_length = 5; memcpy(hello.payload, "P0UR1", 5);
    p0_usb_boot_report(&reply, &hello, 1, 1, 0, 5, 7, 10, UINT32_C(0x04000000), uid);
    assert(reply.type == 0x84 && reply.session_id == 123 && reply.sequence == 1);
    assert(reply.payload_length == 40 && reply.payload[0] == 1 && reply.payload[6] == 21);
    assert(p0_read_u32_le(reply.payload + 8) == 7);
    assert(p0_read_u32_le(reply.payload + 12) == ~UINT32_C(7));
    assert(p0_read_u32_le(reply.payload + 32) == 3);
    assert(p0_read_u32_le(reply.payload + 36) == 224);

    p0_usb_quiet_t usb;
    p0_usb_quiet_init(&usb);
    assert(p0_usb_motion_accept(&usb, &hello, 10) == P0_USB_OPEN);
    p0_usb_quiet_stop(&usb);
    assert(p0_usb_motion_accept(&usb, &hello, 20) == P0_USB_IGNORE);
    assert(usb.phase == P0_USB_CLOSED);
    p0_usb_quiet_init(&usb);
    assert(p0_usb_motion_accept(&usb, &hello, 30) == P0_USB_OPEN);
    p0_usb_motion_guard_t guard;
    p0_usb_motion_init(&guard);
    assert(p0_usb_motion_arm(&guard, 50, 1));
    p0_usb_motion_stop(&guard);
    assert(!p0_usb_motion_arm(&guard, 60, 1));
    puts("NO_DEVICE: retained record, report, CLOSED silence and one ARM boundaries PASS");
    return 0;
}
