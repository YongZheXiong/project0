/* 编译真实主循环；用定时字节流替代硬件，不连接USB设备。 */
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
static event_t events[512];
static size_t event_count, event_next;
static uint32_t clock_us;
static p0_uart_rx_t rx;
static jmp_buf finished;
static int mode;
static bool injected, tx_active, saw_rx_during_tx, saw_protocol_fault;
static unsigned applies, ack_count, nack_count;
static int16_t pwm[4];

static void advance(uint32_t us)
{
    uint32_t end = clock_us + us;
    while (event_next < event_count && events[event_next].us <= end) {
        p0_uart_rx_push_isr(&rx, events[event_next++].byte, false);
        if (tx_active) saw_rx_during_tx = true;
    }
    clock_us = end;
}

static uint32_t schedule(uint32_t us, uint8_t type, uint32_t seq)
{
    p0_packet_t command = {0};
    uint8_t frame[P0_PROTOCOL_MAX_FRAME];
    size_t i, length;
    command.type = type;
    command.session_id = type == P0_MSG_STOP ? 0 : 77;
    command.sequence = seq;
    if (type == P0_MSG_M2A_CALIBRATION_HOLD) {
        command.payload_length = 4;
        command.payload[0] = 1;
        command.payload[1] = 1;
        command.payload[2] = 50;
    }
    length = p0_packet_encode(&command, frame, sizeof(frame));
    for (i = 0; i < length; ++i) {
        assert(event_count < sizeof(events) / sizeof(events[0]));
        events[event_count++] = (event_t){us, frame[i]};
        us += 87; /* 115200/8N1约87微秒一个字节 */
    }
    return us;
}

void p0_hw_early_safe_init(void) {}
void p0_hw_init(void) { p0_uart_rx_init(&rx); }
void p0_hw_motor_force_safe(void *unused)
{ (void)unused; memset(pwm, 0, sizeof(pwm)); }
void p0_hw_motor_apply_pwm(void *unused, const int16_t output[4])
{ (void)unused; memcpy(pwm, output, sizeof(pwm)); ++applies; }
uint32_t p0_hw_millis(void) { return clock_us / 1000; }
void p0_hw_main_alive(void) { advance(100); }
bool p0_hw_supervisor_tripped(void) { return false; }
bool p0_hw_uart_read_byte(uint8_t *byte) { return p0_uart_rx_pop(&rx, byte); }
bool p0_hw_uart_take_rx_fault(void) { return p0_uart_rx_take_fault(&rx); }
void p0_hw_encoder_read(int32_t count[4]) { memset(count, 0, 4 * sizeof(*count)); }
bool p0_hw_vin_read(uint16_t *raw, uint16_t *mv)
{ *raw = 1338; *mv = 11861; return true; }
void p0_hw_watchdog_start(void) {}
uint32_t p0_hw_take_retained_fault(void) { return 0; }
void p0_hw_fault_trap(uint32_t code) { (void)code; abort(); }
void p0_hw_watchdog_feed(void)
{
    if (g_control.fault == P0_FAULT_PROTOCOL) saw_protocol_fault = true;
    if (clock_us >= 300000) longjmp(finished, 1);
}

void p0_hw_uart_write(const uint8_t *data, size_t length)
{
    p0_parser_t parser;
    p0_packet_t packet = {0};
    size_t i;
    p0_parser_init(&parser);
    for (i = 0; i < length; ++i) {
        (void)p0_parser_feed(&parser, data[i], &packet);
    }
    if (packet.type == P0_MSG_ACK) ++ack_count;
    if (packet.type == P0_MSG_NACK) ++nack_count;
    if (!injected && packet.type == P0_MSG_ACK && packet.sequence == 4) {
        injected = true;
        if (mode == 1) {
            for (i = 0; i < P0_UART_RX_CAPACITY; ++i)
                p0_uart_rx_push_isr(&rx, (uint8_t)i, false);
        } else if (mode == 2) {
            p0_uart_rx_push_isr(&rx, 0, true);
        } else if (mode == 3) {
            /* TX返回前已过75ms租约；缓冲的新HOLD不得抢先续租。 */
            advance(80000);
        }
    }
    tx_active = true;
    advance((uint32_t)length * 87);
    tx_active = false;
}

static void run_case(int case_mode)
{
    uint32_t next;
    mode = case_mode;
    clock_us = 0;
    event_count = event_next = 0;
    injected = tx_active = saw_rx_during_tx = saw_protocol_fault = false;
    applies = ack_count = nack_count = 0;
    memset(&g_control, 0, sizeof(g_control));
    memset(&g_motion, 0, sizeof(g_motion));
    memset(&g_m2a_calibration, 0, sizeof(g_m2a_calibration));
    g_motion_fault = false;
    g_telemetry_sequence = 0;
    schedule(10000, P0_MSG_HEARTBEAT, 1);
    schedule(20000, P0_MSG_ARM, 2);
    next = schedule(130000, P0_MSG_HEARTBEAT, 3);
    schedule(next, P0_MSG_M2A_CALIBRATION_HOLD, 4);
    schedule(160000, P0_MSG_M2A_CALIBRATION_HOLD, 5);
    schedule(180000, P0_MSG_M2A_CALIBRATION_HOLD, 6);
    schedule(201000, P0_MSG_HEARTBEAT, 7);
    schedule(230000, P0_MSG_STOP, 8);
    if (!setjmp(finished)) (void)firmware_main();
    assert(event_next == event_count);
    assert(saw_rx_during_tx);
    assert(g_control.state == P0_STATE_DISARMED);
    assert(g_control.session_id == 0);
    for (size_t i = 0; i < 4; ++i) assert(pwm[i] == 0);
    if (mode == 0) {
        assert(applies == 3 && ack_count == 8 && nack_count == 0);
        assert(!saw_protocol_fault);
    } else {
        assert(applies == 1 && nack_count > 0);
        if (mode != 3) assert(saw_protocol_fault);
    }
}

int main(void)
{
    for (int i = 0; i < 4; ++i) run_case(i);
    /* 接收错误必须清除半帧，不能拼上后来的命令尾部。 */
    p0_parser_init(&g_parser);
    p0_packet_t packet;
    (void)p0_parser_feed(&g_parser, P0_PROTOCOL_SOF0, &packet);
    (void)p0_parser_feed(&g_parser, P0_PROTOCOL_SOF1, &packet);
    assert(g_parser.count == 2);
    p0_uart_rx_push_isr(&rx, 0, true);
    assert(check_uart_rx_fault());
    assert(g_parser.count == 0);
    assert(g_control.state == P0_STATE_FAULT);
    assert(g_control.fault == P0_FAULT_PROTOCOL);
    puts("PASS: actual main loop TX overlap, RX faults, STOP and expired lease");
    return 0;
}
