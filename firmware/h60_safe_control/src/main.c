#include "p0_build_config.h"
#include "p0_usb_diag.h"
#include "p0_control.h"
#include "p0_hw.h"
#include "p0_iwdg_diagnostic.h"
#include "p0_m2a_calibration.h"
#include "p0_motion.h"
#include "p0_motion_scheduler.h"
#include "p0_protocol.h"
#if P0_USB_GUARDED_BUILD != 0
#include "p0_usb_quiet.h"
static p0_usb_quiet_t g_usb;
static void usb_stop(void)
{ p0_usb_quiet_stop(&g_usb); p0_hw_usb_tx_quiet(); p0_hw_motor_force_safe(0); }
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define P0_TELEMETRY_PERIOD_MS UINT32_C(100)

static p0_control_t g_control;
static p0_parser_t g_parser;
static uint32_t g_telemetry_sequence;
static uint32_t g_boot_fault_code;
#if P0_USB_LINK_RECOVERY_BUILD != 0
#include "p0_usb_link_recovery.h"
static volatile p0_usb_boot_retained_t g_boot_retained
    __attribute__((section(".noinit")));
static uint32_t g_boot_epoch;
static bool g_boot_prior_valid;
#endif
static p0_motion_controller_t g_motion;
static p0_motion_scheduler_t g_motion_scheduler;
static p0_m2a_calibration_t g_m2a_calibration;
#if P0_USB_MOTION_BUILD != 0
static p0_usb_motion_guard_t g_um_guard;
#if P0_USB_MANUAL_BUILD != 0
#include "p0_usb_manual.h"
static p0_usb_manual_t g_manual;
#endif
static p0_packet_t g_um_tx[4];
static uint8_t g_um_tx_read, g_um_tx_count;
#endif
#if P0_USB_MOTION_TRACE_BUILD != 0
static p0_trace_t g_trace;
static int16_t clamp_i16(int32_t value);
static void trace_record(uint8_t flags, uint32_t now_ms, const int32_t count[4])
{
    uint8_t i = g_trace.channel;
    p0_trace_record_t record = {0};
    p0_trace_io_t io;
    if (i >= 4 || !(g_trace.flags & P0_TRACE_STARTED) ||
        (g_trace.flags & P0_TRACE_FROZEN)) return;
    p0_hw_usb_motion_trace_snapshot(i, &io);
    record.tick_ms = now_ms;
    record.encoder_count = count[i];
    record.requested = clamp_i16(g_motion.requested_target_mm_s[i]);
    record.ramped = clamp_i16(g_motion.ramped_target_mm_s[i]);
    record.measured = clamp_i16(g_motion.measured_speed_mm_s[i]);
    record.output = g_motion.output_permille[i];
    record.ccr1 = io.ccr1;
    record.ccr2 = io.ccr2;
    record.generation = io.generation;
    record.flags = flags;
    record.io_flags = io.flags;
    if (record.requested != g_motion.requested_target_mm_s[i] ||
        record.ramped != g_motion.ramped_target_mm_s[i] ||
        record.measured != g_motion.measured_speed_mm_s[i])
        record.flags |= P0_TRACE_CLAMPED;
    p0_trace_append(&g_trace, &record);
}

static void trace_after_stop(void)
{
    uint32_t now = p0_hw_millis();
    if (p0_trace_stop(&g_trace, now)) {
        int32_t count[4];
        p0_hw_encoder_read(count);
        trace_record(P0_TRACE_STOP, now, count);
    }
}

static void trace_post_service(uint32_t now)
{
    if (g_control.state == P0_STATE_DISARMED && p0_trace_post_due(&g_trace, now)) {
        int32_t count[4];
        p0_hw_encoder_read(count);
        trace_record(P0_TRACE_POST, now, count);
    }
}
#endif
static bool g_motion_fault;
#if P0_IWDG_DIAGNOSTIC_BUILD != 0
static p0_iwdg_diagnostic_t g_iwdg_diagnostic;
#endif
#if P0_M2A_SLOWDRIVE_BUILD != 0
static p0_m2a_slowdrive_t g_slow;
static bool check_uart_rx_fault(void);

