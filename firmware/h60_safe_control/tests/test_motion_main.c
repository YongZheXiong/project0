/* 编译真实motion_service；硬件全部由主机替身提供，不连接USB设备。 */
#define main firmware_main
#include "../src/main.c"
#undef main

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static uint32_t fake_now_ms;
static int32_t fake_encoder_count[4];
static int16_t observed_pwm[4];
static unsigned force_safe_count;
static unsigned apply_count;

void p0_hw_early_safe_init(void) {}
void p0_hw_init(void) {}
void p0_hw_motor_force_safe(void *unused)
{
    (void)unused;
    memset(observed_pwm, 0, sizeof(observed_pwm));
    ++force_safe_count;
}
void p0_hw_motor_apply_pwm(void *unused, const int16_t output[4])
{
    (void)unused;
    memcpy(observed_pwm, output, sizeof(observed_pwm));
    ++apply_count;
}
uint32_t p0_hw_millis(void) { return fake_now_ms; }
void p0_hw_main_alive(void) {}
bool p0_hw_supervisor_tripped(void) { return false; }
bool p0_hw_uart_read_byte(uint8_t *byte) { (void)byte; return false; }
bool p0_hw_uart_take_rx_fault(void) { return false; }
void p0_hw_uart_write(const uint8_t *data, size_t length)
{ (void)data; (void)length; }
void p0_hw_encoder_read(int32_t count[4])
{ memcpy(count, fake_encoder_count, sizeof(fake_encoder_count)); }
bool p0_hw_vin_read(uint16_t *raw, uint16_t *nominal_mv)
{ *raw = 0; *nominal_mv = 0; return true; }
void p0_hw_watchdog_start(void) {}
void p0_hw_watchdog_feed(void) {}
uint32_t p0_hw_take_retained_fault(void) { return P0_HW_FAULT_NONE; }
void p0_hw_fault_trap(uint32_t code) { (void)code; abort(); }

static p0_motion_config_t synthetic_config(void)
{
    p0_motion_config_t config = {0};
    uint8_t i;

    config.control_period_ms = P0_MOTION_CONTROL_PERIOD_MS;
    config.maximum_target_mm_s = UINT16_C(200);
    config.acceleration_mm_s2 = UINT16_C(1000);
    config.deceleration_mm_s2 = UINT16_C(1000);
    config.reversal_zero_hold_ms = UINT16_C(20);
    config.zero_speed_threshold_mm_s = UINT16_C(20);
    config.maximum_output_permille = UINT16_C(300);
    config.kp_q10 = P0_MOTION_GAIN_SCALE;
    config.ki_q10_per_s = 0;
    for (i = 0; i < P0_MOTION_CHANNEL_COUNT; ++i) {
        config.encoder_counts_per_revolution[i] = UINT32_C(1000);
        config.maximum_encoder_delta_counts[i] = UINT32_C(100);
        config.wheel_circumference_mm[i] = UINT32_C(1000);
        config.encoder_counter_bits[i] = UINT8_C(32);
        config.encoder_polarity[i] = INT8_C(1);
    }
    return config;
}

static void test_late_service_forces_zero_and_faults_without_apply(void)
{
    p0_motion_config_t config = synthetic_config();
    p0_motor_ops_t operations = {
        motion_force_zero,
        motion_prepare_arm,
        motion_set_targets,
        motion_calibration_hold,
        0};
    int16_t target[4] = {100, 0, 0, 0};
    p0_packet_t stop = {0};
    unsigned applies_before_late;

    memset(&g_control, 0, sizeof(g_control));
    memset(&g_motion, 0, sizeof(g_motion));
    memset(&g_motion_scheduler, 0, sizeof(g_motion_scheduler));
    memset(fake_encoder_count, 0, sizeof(fake_encoder_count));
    memset(observed_pwm, 0, sizeof(observed_pwm));
    force_safe_count = 0;
    apply_count = 0;
    g_motion_fault = false;

    assert(p0_motion_init(&g_motion, &config));
    p0_control_init(&g_control, operations, true);
    p0_control_finish_boot(&g_control, true);
    g_control.state = P0_STATE_ARMED;
    g_control.session_valid = true;
    g_control.session_id = UINT32_C(7);
    assert(p0_motion_set_targets(&g_motion, target));

    motion_service(UINT32_C(100));
    assert(g_motion.encoder_ready);
    assert(apply_count == 0);
    assert(observed_pwm[0] == 0);

    motion_service(UINT32_C(109));
    assert(apply_count == 0);
    motion_service(UINT32_C(110));
    assert(apply_count == 1);
    assert(observed_pwm[0] > 0);

    applies_before_late = apply_count;
    motion_service(UINT32_C(121));
    assert(apply_count == applies_before_late);
    assert(force_safe_count > 0);
    assert(observed_pwm[0] == 0);
    assert(g_control.state == P0_STATE_FAULT);
    assert(g_control.fault == P0_FAULT_LOCAL);
    assert(!g_control.session_valid);
    assert(g_motion.requested_target_mm_s[0] == 0);
    assert(g_motion.output_permille[0] == 0);

    stop.type = P0_MSG_STOP;
    assert(p0_control_handle_packet(&g_control, &stop, UINT32_C(122)) ==
           P0_STATUS_OK);
    assert(g_control.state == P0_STATE_DISARMED);
    motion_service(UINT32_C(122));
    g_control.state = P0_STATE_ARMED;
    motion_service(UINT32_C(500));
    assert(g_control.state == P0_STATE_ARMED);
    assert(apply_count == applies_before_late);
}

int main(void)
{
    test_late_service_forces_zero_and_faults_without_apply();
    puts("PASS: actual motion_service exact-period and late-fault integration");
    return 0;
}
