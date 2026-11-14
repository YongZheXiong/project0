#ifndef P0_USB_LINK_RECOVERY_H
#define P0_USB_LINK_RECOVERY_H

#include "p0_build_config.h"
#include "p0_protocol.h"

#define P0_USB_BOOT_REPORT UINT8_C(0x84)
#define P0_USB_BOOT_MAGIC UINT32_C(0x50425231)
#define P0_BOOT_PRIOR_VALID UINT8_C(1)
#define P0_BOOT_ARM_SPENT UINT8_C(2)
#define P0_BOOT_TX_ACTIVE UINT8_C(4)

/* SRAM保留记录不是密码学身份；断电/损坏后不保证连续编号。 */
typedef struct {
    uint32_t magic;
    uint32_t epoch;
    uint32_t inverse;
} p0_usb_boot_retained_t;

bool p0_usb_boot_valid(const volatile p0_usb_boot_retained_t *record);
uint32_t p0_usb_boot_advance(volatile p0_usb_boot_retained_t *record, bool *prior_valid);
void p0_usb_boot_report(p0_packet_t *reply, const p0_packet_t *hello,
    uint8_t phase, uint8_t state, uint8_t fault, uint8_t flags,
    uint32_t epoch, uint32_t uptime_ms, uint32_t reset_flags, const uint32_t uid[3]);

#endif