static bool slow_apply(p0_slow_action_t action)
{
    if (action == P0_SLOW_OFF || action == P0_SLOW_REJECT) {
        p0_hw_motor_force_safe(0);
        return action != P0_SLOW_REJECT;
    }
    if (action == P0_SLOW_NONE) return true;
    return p0_hw_slow_commit(&g_slow, action, g_control.last_heartbeat_ms);
}
#endif

static void motion_force_zero(void *unused)
{
    (void)unused;
#if P0_USB_MOTION_BUILD != 0
    p0_usb_motion_stop(&g_um_guard);
#endif
#if P0_M2A_SLOWDRIVE_BUILD != 0
    p0_hw_motor_force_safe(0);
    p0_slow_reset(&g_slow);
#endif
    p0_motion_reset(&g_motion);
    p0_motion_scheduler_reset(&g_motion_scheduler);
    p0_m2a_calibration_reset(&g_m2a_calibration);
    p0_hw_motor_force_safe(0);
#if P0_USB_MOTION_TRACE_BUILD != 0
    /* 先完成原安全撤输出，记录在后，不延迟STOP。 */
    trace_after_stop();
#endif
}

static bool motion_prepare_arm(void *unused, uint32_t now_ms)
{
    (void)unused;
#if P0_USB_MOTION_BUILD != 0
#if P0_USB_MOTION_TRACE_BUILD != 0
    if (g_trace.flags != P0_TRACE_SELECTED) return false;
#endif
    p0_hw_motor_force_safe(0);
#if P0_USB_MOTION_TRACE_BUILD != 0
    if (!p0_usb_motion_arm(&g_um_guard, now_ms, p0_hw_motor_stop_generation()) ||
        !p0_hw_usb_motion_begin(&g_um_guard)) return false;
    return p0_trace_start(&g_trace, now_ms);
#else
    return p0_usb_motion_arm(&g_um_guard, now_ms, p0_hw_motor_stop_generation()) &&
        p0_hw_usb_motion_begin(&g_um_guard);
#endif
#elif P0_M2A_SLOWDRIVE_BUILD != 0
    p0_slow_arm(&g_slow, now_ms, p0_hw_motor_stop_generation());
    return true;
#elif P0_M2A_RUNTIME_AVAILABLE
    return p0_m2a_calibration_arm(&g_m2a_calibration, now_ms);
#elif P0_MOTION_RUNTIME_AVAILABLE
    (void)now_ms;
    return true;
#else
    (void)now_ms;
    return false;
#endif
}

static bool motion_calibration_hold(
    void *unused,
    uint8_t channel,
    int8_t direction,
    uint16_t duty_permille,
    uint32_t now_ms)
{
    int16_t output_permille[4];

    (void)unused;
#if P0_M2A_SLOWDRIVE_BUILD != 0
    (void)output_permille;
    (void)now_ms;
    return slow_apply(p0_slow_hold(&g_slow, channel, direction, duty_permille,
        p0_hw_millis(), p0_hw_motor_stop_generation()));
#elif P0_M2A_RUNTIME_AVAILABLE
    if (!p0_m2a_calibration_hold(
            &g_m2a_calibration,
            channel,
            direction,
            duty_permille,
            now_ms,
            output_permille)) {
        p0_hw_motor_force_safe(0);
        return false;
    }
    if (direction == 0) {
        p0_hw_motor_force_safe(0);
    } else {
        p0_hw_motor_apply_pwm(0, output_permille);
    }
    return true;
#else
    (void)channel;
    (void)direction;
    (void)duty_permille;
    (void)now_ms;
    (void)output_permille;
    p0_hw_motor_force_safe(0);
    return false;
#endif
}

static bool motion_set_targets(void *unused, const int16_t target[4])
{
    (void)unused;
#if P0_USB_MOTION_TRACE_BUILD != 0
    if (target == NULL || g_trace.channel >= 4 || !(g_trace.flags & P0_TRACE_STARTED)) return false;
    for (unsigned i = 0; i < 4; ++i) {
        if ((i != g_trace.channel && target[i] != 0) ||
            (i == g_trace.channel && (target[i] < 0 || target[i] > P0_UM_TARGET_LIMIT)))
            return false;
    }
#endif
    if (!p0_motion_set_targets(&g_motion, target)) {
        p0_hw_motor_force_safe(0);
        return false;
    }
#if P0_USB_MOTION_BUILD != 0
    g_um_guard.target_ms = p0_hw_millis();
#endif
    return true;
}

