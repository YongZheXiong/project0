#ifndef P0_USB_DIAG_H
#define P0_USB_DIAG_H

#include <stdbool.h>
#include <stdint.h>
#include "p0_build_config.h"

/* 四个单写者上下文；不读外设、不发串口、不改变保护状态。 */
#define P0_DIAG_MAGIC UINT32_C(0x50304431)
#define P0_DIAG_SCHEMA UINT32_C(1)
#define P0_DIAG_ADDRESS UINT32_C(0x2001C000)
#define P0_DIAG_BANK_BYTES UINT32_C(7504)
#define P0_DIAG_BYTES (P0_DIAG_BANK_BYTES * 2)
enum { P0_DIAG_MAIN, P0_DIAG_UART, P0_DIAG_TICK, P0_DIAG_FAULT, P0_DIAG_LANES };
enum {
    P0_DIAG_BOOT = 1, P0_DIAG_HW_READY, P0_DIAG_MAIN_READY,
    P0_DIAG_RX_BYTE, P0_DIAG_RX_FAULT, P0_DIAG_PARSE_ERROR,
    P0_DIAG_PACKET, P0_DIAG_ACTION, P0_DIAG_TX_BEGIN,
    P0_DIAG_TX_COMPLETE, P0_DIAG_TX_ABORT, P0_DIAG_TX_QUIET,
    P0_DIAG_STATE, P0_DIAG_TRAP, P0_DIAG_ACK_QUEUED,
    P0_DIAG_TX_LEASE_EXPIRED
};
typedef struct { uint32_t value, inverse; } p0_diag_word_t;
typedef struct { p0_diag_word_t word[5]; } p0_diag_event_t;
typedef struct {
    /* magic/schema/bytes/epoch/reset CSR/UID[0..2]，magic最后提交。 */
    p0_diag_word_t header[8];
    p0_diag_event_t uart[96], main[64], tick[16], fault[8];
    p0_diag_event_t last_hello, last_ack_complete;
} p0_diag_bank_t;
typedef struct { p0_diag_bank_t bank[2]; } p0_diag_store_t;

#if P0_USB_RX_DIAG_BUILD != 0
extern volatile p0_diag_store_t g_p0_diag_store;
void p0_diag_boot(uint32_t reset_flags, const uint32_t uid[3]);
void p0_diag_emit(unsigned lane, uint32_t tick_ms, uint32_t event, uint32_t a, uint32_t b);
/* HAL按IPSR选择单写者lane；测试以显式替身实现。 */
void p0_hw_diag_event(uint32_t event, uint32_t a, uint32_t b);
#define P0_DIAG(event, a, b) p0_hw_diag_event((event), (a), (b))
#else
#define P0_DIAG(event, a, b) ((void)0)
#endif
#endif
