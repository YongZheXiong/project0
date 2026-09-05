/* 直接执行真实主循环的回调、协议分派和安全服务。 */
#define main firmware_main
#include "../src/main.c"
#undef main
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static uint32_t now, gen;
static bool trip, rx_fault, race;
static unsigned wake_count, run_count;
static int output;
void p0_hw_motor_force_safe(void *p) { (void)p; output = 0; ++gen; }
uint32_t p0_hw_motor_stop_generation(void) { return gen; }
bool p0_hw_slow_commit(p0_m2a_slowdrive_t *s, p0_slow_action_t a, uint32_t hb)
{
    if (race) { p0_hw_motor_force_safe(0); trip = true; }
    if (trip || rx_fault || !p0_slow_fresh(s, now, gen) || now-hb > 250) {
        p0_hw_motor_force_safe(0); return false;
    }
    if (a == P0_SLOW_WAKE) { output = 11; ++wake_count; s->wake_at_ms = now; }
    else { assert(a == P0_SLOW_RUN); output = 5; ++run_count; }
    return true;
}
void p0_hw_motor_apply_pwm(void *p, const int16_t v[4]) { (void)p; (void)v; abort(); }
uint32_t p0_hw_millis(void) { return now; }
bool p0_hw_supervisor_tripped(void) { return trip; }
bool p0_hw_uart_take_rx_fault(void) { bool f = rx_fault; rx_fault = false; return f; }
void p0_hw_early_safe_init(void) {}
void p0_hw_init(void) {}
void p0_hw_main_alive(void) {}
bool p0_hw_uart_read_byte(uint8_t *b) { (void)b; return false; }
void p0_hw_uart_write(const uint8_t *d, size_t n) { (void)d; (void)n; }
void p0_hw_encoder_read(int32_t v[4]) { memset(v, 0, 4*sizeof(*v)); }
bool p0_hw_vin_read(uint16_t *r, uint16_t *v) { *r=1; *v=12000; return true; }
void p0_hw_watchdog_start(void) {}
void p0_hw_watchdog_feed(void) {}
uint32_t p0_hw_take_retained_fault(void) { return 0; }
void p0_hw_fault_trap(uint32_t c) { (void)c; abort(); }

static p0_packet_t packet(uint8_t type, uint32_t seq)
{
    p0_packet_t p = {0}; p.type=type; p.session_id=77; p.sequence=seq;
    if (type == P0_MSG_M2A_CALIBRATION_HOLD) {
        p.payload_length=4; p.payload[0]=1; p.payload[1]=1; p.payload[2]=50;
    }
    return p;
}
static p0_status_t send(p0_packet_t p)
{
    service_safety(now);
    return p0_control_handle_packet(&g_control, &p, now);
}
static void setup(void)
{
    now=0; trip=rx_fault=race=false; wake_count=run_count=0;
    g_motion_fault=false;
    (void)motion_configure(); /* 闭环标定门保持无效；本测试使用独立校准模式。 */
    p0_motor_ops_t ops = {motion_force_zero, motion_prepare_arm,
                         motion_set_targets, motion_calibration_hold, 0};
    p0_control_init(&g_control, ops, true);
    p0_control_finish_boot(&g_control, true);
    assert(send(packet(P0_MSG_HEARTBEAT,1)) == P0_STATUS_OK);
    assert(send(packet(P0_MSG_ARM,2)) == P0_STATUS_OK);
    assert(output==0);
    now=1;
    assert(send(packet(P0_MSG_M2A_CALIBRATION_HOLD,3)) == P0_STATUS_OK);
    assert(output==11 && wake_count==1);
}
int main(void)
{
    unsigned count=0;
    for (unsigned phase=0;phase<4;++phase) {
        for (unsigned fault=0;fault<11;++fault) {
            setup(); now=1+phase; service_safety(now);
            if (phase<3) assert(run_count==0);
            else assert(run_count==1);
            p0_packet_t p=packet(P0_MSG_M2A_CALIBRATION_HOLD,4);
            switch (fault) {
            case 0: p=packet(P0_MSG_STOP,4); (void)send(p); break;
            case 1: p=packet(P0_MSG_DISARM,4); (void)send(p); break;
            case 2: p.payload[1]=p.payload[2]=0; (void)send(p); break;
            case 3: now=77; (void)send(p); break;
            case 4: now=1001; (void)send(p); break;
            case 5: p.sequence=3; (void)send(p); break;
            case 6: p.session_id=88; (void)send(p); break;
            case 7: rx_fault=true; service_safety(now); break;
            case 8: p0_hw_motor_force_safe(0); trip=true; service_safety(now); break;
            case 9: p0_control_protocol_fault(&g_control); break;
            case 10: now=251; service_safety(now); break;
            }
            assert(output==0);
            unsigned runs=run_count, wakes=wake_count;
            now+=5; service_safety(now);
            (void)send(packet(P0_MSG_M2A_CALIBRATION_HOLD,9));
            service_safety(now);
            assert(output==0 && run_count==runs && wake_count==wakes);
            ++count;
        }
    }
    setup(); race=true; now=4; service_safety(now);
    assert(output==0 && run_count==0 && g_control.state==P0_STATE_FAULT);
    printf("PASS: actual main/protocol %u cancel cases and precommit interrupt\n",count);
    /* STOP后新会话必须重新唤醒；不依赖重启/遗留占空比，旧会话不自恢复。 */
    setup(); now=4; service_safety(now);
    for (unsigned cycle=0;cycle<3;++cycle) {
        assert(output==5 && run_count==cycle+1 && wake_count==cycle+1);
        assert(send(packet(P0_MSG_STOP,0))==P0_STATUS_OK);
        assert(output==0 && !g_slow.armed && g_control.state==P0_STATE_DISARMED);
        now+=470000;
        service_safety(now); assert(output==0);
        p0_packet_t p=packet(P0_MSG_HEARTBEAT,1); p.session_id=100+cycle;
        assert(send(p)==P0_STATUS_OK);
        p.type=P0_MSG_ARM; p.sequence=2; assert(send(p)==P0_STATUS_OK);
        assert(output==0 && g_slow.phase==P0_SLOW_IDLE);
        p=packet(P0_MSG_M2A_CALIBRATION_HOLD,3); p.session_id=100+cycle;
        assert(send(p)==P0_STATUS_OK); assert(output==11);
        now+=2; service_safety(now); assert(output==11);
        ++now; service_safety(now); assert(output==5);
    }
    assert(send(packet(P0_MSG_STOP,0))==P0_STATUS_OK);
    assert(output==0);
    puts("PASS: 3 STOP/new-session restart cycles through actual protocol/main callbacks");
}