static bool motion_configure(void)
{
    p0_motion_config_t config = {0};

    config.control_period_ms = P0_MOTION_CONTROL_PERIOD_MS;
#if P0_USB_MOTION_BUILD != 0
    config = p0_usb_motion_config();
#endif
    return p0_motion_init(&g_motion, &config);
}

static void motion_service(uint32_t now_ms)
{
#if (P0_MOTION_OUTPUT_COMPILED != 0) && \
    (P0_M2A_CALIBRATION_BUILD == 0)
    int32_t encoder_count[4];
    int16_t output_permille[4];
    p0_motion_schedule_result_t schedule_result;

    if (g_control.state != P0_STATE_ARMED) {
        p0_motion_scheduler_reset(&g_motion_scheduler);
        return;
    }
    schedule_result = p0_motion_scheduler_poll(&g_motion_scheduler, now_ms);
    if (schedule_result == P0_MOTION_SCHEDULE_WAIT) {
        return;
    }
    if (schedule_result == P0_MOTION_SCHEDULE_LATE) {
        p0_control_local_fault(&g_control, P0_FAULT_LOCAL);
        return;
    }
    p0_hw_encoder_read(encoder_count);
    if (!p0_motion_step(&g_motion, encoder_count, output_permille)) {
        p0_control_local_fault(&g_control, P0_FAULT_LOCAL);
        return;
    }
    if (schedule_result == P0_MOTION_SCHEDULE_PRIME) {
#if P0_USB_MOTION_BUILD == 0
        p0_hw_motor_force_safe(0);
#endif
#if P0_USB_MOTION_TRACE_BUILD != 0
        trace_record(P0_TRACE_PRIME, now_ms, encoder_count);
#endif
        return;
    }
#if P0_USB_MOTION_BUILD != 0
#if P0_USB_MOTION_TRACE_BUILD != 0
    bool committed = p0_hw_usb_motion_commit(output_permille);
    if (!committed) {
        /* HAL拒绝返回前已撤输出；保留本次请求，再执行原故障状态转换。 */
        trace_record(P0_TRACE_CONTROL | P0_TRACE_COMMIT_FAILED, now_ms, encoder_count);
        p0_control_local_fault(&g_control, P0_FAULT_LOCAL);
    } else {
        trace_record(P0_TRACE_CONTROL | P0_TRACE_COMMIT_OK, now_ms, encoder_count);
    }
#else
    if (!p0_hw_usb_motion_commit(output_permille))
        p0_control_local_fault(&g_control, P0_FAULT_LOCAL);
#endif
#else
    p0_hw_motor_apply_pwm(0, output_permille);
#endif
#else
    (void)now_ms;
#endif
}

static void calibration_service(uint32_t now_ms)
{
#if P0_M2A_SLOWDRIVE_BUILD != 0
    /* 候选提交前先消费接收错误、核对通信期限和上层状态。 */
    if (check_uart_rx_fault()) return;
    now_ms = p0_hw_millis();
    p0_control_tick(&g_control, now_ms);
    if (g_control.state != P0_STATE_ARMED || !g_control.session_valid) return;
    if (!slow_apply(p0_slow_service(&g_slow, now_ms,
                                   p0_hw_motor_stop_generation()))) {
        g_motion_fault = true;
    }
#elif P0_M2A_RUNTIME_AVAILABLE
    int16_t output_permille[4];
    p0_m2a_service_result_t result = p0_m2a_calibration_service(
        &g_m2a_calibration,
        now_ms,
        output_permille);

    if (result != P0_M2A_SERVICE_OK) {
        p0_hw_motor_force_safe(0);
        g_motion_fault = true;
    }
#else
    (void)now_ms;
#endif
}

