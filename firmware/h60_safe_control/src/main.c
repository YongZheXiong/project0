#include "p0_build_config.h"
#include "p0_control.h"
#include "p0_hw.h"
#include "p0_m2a_calibration.h"
#include "p0_motion.h"
#include "p0_protocol.h"

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define P0_TELEMETRY_PERIOD_MS UINT32_C(100)

static p0_control_t g_control;
static p0_parser_t g_parser;
static uint32_t g_telemetry_sequence;
static uint32_t g_boot_fault_code;
static p0_motion_controller_t g_motion;
static p0_m2a_calibration_t g_m2a_calibration;
static bool g_motion_fault;
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
#if P0_M2A_SLOWDRIVE_BUILD != 0
    p0_hw_motor_force_safe(0);
    p0_slow_reset(&g_slow);
#endif
    p0_motion_reset(&g_motion);
    p0_m2a_calibration_reset(&g_m2a_calibration);
    p0_hw_motor_force_safe(0);
}

static bool motion_prepare_arm(void *unused, uint32_t now_ms)
{
    (void)unused;
#if P0_M2A_SLOWDRIVE_BUILD != 0
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
    if (!p0_motion_set_targets(&g_motion, target)) {
        p0_hw_motor_force_safe(0);
        return false;
    }
    return true;
}

static bool motion_configure(void)
{
    p0_motion_config_t config = {0};

    config.control_period_ms = P0_MOTION_CONTROL_PERIOD_MS;
    return p0_motion_init(&g_motion, &config);
}

static void motion_service(uint32_t now_ms)
{
#if (P0_MOTION_OUTPUT_COMPILED != 0) && \
    (P0_M2A_CALIBRATION_BUILD == 0)
    static uint32_t last_motion_ms;
    int32_t encoder_count[4];
    int16_t output_permille[4];

    if (g_control.state != P0_STATE_ARMED) {
        return;
    }
    if ((uint32_t)(now_ms - last_motion_ms) <
        P0_MOTION_CONTROL_PERIOD_MS) {
        return;
    }
    last_motion_ms = now_ms;
    p0_hw_encoder_read(encoder_count);
    if (!p0_motion_step(&g_motion, encoder_count, output_permille)) {
        p0_hw_motor_force_safe(0);
        g_motion_fault = true;
        return;
    }
    p0_hw_motor_apply_pwm(0, output_permille);
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
    uint8_t frame[P0_PROTOCOL_MAX_FRAME];
    size_t length = p0_packet_encode(packet, frame, sizeof(frame));

    P0_HW_ASSERT(length != 0);
    p0_hw_uart_write(frame, length);
}

static bool check_uart_rx_fault(void)
{
    if (!p0_hw_uart_take_rx_fault()) {
        return false;
    }
    p0_parser_init(&g_parser);
    p0_control_protocol_fault(&g_control);
    return true;
}

static void service_safety(uint32_t now_ms)
{
    if (p0_hw_supervisor_tripped()) {
        p0_control_local_fault(&g_control, P0_FAULT_WATCHDOG_PRETRIP);
    }
    calibration_service(now_ms);
    if (g_motion_fault) {
        g_motion_fault = false;
        p0_control_local_fault(&g_control, P0_FAULT_LOCAL);
    }
    p0_control_tick(&g_control, now_ms);
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
    p0_parser_init(&g_parser);

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
         P0_M2A_RUNTIME_AVAILABLE));

    g_boot_fault_code = p0_hw_take_retained_fault();
    self_test_ok = p0_hw_vin_read(&vin_raw, &vin_nominal_mv);
    (void)vin_raw;
    (void)vin_nominal_mv;
    p0_control_finish_boot(&g_control, self_test_ok);
    if (g_boot_fault_code != P0_HW_FAULT_NONE) {
        p0_control_local_fault(&g_control, P0_FAULT_LOCAL);
    }

    p0_hw_watchdog_start();
    last_telemetry_ms = p0_hw_millis();

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
                p0_status_t status = p0_control_handle_packet(
                    &g_control,
                    &packet,
                    now_ms);
                send_command_status(&packet, status);
            } else if (result < 0) {
                p0_control_protocol_fault(&g_control);
            }
        }

        (void)check_uart_rx_fault();
        now_ms = p0_hw_millis();
        service_safety(now_ms);
        motion_service(now_ms);
        if ((uint32_t)(now_ms - last_telemetry_ms) >=
            P0_TELEMETRY_PERIOD_MS) {
            last_telemetry_ms = now_ms;
            send_telemetry();
        }
        p0_hw_watchdog_feed();
    }
}
