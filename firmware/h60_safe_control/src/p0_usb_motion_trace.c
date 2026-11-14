#include "p0_usb_motion_trace.h"

/* 主循环单写者；固定数组、不覆盖、不等待、不在IRQ中写记录。 */
void p0_trace_init(p0_trace_t *t)
{
    t->armed_ms = t->stopped_ms = t->last_post_ms = 0;
    t->count = 0;
    t->channel = UINT8_MAX;
    t->flags = 0;
}

bool p0_trace_select(p0_trace_t *t, uint8_t channel)
{
    if (channel >= 4 || t->flags != 0) return false;
    t->channel = channel;
    t->flags = P0_TRACE_SELECTED;
    return true;
}

bool p0_trace_start(p0_trace_t *t, uint32_t now)
{
    if (t->flags != P0_TRACE_SELECTED) return false;
    t->armed_ms = now;
    t->flags |= P0_TRACE_STARTED;
    return true;
}

void p0_trace_append(p0_trace_t *t, const p0_trace_record_t *record)
{
    if (!(t->flags & P0_TRACE_STARTED) || (t->flags & P0_TRACE_FROZEN)) return;
    if (t->count >= P0_TRACE_CAPACITY) {
        t->flags |= P0_TRACE_OVERFLOW | P0_TRACE_FROZEN;
        return;
    }
    t->records[t->count++] = *record;
}

bool p0_trace_stop(p0_trace_t *t, uint32_t now)
{
    if (!(t->flags & P0_TRACE_STARTED) || (t->flags & P0_TRACE_STOPPED)) return false;
    t->flags |= P0_TRACE_STOPPED;
    t->stopped_ms = t->last_post_ms = now;
    return true;
}

bool p0_trace_post_due(p0_trace_t *t, uint32_t now)
{
    if (!(t->flags & P0_TRACE_STOPPED) || (t->flags & P0_TRACE_FROZEN)) return false;
    if ((uint32_t)(now - t->stopped_ms) >= P0_TRACE_POST_MS) {
        t->flags |= P0_TRACE_FROZEN;
        return false;
    }
    if ((uint32_t)(now - t->last_post_ms) < 10) return false;
    t->last_post_ms = now;
    return true;
}

bool p0_trace_response(const p0_trace_t *t, uint16_t index, p0_packet_t *p)
{
    if (!(t->flags & P0_TRACE_STOPPED) || !(t->flags & P0_TRACE_STARTED)) return false;
    if (index != P0_TRACE_SUMMARY &&
        (!(t->flags & P0_TRACE_FROZEN) || index >= t->count)) return false;
    p->type = P0_TRACE_DATA;
    p->payload_length = 36;
    for (unsigned i = 0; i < 36; ++i) p->payload[i] = 0;
    p->payload[0] = 1;
    p->payload[1] = t->channel;
    p0_write_u16_le(p->payload + 2, index);
    p0_write_u16_le(p->payload + 4, t->count);
    p->payload[6] = t->flags;
    if (index != P0_TRACE_SUMMARY) {
        const p0_trace_record_t *r = &t->records[index];
        p0_write_u32_le(p->payload + 8, r->tick_ms);
        p0_write_u32_le(p->payload + 12, (uint32_t)r->encoder_count);
        p0_write_i16_le(p->payload + 16, r->requested);
        p0_write_i16_le(p->payload + 18, r->ramped);
        p0_write_i16_le(p->payload + 20, r->measured);
        p0_write_i16_le(p->payload + 22, r->output);
        p0_write_u16_le(p->payload + 24, r->ccr1);
        p0_write_u16_le(p->payload + 26, r->ccr2);
        p0_write_u32_le(p->payload + 28, r->generation);
        p->payload[32] = r->flags;
        p->payload[33] = r->io_flags;
    }
    return true;
}