static void send_packet(const p0_packet_t *packet)
{
#if P0_USB_GUARDED_BUILD != 0
    if (g_usb.phase != P0_USB_ACTIVE || !p0_hw_usb_tx_active()) return;
#endif
#if P0_USB_MOTION_BUILD != 0
    if (g_um_tx_count == 4 || packet->payload_length > 40) {
        p0_control_local_fault(&g_control, P0_FAULT_LOCAL);
        usb_stop();
        g_um_tx_count = 0;
        return;
    }
    g_um_tx[(g_um_tx_read + g_um_tx_count) % 4] = *packet;
    ++g_um_tx_count;
    if (packet->type == P0_MSG_ACK || packet->type == P0_MSG_NACK)
        P0_DIAG(P0_DIAG_ACK_QUEUED | ((uint32_t)packet->type << 8) |
            ((uint32_t)packet->payload[1] << 16), packet->session_id, packet->sequence);
#else
    uint8_t frame[P0_PROTOCOL_MAX_FRAME];
    size_t length = p0_packet_encode(packet, frame, sizeof(frame));

    P0_HW_ASSERT(length != 0);
    p0_hw_uart_write(frame, length);
#endif
}

#if P0_USB_MOTION_BUILD != 0
static void usb_response_service(bool flush)
{
    do {
        uint8_t frame[P0_PROTOCOL_MAX_FRAME];
        if (!g_um_tx_count || !p0_hw_usb_tx_active()) return;
        if (g_control.state == P0_STATE_ARMED &&
            (!g_motion_scheduler.active ||
             (uint32_t)(p0_hw_millis() - g_motion_scheduler.last_step_ms) > 1))
            return;
        /* ACK/NACK为22字节、遥测58字节，115200bps最多约5.04ms。
           仅在本次控制步之后0-1ms开始一帧，不跨下一10ms控制期限。 */
        size_t length = p0_packet_encode(&g_um_tx[g_um_tx_read], frame, sizeof(frame));
        P0_HW_ASSERT(length != 0);
        p0_hw_uart_write(frame, length);
        g_um_tx_read = (uint8_t)((g_um_tx_read + 1) % 4);
        --g_um_tx_count;
    } while (flush);
}
#endif

static bool check_uart_rx_fault(void)
{
    if (!p0_hw_uart_take_rx_fault()) {
        return false;
    }
#if P0_USB_GUARDED_BUILD != 0
    usb_stop();
#endif
    p0_parser_init(&g_parser);
    p0_control_protocol_fault(&g_control);
    P0_DIAG(P0_DIAG_RX_FAULT, g_control.state, g_control.fault);
    return true;
}

static void service_safety(uint32_t now_ms)
{
    if (p0_hw_supervisor_tripped()) {
        p0_control_local_fault(&g_control, P0_FAULT_WATCHDOG_PRETRIP);
    }
#if P0_USB_MOTION_BUILD != 0
    if (g_control.state == P0_STATE_ARMED &&
        (!p0_hw_usb_tx_active() ||
         !p0_usb_motion_fresh(&g_um_guard, now_ms, p0_hw_motor_stop_generation())))
        p0_control_local_fault(&g_control, P0_FAULT_TIMEOUT);
#endif
    calibration_service(now_ms);
    if (g_motion_fault) {
        g_motion_fault = false;
        p0_control_local_fault(&g_control, P0_FAULT_LOCAL);
    }
    p0_control_tick(&g_control, now_ms);
#if P0_USB_GUARDED_BUILD != 0
    p0_usb_quiet_tick(&g_usb, now_ms);
    if (g_usb.phase == P0_USB_CLOSED || g_control.state == P0_STATE_FAULT ||
        g_boot_fault_code != P0_HW_FAULT_NONE ||
        (g_usb.phase == P0_USB_ACTIVE && !p0_hw_usb_tx_active())) usb_stop();
#if P0_USB_RX_DIAG_BUILD != 0
    static uint32_t last_state = UINT32_MAX;
    uint32_t state = (uint32_t)g_usb.phase | ((uint32_t)g_control.state << 8) |
        ((uint32_t)g_control.fault << 16) | ((uint32_t)g_um_guard.spent << 24);
    if (state != last_state) {
        P0_DIAG(P0_DIAG_STATE, state, g_boot_fault_code);
        last_state = state;
    }
#endif
#endif
}

static void send_command_status(
    const p0_packet_t *command,
    p0_status_t status)
{
    p0_packet_t response = {0};

    response.type = (status == P0_STATUS_OK) ? P0_MSG_ACK : P0_MSG_NACK;
    response.payload_length = UINT16_C(4);
    response.session_id = command->session_id;
    response.sequence = command->sequence;
    response.payload[0] = command->type;
    response.payload[1] = (uint8_t)status;
    response.payload[2] = (uint8_t)g_control.state;
    response.payload[3] = (uint8_t)g_control.fault;
    send_packet(&response);
}

