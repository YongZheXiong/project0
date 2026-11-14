#ifndef P0_USB_MOTION_H
#define P0_USB_MOTION_H

#include "p0_build_config.h"
#include "p0_motion.h"
#include "p0_usb_quiet.h"

/* 工程受控候选，非生产标定。旧构建边界原样保留。 */
#if P0_USB_INTEGRATED_BUILD != 0
#define P0_UM_TARGET_LIMIT INT16_C(40)
#define P0_UM_OUTPUT_LIMIT INT16_C(200)
#define P0_UM_KP_Q10 INT32_C(6144)
#define P0_UM_KI_Q10 INT32_C(2048)
#define P0_UM_MAX_ARMED_MS UINT32_C(20000)
#else
#define P0_UM_TARGET_LIMIT INT16_C(20)
#define P0_UM_KI_Q10 INT32_C(0)
#define P0_UM_MAX_ARMED_MS UINT32_C(1000)
#if P0_USB_STARTUP_CANDIDATE_BUILD != 0 || P0_USB_FOUR_WHEEL_CANDIDATE_BUILD != 0
#define P0_UM_OUTPUT_LIMIT INT16_C(120)
#define P0_UM_KP_Q10 INT32_C(6144)
#else
#define P0_UM_OUTPUT_LIMIT INT16_C(80)
#define P0_UM_KP_Q10 INT32_C(4096)
#endif
#endif
#define P0_UM_TARGET_LEASE_MS UINT32_C(75)
#define P0_UM_WAKE_MS UINT32_C(3)

typedef struct {
    volatile bool armed;
    volatile bool spent;
    volatile uint32_t armed_ms;
    volatile uint32_t target_ms;
    volatile uint32_t stop_generation;
} p0_usb_motion_guard_t;

p0_motion_config_t p0_usb_motion_config(void);
void p0_usb_motion_init(p0_usb_motion_guard_t *guard);
void p0_usb_motion_stop(p0_usb_motion_guard_t *guard);
bool p0_usb_motion_arm(p0_usb_motion_guard_t *guard, uint32_t now, uint32_t generation);
bool p0_usb_motion_fresh(const p0_usb_motion_guard_t *guard, uint32_t now, uint32_t generation);
p0_usb_action_t p0_usb_motion_accept(p0_usb_quiet_t *usb, const p0_packet_t *packet, uint32_t now);

#endif
