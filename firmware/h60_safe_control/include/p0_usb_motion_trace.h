#ifndef P0_USB_MOTION_TRACE_H
#define P0_USB_MOTION_TRACE_H

#include "p0_build_config.h"
#include "p0_protocol.h"

#define P0_TRACE_SELECT UINT8_C(0x0A)
#define P0_TRACE_READ UINT8_C(0x0B)
#define P0_TRACE_DATA UINT8_C(0x83)
#define P0_TRACE_CAPACITY UINT16_C(160)
#define P0_TRACE_SUMMARY UINT16_C(0xFFFF)
#define P0_TRACE_POST_MS UINT32_C(500)
#define P0_TRACE_STARTED UINT8_C(1)
#define P0_TRACE_STOPPED UINT8_C(2)
#define P0_TRACE_FROZEN UINT8_C(4)
#define P0_TRACE_OVERFLOW UINT8_C(8)
#define P0_TRACE_SELECTED UINT8_C(16)
#define P0_TRACE_PRIME UINT8_C(1)
#define P0_TRACE_CONTROL UINT8_C(2)
#define P0_TRACE_STOP UINT8_C(4)
#define P0_TRACE_POST UINT8_C(8)
#define P0_TRACE_COMMIT_OK UINT8_C(16)
#define P0_TRACE_COMMIT_FAILED UINT8_C(32)
#define P0_TRACE_CLAMPED UINT8_C(64)
#define P0_TRACE_IO_AF UINT8_C(1)
#define P0_TRACE_IO_CLOCK UINT8_C(2)
#define P0_TRACE_IO_CCER UINT8_C(4)
#define P0_TRACE_IO_MOE_OR_NA UINT8_C(8)
#define P0_TRACE_IO_COHERENT UINT8_C(16)
#define P0_TRACE_IO_RANGE UINT8_C(32)

typedef struct {
    uint16_t ccr1, ccr2;
    uint32_t generation;
    uint8_t flags;
} p0_trace_io_t;

typedef struct {
    uint32_t tick_ms;
    int32_t encoder_count;
    int16_t requested, ramped, measured, output;
    uint16_t ccr1, ccr2;
    uint32_t generation;
    uint8_t flags, io_flags;
    uint16_t reserved;
} p0_trace_record_t;

typedef struct {
    p0_trace_record_t records[P0_TRACE_CAPACITY];
    uint32_t armed_ms, stopped_ms, last_post_ms;
    uint16_t count;
    uint8_t channel, flags;
} p0_trace_t;

_Static_assert(sizeof(p0_trace_record_t) == 28, "trace record layout");
_Static_assert(sizeof(p0_trace_t) <= 4500, "trace RAM budget");

void p0_trace_init(p0_trace_t *trace);
bool p0_trace_select(p0_trace_t *trace, uint8_t channel);
bool p0_trace_start(p0_trace_t *trace, uint32_t now_ms);
void p0_trace_append(p0_trace_t *trace, const p0_trace_record_t *record);
bool p0_trace_stop(p0_trace_t *trace, uint32_t now_ms);
bool p0_trace_post_due(p0_trace_t *trace, uint32_t now_ms);
bool p0_trace_response(const p0_trace_t *trace, uint16_t index, p0_packet_t *response);

#endif
