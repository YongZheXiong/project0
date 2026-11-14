/* Actual main/protocol/controller. Only clock, UART and hardware are replaced. */
#define main firmware_main
#include "../src/main.c"
#undef main
#include "p0_uart_rx.h"
#include <assert.h>
#include <setjmp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct { uint32_t us; uint8_t byte; } event_t;
static event_t events[8192];
static size_t count, next;
static uint32_t now_us, generation, wake_ms;
static p0_uart_rx_t rx;
static jmp_buf done;
static int scenario;
static bool enabled, latched, waking, interactive;
static unsigned nonzero_applies, writes;
static uint32_t last_nonzero_ms, boundary_us;
static int16_t current[4];
static bool late_injected;

static void advance(uint32_t us)
{
    uint32_t end = now_us + us;
    while (next < count && events[next].us <= end)
        p0_uart_rx_push_isr(&rx, events[next++].byte, false);
    now_us = end;
}
static void wire(uint32_t ms, const uint8_t *bytes, size_t length)
{
    for (size_t i = 0; i < length; ++i) {
        assert(count < sizeof(events) / sizeof(events[0]));
        events[count++] = (event_t){ms * 1000 + (uint32_t)i * 87, bytes[i]};
    }
}
static void schedule(uint32_t ms, uint8_t type, uint32_t sequence, int target)
{
    p0_packet_t p = {0};
    uint8_t bytes[P0_PROTOCOL_MAX_FRAME];
    p.type = type; p.session_id = 77; p.sequence = sequence;
    if (type == P0_USB_HELLO) {p.payload_length = 5; memcpy(p.payload, "P0UM1", 5);}
    if (type == P0_MSG_WHEEL_TARGET) {
        p.payload_length = 8;
        for (size_t i = 0; i < 4; ++i) p0_write_i16_le(p.payload + 2*i, (int16_t)target);
    }
    if (scenario == 7 && ms == 180) p.session_id = 88;
    if (scenario == 8 && ms == 180) p.sequence = 4;
    size_t n = p0_packet_encode(&p, bytes, sizeof(bytes));
    if (scenario == 6 && ms == 180) bytes[n-1] ^= 1;
    wire(ms, bytes, n);
}
void p0_hw_early_safe_init(void) {}
void p0_hw_init(void) {p0_uart_rx_init(&rx); enabled = latched = waking = false; generation = 0;}
void p0_hw_motor_force_safe(void *c) {(void)c; memset(current, 0, sizeof(current)); ++generation; waking = false;}
void p0_hw_motor_apply_pwm(void *c, const int16_t p[4]) {(void)c; (void)p; abort();}
uint32_t p0_hw_motor_stop_generation(void) {return generation;}
bool p0_hw_usb_motion_begin(p0_usb_motion_guard_t *g)
{return enabled && !latched && p0_usb_motion_fresh(g, now_us/1000, generation);}
bool p0_hw_usb_motion_commit(const int16_t output[4])
{
    assert(enabled && !latched && p0_usb_motion_fresh(&g_um_guard, now_us/1000, generation));
    bool nonzero = false;
    for (unsigned i = 0; i < 4; ++i) {assert(abs(output[i]) <= 80); if (output[i]) nonzero = true;}
    if (nonzero && !waking) {waking = true; wake_ms = now_us/1000; return true;}
    if (waking && now_us/1000 - wake_ms < 3) return true;
    memcpy(current, output, sizeof(current));
    if (nonzero) {++nonzero_applies; last_nonzero_ms = now_us/1000;}
    return true;
}
uint32_t p0_hw_millis(void) {return now_us/1000;}
void p0_hw_main_alive(void)
{
    if (interactive && now_us >= boundary_us) {
        char line[1024], hex[512] = "";
        unsigned ms;
        printf("READY %u\n", now_us/1000); fflush(stdout);
        if (!fgets(line, sizeof(line), stdin)) longjmp(done, 1);
        assert(sscanf(line, "%u %511s", &ms, hex) >= 1 && ms*1000 >= now_us);
        if (strcmp(hex, "-")) {
            uint8_t bytes[128]; size_t n = strlen(hex)/2;
            assert(n <= sizeof(bytes) && strlen(hex)%2 == 0);
            for (size_t i = 0; i < n; ++i) {unsigned byte; assert(sscanf(hex+2*i, "%2x", &byte) == 1); bytes[i]=(uint8_t)byte;}
            wire(ms, bytes, n);
        }
        boundary_us = (ms + 15)*1000;
    }
    if (scenario == 11 && now_us >= 180000 && !late_injected) {late_injected=true; advance(11000);}
    advance(100);
}
bool p0_hw_supervisor_tripped(void) {return scenario == 14 && now_us >= 180000;}
bool p0_hw_uart_read_byte(uint8_t *b) {return p0_uart_rx_pop(&rx, b);}
bool p0_hw_uart_take_rx_fault(void) {return (scenario == 13 && now_us >= 180000) || p0_uart_rx_take_fault(&rx);}
void p0_hw_encoder_read(int32_t c[4])
{for (unsigned i=0; i<4; ++i) c[i] = scenario == 10 && now_us >= 180000 ? 13 : 0;}
bool p0_hw_vin_read(uint16_t *r, uint16_t *v) {*r=1353; *v=11994; return scenario != 15;}
void p0_hw_watchdog_start(void) {}
void p0_hw_watchdog_feed(void) {if (!interactive && now_us >= 1600000) longjmp(done, 1);}
uint32_t p0_hw_take_retained_fault(void) {return scenario == 12 ? P0_HW_FAULT_IWDG_RESET : 0;}
void p0_hw_fault_trap(uint32_t c) {(void)c; abort();}
void p0_hw_usb_tx_lease(uint32_t ms) {(void)ms;}
bool p0_hw_usb_tx_start(uint32_t ms) {(void)ms; if (latched) return false; enabled=true; return true;}
void p0_hw_usb_tx_quiet(void) {enabled=false; latched=true; p0_hw_motor_force_safe(0);}
bool p0_hw_usb_tx_active(void) {return enabled && !latched;}
void p0_hw_uart_write(const uint8_t *data, size_t n)
{
    assert(enabled && !latched); ++writes;
    if (interactive) {
        printf("WIRE %u ", now_us/1000);
        for (size_t i=0; i<n; ++i) printf("%02x", data[i]);
        puts(""); fflush(stdout);
    }
    advance((uint32_t)n*87);
}
static int event_compare(const void *a, const void *b)
{const event_t *x=a,*y=b; return x->us > y->us ? 1 : (x->us < y->us ? -1 : 0);}
static void run(int which)
{
    scenario=which; count=next=0; now_us=0; nonzero_applies=writes=0; last_nonzero_ms=0;
    late_injected=false;
    memset(&g_control, 0, sizeof(g_control)); g_motion_fault=false; g_telemetry_sequence=0;
    p0_usb_motion_init(&g_um_guard);
    uint32_t seq=1;
    if (which != 0) {
        schedule(5, P0_USB_HELLO, seq++, 0);
        schedule(30, P0_MSG_HEARTBEAT, seq++, 0);
        schedule(120, P0_MSG_ARM, seq++, 0);
        for (uint32_t t=140; t<=1200; t+=20) {
            if (which == 1 && t > 500) break;
            if (which == 3 && t > 140) continue;
            if (which == 5 && t >= 220) break;
            schedule(t, P0_MSG_WHEEL_TARGET, seq++, which == 9 && t == 180 ? 21 : 20);
            if (t%100 == 40 && which != 2) schedule(t+8, P0_MSG_HEARTBEAT, seq++, 0);
        }
        if (which == 3) {schedule(180,P0_MSG_HEARTBEAT,seq++,0);schedule(230,P0_MSG_HEARTBEAT,seq++,0);}
        if (which == 5) {
            schedule(220,P0_MSG_STOP,seq++,0); schedule(240,P0_MSG_HEARTBEAT,seq++,0);
            schedule(260,P0_MSG_ARM,seq++,0); schedule(280,P0_MSG_WHEEL_TARGET,seq++,20);
        }
        if (which == 1) {
            schedule(510,P0_MSG_STOP,seq++,0);schedule(550,P0_MSG_DISARM,seq++,0);
            schedule(580,P0_USB_QUIET,seq++,0);
        }
    }
    qsort(events,count,sizeof(events[0]),event_compare);
    if (setjmp(done)==0) firmware_main();
    for (unsigned i=0;i<4;++i) assert(current[i]==0);
    assert(g_control.state != P0_STATE_ARMED);
    if (which == 0) {assert(writes==0 && nonzero_applies==0 && !g_um_guard.spent); return;}
    if (which == 12 || which == 15) {assert(writes==0 && nonzero_applies==0); return;}
    if (!(nonzero_applies > 0 && latched))
        fprintf(stderr,"scenario=%d applies=%u state=%d fault=%d last=%u\n",which,nonzero_applies,g_control.state,g_control.fault,last_nonzero_ms);
    assert(nonzero_applies > 0 && latched);
    if (which == 2) assert(last_nonzero_ms < 281);
    if (which == 3) assert(last_nonzero_ms < 220);
    if (which == 5) assert(last_nonzero_ms < 223); /* STOP最后字节约221.5ms */
    if (which >= 6 && which <= 14) assert(last_nonzero_ms < 200);
    if (which == 1) assert(last_nonzero_ms < 513 && g_control.fault==P0_FAULT_NONE);
    if (which == 4) assert(last_nonzero_ms < 1123);
}
static void boundaries(void)
{
    p0_usb_motion_guard_t g;
    p0_usb_motion_init(&g); assert(p0_usb_motion_arm(&g,UINT32_MAX-30,7));
    assert(p0_usb_motion_fresh(&g,43,7)); assert(!p0_usb_motion_fresh(&g,44,7));
    assert(!p0_usb_motion_fresh(&g,0,8)); p0_usb_motion_stop(&g);
    assert(!p0_usb_motion_arm(&g,0,7));
}
int main(int argc, char **argv)
{
    if (argc==2 && !strcmp(argv[1],"--interactive")) {
        interactive=true; scenario=99; boundary_us=0;
        if (setjmp(done)==0) firmware_main();
        return 0;
    }
    for (int i=0;i<16;++i) run(i);
    boundaries(); puts("USB motion: 16 actual-main scenarios and wrap/one-arm boundaries PASS"); return 0;
}
