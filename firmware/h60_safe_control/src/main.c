#include "p0_build_config.h"
#include "p0_control.h"
#include "p0_hw.h"
#include "p0_protocol.h"

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define P0_TELEMETRY_PERIOD_MS UINT32_C(100)

static p0_control_t g_control;
static p0_parser_t g_parser;
static uint32_t g_telemetry_sequence;
static uint32_t g_boot_fault_code;

static void send_packet(const p0_packet_t *packet)
{
    uint8_t frame[P0_PROTOCOL_MAX_FRAME];
    size_t length = p0_packet_encode(packet, frame, sizeof(frame));

    P0_HW_ASSERT(length != 0);
    p0_hw_uart_write(frame, length);
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
    packet.payload[35] = 0;
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

    p0_hw_early_safe_init();
    p0_hw_init();
    p0_parser_init(&g_parser);

    motor_ops.force_zero = p0_hw_motor_force_safe;
    motor_ops.apply_wheel_targets = p0_hw_motor_apply_targets;
    motor_ops.context = 0;
    p0_control_init(
        &g_control,
        motor_ops,
        (P0_MOTION_OUTPUT_COMPILED != 0));

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

        if (p0_hw_supervisor_tripped()) {
            p0_control_local_fault(
                &g_control,
                P0_FAULT_WATCHDOG_PRETRIP);
        }

        while ((rx_budget != 0) && p0_hw_uart_read_byte(&byte)) {
            p0_packet_t packet;
            p0_parse_result_t result = p0_parser_feed(
                &g_parser,
                byte,
                &packet);
            --rx_budget;

            if (result == P0_PARSE_PACKET) {
                p0_status_t status = p0_control_handle_packet(
                    &g_control,
                    &packet,
                    now_ms);
                send_command_status(&packet, status);
            } else if (result < 0) {
                p0_control_protocol_fault(&g_control);
            }
        }

        p0_control_tick(&g_control, now_ms);
        if ((uint32_t)(now_ms - last_telemetry_ms) >=
            P0_TELEMETRY_PERIOD_MS) {
            last_telemetry_ms = now_ms;
            send_telemetry();
        }
        p0_hw_watchdog_feed();
    }
}