#if P0_USB_GUARDED_BUILD != 0
static void handle_usb_packet(const p0_packet_t *p, uint32_t now)
{
#if P0_USB_MOTION_BUILD != 0
    P0_DIAG(P0_DIAG_PACKET | ((uint32_t)p->type << 8) |
        ((uint32_t)g_usb.phase << 16) | ((uint32_t)g_control.state << 20) |
        ((uint32_t)g_control.fault << 24), p->session_id, p->sequence);
#if P0_USB_MANUAL_BUILD != 0
    p0_usb_action_t action = p0_usb_manual_accept(&g_manual, &g_usb, &g_um_guard, p, now,
        g_control.state == P0_STATE_DISARMED && g_control.fault == P0_FAULT_NONE);
#else
    p0_usb_action_t action = p0_usb_motion_accept(&g_usb, p, now);
#endif
    P0_DIAG(P0_DIAG_ACTION | ((uint32_t)action << 8) |
        ((uint32_t)g_usb.phase << 16) | ((uint32_t)g_control.state << 20) |
        ((uint32_t)g_control.fault << 24), p->session_id, p->sequence);
#else
    p0_usb_action_t action = p0_usb_quiet_accept(&g_usb, p, now);
#endif
    p0_status_t status = P0_STATUS_OK;
    if (action == P0_USB_IGNORE) {
#if P0_USB_MOTION_BUILD != 0
        if (g_usb.phase == P0_USB_CLOSED && g_control.state != P0_STATE_FAULT)
            p0_control_protocol_fault(&g_control);
#endif
        if (g_usb.phase == P0_USB_CLOSED) usb_stop();
        return;
    }
    if (action == P0_USB_OPEN) {
#if P0_USB_MANUAL_BUILD != 0
        /* PAUSED期间的旧心跳可能重新建立旧控制会话；新HELLO先保持失能并清除它。 */
        p0_packet_t stopped = {0};
        stopped.type = P0_MSG_STOP;
        status = p0_control_handle_packet(&g_control, &stopped, now);
        if (status != P0_STATUS_OK) { usb_stop(); return; }
#endif
        if (g_control.state != P0_STATE_DISARMED || !p0_hw_usb_tx_start(now)) {
            usb_stop(); return;
        }
    } else {
        p0_packet_t command = *p;
        if (action == P0_USB_CLOSE) command.type = P0_MSG_STOP;
#if P0_USB_MOTION_TRACE_BUILD != 0
        if (p->type == P0_TRACE_SELECT) {
            if (g_control.state != P0_STATE_DISARMED || g_um_guard.spent ||
                !p0_trace_select(&g_trace, p->payload[0])) status = P0_STATUS_BAD_STATE;
        } else if (p->type == P0_TRACE_READ) {
            p0_packet_t response = {0};
            if (g_control.state == P0_STATE_DISARMED && g_um_guard.spent &&
                p0_trace_response(&g_trace, p0_read_u16_le(p->payload), &response)) {
                response.session_id = p->session_id;
                response.sequence = p->sequence;
                send_packet(&response);
                return;
            }
            status = P0_STATUS_BAD_STATE;
        } else {
            status = p0_control_handle_packet(&g_control, &command, now);
        }
        if (status != P0_STATUS_OK) p0_control_protocol_fault(&g_control);
#else
        status = p0_control_handle_packet(&g_control, &command, now);
#endif
    }
    if (p->type == P0_MSG_HEARTBEAT && status == P0_STATUS_OK)
        p0_hw_usb_tx_lease(now);
    send_command_status(p, status);
#if P0_USB_LINK_RECOVERY_BUILD != 0
    if (action == P0_USB_OPEN && status == P0_STATUS_OK) {
        p0_packet_t report;
        uint32_t uid[3], reset_flags;
        uint8_t flags = g_boot_prior_valid ? P0_BOOT_PRIOR_VALID : 0;
        if (g_um_guard.spent) flags |= P0_BOOT_ARM_SPENT;
        if (p0_hw_usb_tx_active()) flags |= P0_BOOT_TX_ACTIVE;
        p0_hw_usb_boot_identity(uid, &reset_flags);
        p0_usb_boot_report(&report, p, (uint8_t)g_usb.phase,
            (uint8_t)g_control.state, (uint8_t)g_control.fault, flags,
            g_boot_epoch, now, reset_flags, uid);
        send_packet(&report);
    }
#endif
    /* Candidate HAL waits for the last stop bit before returning. */
#if P0_USB_MOTION_BUILD != 0
    if (action == P0_USB_CLOSE || status != P0_STATUS_OK)
        usb_response_service(true); /* STOP/拒绝已先撤输出，随后才排空/静默。 */
#endif
    if (action == P0_USB_CLOSE || status != P0_STATUS_OK) usb_stop();
}
#endif

