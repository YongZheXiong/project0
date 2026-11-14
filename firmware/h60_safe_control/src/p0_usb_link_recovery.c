#include "p0_usb_link_recovery.h"

bool p0_usb_boot_valid(const volatile p0_usb_boot_retained_t *r)
{
    return r != 0 && r->magic == P0_USB_BOOT_MAGIC && r->epoch != 0 &&
        r->inverse == ~r->epoch;
}

uint32_t p0_usb_boot_advance(volatile p0_usb_boot_retained_t *r, bool *prior_valid)
{
    bool valid = p0_usb_boot_valid(r);
    uint32_t next = valid ? r->epoch + UINT32_C(1) : UINT32_C(1);
    if (next == 0) next = 1;
    /* 中断写入宁可使下一次记录失效，不把半写记录当复位证明。 */
    r->magic = 0;
    r->epoch = next;
    r->inverse = ~next;
    r->magic = P0_USB_BOOT_MAGIC;
    if (prior_valid != 0) *prior_valid = valid;
    return next;
}

void p0_usb_boot_report(p0_packet_t *reply, const p0_packet_t *hello,
    uint8_t phase, uint8_t state, uint8_t fault, uint8_t flags,
    uint32_t epoch, uint32_t uptime_ms, uint32_t reset_flags, const uint32_t uid[3])
{
    *reply = (p0_packet_t){0};
    reply->type = P0_USB_BOOT_REPORT;
    reply->session_id = hello->session_id;
    reply->sequence = hello->sequence;
    reply->payload_length = 40;
    reply->payload[0] = 1;
    reply->payload[1] = phase;
    reply->payload[2] = state;
    reply->payload[3] = fault;
    reply->payload[4] = P0_FIRMWARE_VERSION_MAJOR;
    reply->payload[5] = P0_FIRMWARE_VERSION_MINOR;
    reply->payload[6] = P0_FIRMWARE_VERSION_PATCH;
    reply->payload[7] = flags;
    p0_write_u32_le(reply->payload + 8, epoch);
    p0_write_u32_le(reply->payload + 12, ~epoch);
    p0_write_u32_le(reply->payload + 16, uptime_ms);
    p0_write_u32_le(reply->payload + 20, reset_flags);
    for (unsigned i = 0; i < 3; ++i)
        p0_write_u32_le(reply->payload + 24 + 4*i, uid[i]);
    p0_write_u32_le(reply->payload + 36, P0_FIRMWARE_CAPABILITIES);
}
