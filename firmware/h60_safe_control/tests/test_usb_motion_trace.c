#include "p0_usb_motion_trace.h"
#include <assert.h>
#include <limits.h>
#include <stdio.h>

int main(void)
{
    p0_trace_t t;
    p0_packet_t packet = {0};
    p0_trace_record_t r = {.tick_ms=10, .encoder_count=-2, .requested=20,
        .ramped=10, .measured=18, .output=8, .ccr1=3200, .ccr2=3174,
        .generation=7, .flags=P0_TRACE_CONTROL|P0_TRACE_COMMIT_OK,
        .io_flags=P0_TRACE_IO_COHERENT};
    p0_trace_init(&t);
    assert(sizeof(t) <= 4500 && !p0_trace_start(&t,0));
    assert(!p0_trace_select(&t,4) && p0_trace_select(&t,1));
    assert(!p0_trace_select(&t,0) && p0_trace_start(&t,UINT32_MAX-100));
    assert(!p0_trace_start(&t,0) && !p0_trace_stop(&(p0_trace_t){0},0));
    assert(!p0_trace_response(&t,P0_TRACE_SUMMARY,&packet));
    p0_trace_append(&t,&r);
    assert(p0_trace_stop(&t,UINT32_MAX-20) && !p0_trace_stop(&t,0));
    assert(p0_trace_response(&t,P0_TRACE_SUMMARY,&packet));
    assert(packet.type==P0_TRACE_DATA && packet.payload_length==36);
    assert(!p0_trace_response(&t,0,&packet));
    assert(!p0_trace_post_due(&t,UINT32_MAX-11));
    assert(p0_trace_post_due(&t,UINT32_MAX-10));
    assert(p0_trace_post_due(&t,0)); /* unsigned时间回绕 */
    assert(!p0_trace_post_due(&t,0));
    assert(!p0_trace_post_due(&t,479) && (t.flags & P0_TRACE_FROZEN));
    assert(p0_trace_response(&t,0,&packet));
    assert(packet.payload[0]==1 && packet.payload[1]==1);
    assert(p0_read_u16_le(packet.payload+4)==1);
    assert(p0_read_u32_le(packet.payload+12)==UINT32_MAX-1);
    assert(p0_read_i16_le(packet.payload+22)==8);
    assert(p0_read_u16_le(packet.payload+24)==3200);
    assert(p0_read_u32_le(packet.payload+28)==7);
    assert(packet.payload[32]==(P0_TRACE_CONTROL|P0_TRACE_COMMIT_OK));
    assert(!packet.payload[7] && !packet.payload[34] && !packet.payload[35]);
    assert(!p0_trace_response(&t,1,&packet));
    p0_trace_append(&t,&r); assert(t.count==1);
    p0_trace_init(&t); assert(p0_trace_select(&t,0) && p0_trace_start(&t,0));
    for (unsigned i=0;i<P0_TRACE_CAPACITY;++i) {
        r.tick_ms=i; p0_trace_append(&t,&r);
    }
    assert(t.count==P0_TRACE_CAPACITY && !(t.flags&P0_TRACE_OVERFLOW));
    r.tick_ms=999; p0_trace_append(&t,&r);
    assert((t.flags&(P0_TRACE_OVERFLOW|P0_TRACE_FROZEN))==(P0_TRACE_OVERFLOW|P0_TRACE_FROZEN));
    assert(t.records[0].tick_ms==0 && t.records[P0_TRACE_CAPACITY-1].tick_ms==159);
    assert(p0_trace_stop(&t,1000) && p0_trace_response(&t,P0_TRACE_SUMMARY,&packet));
    puts("Trace: fixed RAM, bounds, overflow without overwrite, wrap, freeze and wire layout PASS");
    return 0;
}