static int16_t clamp_i16(int32_t value)
{
    if (value > INT16_MAX) {
        return INT16_MAX;
    }
    if (value < INT16_MIN) {
        return INT16_MIN;
    }
    return (int16_t)value;
}

static int32_t encoder_delta(uint8_t channel, int32_t now, int32_t before)
{
    if ((channel == UINT8_C(1)) || (channel == UINT8_C(3))) {
        return (int32_t)(int16_t)((uint16_t)now - (uint16_t)before);
    }
    return (int32_t)((uint32_t)now - (uint32_t)before);
}

static void send_telemetry(void)
{
    static int32_t previous_count[4];
    p0_packet_t packet = {0};
    int32_t count[4];
    uint16_t vin_raw = 0;
    uint16_t vin_nominal_mv = 0;
    uint8_t i;

    p0_hw_encoder_read(count);
    (void)p0_hw_vin_read(&vin_raw, &vin_nominal_mv);

    packet.type = P0_MSG_TELEMETRY;
    packet.payload_length = UINT16_C(40);
    packet.session_id = g_control.session_valid ? g_control.session_id : 0;
#if P0_USB_GUARDED_BUILD != 0
    packet.session_id = g_usb.session;
#endif
    packet.sequence = ++g_telemetry_sequence;
    packet.payload[0] = (uint8_t)g_control.state;
    packet.payload[1] = (uint8_t)g_control.fault;
    packet.payload[2] = g_control.motion_output_available ? UINT8_C(1) :
                                                            UINT8_C(0);
    packet.payload[3] = g_control.self_test_ok ? UINT8_C(1) : UINT8_C(0);

    for (i = 0; i < UINT8_C(4); ++i) {
        int32_t delta = encoder_delta(i, count[i], previous_count[i]);
        p0_write_u32_le(
            &packet.payload[4U + (size_t)i * 4U],
            (uint32_t)count[i]);
        p0_write_i16_le(
            &packet.payload[20U + (size_t)i * 2U],
            clamp_i16(delta));
        previous_count[i] = count[i];
    }

    p0_write_u16_le(&packet.payload[28], vin_raw);
    p0_write_u16_le(&packet.payload[30], vin_nominal_mv);
    packet.payload[32] = P0_FIRMWARE_VERSION_MAJOR;
    packet.payload[33] = P0_FIRMWARE_VERSION_MINOR;
    packet.payload[34] = P0_FIRMWARE_VERSION_PATCH;
    packet.payload[35] = P0_FIRMWARE_CAPABILITIES;
    p0_write_u32_le(&packet.payload[36], g_boot_fault_code);
    send_packet(&packet);
}

int main(void)
{
    p0_motor_ops_t motor_ops;
    uint32_t last_telemetry_ms;
    bool self_test_ok;
    uint16_t vin_raw;
    uint16_t vin_nominal_mv;
    bool motion_config_valid;

    p0_hw_early_safe_init();
    p0_hw_init();
#if P0_USB_GUARDED_BUILD != 0
    p0_usb_quiet_init(&g_usb);
#endif
    p0_parser_init(&g_parser);
#if P0_USB_MOTION_BUILD != 0
    p0_usb_motion_init(&g_um_guard);
#if P0_USB_MANUAL_BUILD != 0
    p0_usb_manual_init(&g_manual);
#endif
    g_um_tx_read = g_um_tx_count = 0;
#endif
#if P0_USB_MOTION_TRACE_BUILD != 0
    p0_trace_init(&g_trace);
#endif

    motion_config_valid = motion_configure();
    motor_ops.force_zero = motion_force_zero;
    motor_ops.prepare_arm = motion_prepare_arm;
    motor_ops.set_wheel_targets = motion_set_targets;
    motor_ops.calibration_hold = motion_calibration_hold;
    motor_ops.context = 0;
    p0_control_init(
        &g_control,
        motor_ops,
        ((P0_MOTION_RUNTIME_AVAILABLE && motion_config_valid) ||
         P0_M2A_RUNTIME_AVAILABLE ||
         (P0_USB_MOTION_BUILD && motion_config_valid)));

    g_boot_fault_code = p0_hw_take_retained_fault();
#if P0_USB_LINK_RECOVERY_BUILD != 0
    g_boot_epoch = p0_usb_boot_advance(&g_boot_retained, &g_boot_prior_valid);
#endif
    self_test_ok = p0_hw_vin_read(&vin_raw, &vin_nominal_mv);
    (void)vin_raw;
    (void)vin_nominal_mv;
    p0_control_finish_boot(&g_control, self_test_ok);
    if ((g_boot_fault_code != P0_HW_FAULT_NONE) &&
        (g_boot_fault_code != P0_HW_FAULT_IWDG_RESET)) {
        p0_control_local_fault(&g_control, P0_FAULT_LOCAL);
    }

    p0_hw_watchdog_start();
    P0_DIAG(P0_DIAG_MAIN_READY, g_boot_fault_code,
        ((uint32_t)g_control.state << 8) | (uint32_t)g_control.fault);
    last_telemetry_ms = p0_hw_millis();
#if P0_IWDG_DIAGNOSTIC_BUILD != 0
    p0_iwdg_diagnostic_init(
        &g_iwdg_diagnostic,
        g_boot_fault_code,
        last_telemetry_ms);
#endif

    for (;;) {
        uint8_t byte;
        uint8_t rx_budget = UINT8_C(64);
        uint32_t now_ms;

        p0_hw_main_alive();
        now_ms = p0_hw_millis();

        service_safety(now_ms);

        while (rx_budget != 0) {
            p0_packet_t packet;
            p0_parse_result_t result;

            if (check_uart_rx_fault() || !p0_hw_uart_read_byte(&byte)) {
                break;
            }
            result = p0_parser_feed(&g_parser, byte, &packet);
            --rx_budget;

            if (result == P0_PARSE_PACKET) {
                /* 缓冲命令也必须先执行当下的失联/租约/会话检查，
                   不能用一轮开始时的旧时间续租已经过期的输出。 */
                now_ms = p0_hw_millis();
                service_safety(now_ms);
                if (check_uart_rx_fault()) {
                    break;
                }
#if P0_USB_GUARDED_BUILD != 0
                handle_usb_packet(&packet, now_ms);
#else
                p0_status_t status = p0_control_handle_packet(
                    &g_control,
                    &packet,
                    now_ms);
                send_command_status(&packet, status);
#endif
            } else if (result < 0) {
#if P0_USB_GUARDED_BUILD != 0
                usb_stop();
#endif
                p0_control_protocol_fault(&g_control);
                P0_DIAG(P0_DIAG_PARSE_ERROR, (uint32_t)result, 0);
            }
        }

        (void)check_uart_rx_fault();
        now_ms = p0_hw_millis();
        service_safety(now_ms);
        motion_service(now_ms);
#if P0_USB_MOTION_TRACE_BUILD != 0
        trace_post_service(p0_hw_millis());
#endif
        if ((uint32_t)(now_ms - last_telemetry_ms) >=
            P0_TELEMETRY_PERIOD_MS) {
            last_telemetry_ms = now_ms;
            send_telemetry();
        }
#if P0_USB_MOTION_BUILD != 0
        usb_response_service(false);
#endif
#if P0_IWDG_DIAGNOSTIC_BUILD != 0
        if (p0_iwdg_diagnostic_should_stall(&g_iwdg_diagnostic, now_ms)) {
            p0_hw_iwdg_diagnostic_stall();
        }
        if (p0_iwdg_diagnostic_should_trigger_exception(
                &g_iwdg_diagnostic, now_ms)) {
            p0_hw_exception_diagnostic_trigger();
        }
#endif
        p0_hw_watchdog_feed();
    }
}
