#include "p0_control.h"
#include "p0_crc32.h"
#include "p0_protocol.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHECK(condition)                                                       \
    do {                                                                       \
        if (!(condition)) {                                                    \
            fprintf(stderr, "FAIL %s:%d: %s\n", __FILE__, __LINE__,          \
                    #condition);                                               \
            exit(EXIT_FAILURE);                                                \
        }                                                                      \
    } while (0)

typedef struct {
    unsigned int zero_calls;
    unsigned int apply_calls;
    unsigned int prepare_calls;
    unsigned int calibration_calls;
    p0_control_t *control;
    p0_state_t state_seen_on_zero;
    int16_t last_target[4];
} motor_stub_t;

static p0_packet_t make_command(
    uint8_t type,
    uint32_t session,
    uint32_t sequence);

static void stub_zero(void *context)
{
    motor_stub_t *stub = (motor_stub_t *)context;
    ++stub->zero_calls;
    if (stub->control != NULL) {
        stub->state_seen_on_zero = stub->control->state;
    }
}

static bool stub_apply(void *context, const int16_t target[4])
{
    motor_stub_t *stub = (motor_stub_t *)context;
    size_t i;
    ++stub->apply_calls;
    for (i = 0; i < 4; ++i) {
        stub->last_target[i] = target[i];
    }
    return true;
}

static bool stub_prepare(void *context, uint32_t now_ms)
{
    motor_stub_t *stub = (motor_stub_t *)context;
    (void)now_ms;
    ++stub->prepare_calls;
    return true;
}

static bool stub_calibration_hold(
    void *context,
    uint8_t channel,
    int8_t direction,
    uint16_t duty_permille,
    uint32_t now_ms)
{
    motor_stub_t *stub = (motor_stub_t *)context;
    (void)now_ms;
    ++stub->calibration_calls;
    return (channel < 4U) &&
           ((direction == -1) || (direction == 0) || (direction == 1)) &&
           (((direction == 0) && (duty_permille == 0)) ||
            ((direction != 0) && (duty_permille > 0) &&
             (duty_permille <= 120U)));
}

static bool stub_reject(void *context, const int16_t target[4])
{
    (void)context;
    (void)target;
    return false;
}

static void init_control(
    p0_control_t *control,
    motor_stub_t *stub,
    bool motion_available)
{
    p0_motor_ops_t ops;
    memset(stub, 0, sizeof(*stub));
    stub->control = control;
    ops.force_zero = stub_zero;
    ops.prepare_arm = stub_prepare;
    ops.set_wheel_targets = stub_apply;
    ops.calibration_hold = stub_calibration_hold;
    ops.context = stub;
    p0_control_init(control, ops, motion_available);
    p0_control_finish_boot(control, true);
}

static void test_m2a_calibration_command_requires_live_armed_session(void)
{
    p0_control_t control;
    motor_stub_t stub;
    p0_packet_t heartbeat = make_command(P0_MSG_HEARTBEAT, 21, 1);
    p0_packet_t arm = make_command(P0_MSG_ARM, 21, 2);
    p0_packet_t hold = make_command(P0_MSG_M2A_CALIBRATION_HOLD, 21, 3);
    p0_packet_t stop = make_command(P0_MSG_STOP, 0, 0);

    init_control(&control, &stub, true);
    hold.payload_length = UINT16_C(4);
    hold.payload[0] = UINT8_C(2);
    hold.payload[1] = UINT8_C(1);
    p0_write_u16_le(&hold.payload[2], UINT16_C(50));

    CHECK(p0_control_handle_packet(&control, &heartbeat, 10) == P0_STATUS_OK);
    CHECK(p0_control_handle_packet(&control, &arm, 20) == P0_STATUS_OK);
    CHECK(stub.prepare_calls == 1U);
    CHECK(p0_control_handle_packet(&control, &hold, 30) == P0_STATUS_OK);
    CHECK(stub.calibration_calls == 1U);
    CHECK(control.last_command_ms == 30U);
    CHECK(p0_control_handle_packet(&control, &stop, 31) == P0_STATUS_OK);
    CHECK(control.state == P0_STATE_DISARMED);
}

static void test_m2a_calibration_rejection_faults_and_zeros(void)
{
    p0_control_t control;
    motor_stub_t stub;
    p0_packet_t heartbeat = make_command(P0_MSG_HEARTBEAT, 22, 1);
    p0_packet_t arm = make_command(P0_MSG_ARM, 22, 2);
    p0_packet_t hold = make_command(P0_MSG_M2A_CALIBRATION_HOLD, 22, 3);

    init_control(&control, &stub, true);
    CHECK(p0_control_handle_packet(&control, &heartbeat, 10) == P0_STATUS_OK);
    CHECK(p0_control_handle_packet(&control, &arm, 20) == P0_STATUS_OK);
    hold.payload_length = UINT16_C(4);
    hold.payload[0] = UINT8_C(4);
    hold.payload[1] = UINT8_C(1);
    p0_write_u16_le(&hold.payload[2], UINT16_C(50));
    CHECK(p0_control_handle_packet(&control, &hold, 30) ==
          P0_STATUS_TARGET_REJECTED);
    CHECK(control.state == P0_STATE_FAULT);
    CHECK(control.fault == P0_FAULT_LOCAL);
    CHECK(stub.state_seen_on_zero == P0_STATE_ARMED);
}

static p0_packet_t make_command(
    uint8_t type,
    uint32_t session,
    uint32_t sequence)
{
    p0_packet_t packet;
    memset(&packet, 0, sizeof(packet));
    packet.type = type;
    packet.session_id = session;
    packet.sequence = sequence;
    return packet;
}

static void test_crc_known_vector(void)
{
    static const uint8_t text[] = "123456789";
    CHECK(p0_crc32_ieee(text, sizeof(text) - 1U) == UINT32_C(0xCBF43926));
}

static void test_packet_round_trip(void)
{
    p0_packet_t input = make_command(P0_MSG_WHEEL_TARGET, 42, 99);
    p0_packet_t output;
    p0_parser_t parser;
    uint8_t frame[P0_PROTOCOL_MAX_FRAME];
    size_t length;
    size_t i;
    p0_parse_result_t result = P0_PARSE_MORE;

    input.payload_length = UINT16_C(8);
    p0_write_i16_le(&input.payload[0], 100);
    p0_write_i16_le(&input.payload[2], -200);
    p0_write_i16_le(&input.payload[4], 300);
    p0_write_i16_le(&input.payload[6], -400);
    length = p0_packet_encode(&input, frame, sizeof(frame));
    CHECK(length == (size_t)P0_PROTOCOL_FIXED_BYTES + 8U);

    p0_parser_init(&parser);
    for (i = 0; i < length; ++i) {
        result = p0_parser_feed(&parser, frame[i], &output);
    }
    CHECK(result == P0_PARSE_PACKET);
    CHECK(output.type == input.type);
    CHECK(output.session_id == input.session_id);
    CHECK(output.sequence == input.sequence);
    CHECK(output.payload_length == input.payload_length);
    CHECK(memcmp(output.payload, input.payload, 8) == 0);
}

static void test_parser_rejects_bad_crc_and_length(void)
{
    p0_packet_t input = make_command(P0_MSG_HEARTBEAT, 1, 1);
    p0_packet_t output;
    p0_parser_t parser;
    uint8_t frame[P0_PROTOCOL_MAX_FRAME];
    size_t length = p0_packet_encode(&input, frame, sizeof(frame));
    size_t i;
    p0_parse_result_t result = P0_PARSE_MORE;

    frame[length - 1U] ^= UINT8_C(0x01);
    p0_parser_init(&parser);
    for (i = 0; i < length; ++i) {
        result = p0_parser_feed(&parser, frame[i], &output);
    }
    CHECK(result == P0_PARSE_ERROR_CRC);

    p0_parser_init(&parser);
    CHECK(p0_parser_feed(&parser, P0_PROTOCOL_SOF0, &output) == P0_PARSE_MORE);
    CHECK(p0_parser_feed(&parser, P0_PROTOCOL_SOF1, &output) == P0_PARSE_MORE);
    CHECK(p0_parser_feed(&parser, P0_PROTOCOL_VERSION, &output) == P0_PARSE_MORE);
    CHECK(p0_parser_feed(&parser, P0_MSG_HEARTBEAT, &output) == P0_PARSE_MORE);
    CHECK(p0_parser_feed(
              &parser,
              (uint8_t)(P0_PROTOCOL_MAX_PAYLOAD + 1U),
              &output) == P0_PARSE_MORE);
    CHECK(p0_parser_feed(&parser, 0, &output) == P0_PARSE_ERROR_LENGTH);
}

static void test_parser_deterministic_noise(void)
{
    p0_parser_t parser;
    p0_packet_t packet;
    uint32_t value = UINT32_C(0x13579BDF);
    size_t i;

    p0_parser_init(&parser);
    for (i = 0; i < 500000U; ++i) {
        p0_parse_result_t result;
        value = value * UINT32_C(1664525) + UINT32_C(1013904223);
        result = p0_parser_feed(&parser, (uint8_t)(value >> 24), &packet);
        CHECK(parser.count <= P0_PROTOCOL_MAX_FRAME);
        if (result == P0_PARSE_PACKET) {
            CHECK(packet.payload_length <= P0_PROTOCOL_MAX_PAYLOAD);
        }
    }
}

static void test_motion_locked_build_rejects_arm(void)
{
    p0_control_t control;
    motor_stub_t stub;
    p0_packet_t heartbeat = make_command(P0_MSG_HEARTBEAT, 7, 1);
    p0_packet_t arm = make_command(P0_MSG_ARM, 7, 2);

    init_control(&control, &stub, false);
    CHECK(control.state == P0_STATE_DISARMED);
    CHECK(p0_control_handle_packet(&control, &heartbeat, 10) == P0_STATUS_OK);
    CHECK(p0_control_handle_packet(&control, &arm, 20) ==
          P0_STATUS_MOTION_LOCKED);
    CHECK(control.state == P0_STATE_DISARMED);
    CHECK(stub.apply_calls == 0);
    CHECK(stub.zero_calls >= 3);
}

static void test_arm_target_stop_and_timeout(void)
{
    p0_control_t control;
    motor_stub_t stub;
    p0_packet_t heartbeat = make_command(P0_MSG_HEARTBEAT, 9, 1);
    p0_packet_t arm = make_command(P0_MSG_ARM, 9, 2);
    p0_packet_t target = make_command(P0_MSG_WHEEL_TARGET, 9, 3);
    p0_packet_t stop = make_command(P0_MSG_STOP, 0, 0);

    init_control(&control, &stub, true);
    CHECK(p0_control_handle_packet(&control, &heartbeat, 10) == P0_STATUS_OK);
    CHECK(p0_control_handle_packet(&control, &arm, 20) == P0_STATUS_OK);
    CHECK(control.state == P0_STATE_ARMED);

    target.payload_length = UINT16_C(8);
    p0_write_i16_le(&target.payload[0], 11);
    p0_write_i16_le(&target.payload[2], -22);
    p0_write_i16_le(&target.payload[4], 33);
    p0_write_i16_le(&target.payload[6], -44);
    CHECK(p0_control_handle_packet(&control, &target, 30) == P0_STATUS_OK);
    CHECK(stub.apply_calls == 1);
    CHECK(stub.last_target[0] == 11);
    CHECK(stub.last_target[3] == -44);

    CHECK(p0_control_handle_packet(&control, &stop, 31) == P0_STATUS_OK);
    CHECK(control.state == P0_STATE_DISARMED);
    CHECK(control.wheel_target[0] == 0);

    init_control(&control, &stub, true);
    CHECK(p0_control_handle_packet(&control, &heartbeat, 10) == P0_STATUS_OK);
    CHECK(p0_control_handle_packet(&control, &arm, 20) == P0_STATUS_OK);
    stub.state_seen_on_zero = P0_STATE_BOOT;
    p0_control_tick(&control, 271);
    CHECK(control.state == P0_STATE_FAULT);
    CHECK(control.fault == P0_FAULT_TIMEOUT);
    CHECK(stub.state_seen_on_zero == P0_STATE_ARMED);
}

static void test_sequence_and_protocol_errors_fail_safe(void)
{
    p0_control_t control;
    motor_stub_t stub;
    p0_packet_t heartbeat = make_command(P0_MSG_HEARTBEAT, 3, 10);
    p0_packet_t repeated = make_command(P0_MSG_HEARTBEAT, 3, 10);
    p0_packet_t clear = make_command(P0_MSG_CLEAR_FAULT, 0, 0);
    p0_packet_t unknown = make_command(UINT8_C(0x7F), 0, 0);

    init_control(&control, &stub, true);
    CHECK(p0_control_handle_packet(&control, &heartbeat, 1) == P0_STATUS_OK);
    CHECK(p0_control_handle_packet(&control, &repeated, 2) ==
          P0_STATUS_BAD_SEQUENCE);
    CHECK(control.state == P0_STATE_FAULT);
    CHECK(control.fault == P0_FAULT_SEQUENCE);
    CHECK(p0_control_handle_packet(&control, &clear, 3) == P0_STATUS_OK);
    CHECK(control.state == P0_STATE_DISARMED);

    CHECK(p0_control_handle_packet(&control, &unknown, 4) ==
          P0_STATUS_UNKNOWN_COMMAND);
    CHECK(control.state == P0_STATE_FAULT);
    CHECK(control.fault == P0_FAULT_PROTOCOL);

    CHECK(p0_control_handle_packet(&control, &clear, 5) == P0_STATUS_OK);
    p0_control_protocol_fault(&control);
    CHECK(control.state == P0_STATE_FAULT);
    CHECK(control.fault == P0_FAULT_PROTOCOL);
}

static void test_arm_requires_fresh_heartbeat(void)
{
    p0_control_t control;
    motor_stub_t stub;
    p0_packet_t heartbeat = make_command(P0_MSG_HEARTBEAT, 5, 1);
    p0_packet_t arm = make_command(P0_MSG_ARM, 5, 2);

    init_control(&control, &stub, true);
    CHECK(p0_control_handle_packet(&control, &heartbeat, 100) == P0_STATUS_OK);
    CHECK(p0_control_handle_packet(&control, &arm, 351) ==
          P0_STATUS_HEARTBEAT_REQUIRED);
    CHECK(control.state == P0_STATE_FAULT);
    CHECK(control.fault == P0_FAULT_TIMEOUT);
}

static void test_rejected_target_faults_before_ack_or_storage(void)
{
    p0_control_t control;
    motor_stub_t stub;
    p0_packet_t heartbeat = make_command(P0_MSG_HEARTBEAT, 12, 1);
    p0_packet_t arm = make_command(P0_MSG_ARM, 12, 2);
    p0_packet_t target = make_command(P0_MSG_WHEEL_TARGET, 12, 3);

    init_control(&control, &stub, true);
    control.motor.set_wheel_targets = stub_reject;
    CHECK(p0_control_handle_packet(&control, &heartbeat, 10) == P0_STATUS_OK);
    CHECK(p0_control_handle_packet(&control, &arm, 20) == P0_STATUS_OK);
    target.payload_length = UINT16_C(8);
    p0_write_i16_le(&target.payload[0], 100);
    CHECK(p0_control_handle_packet(&control, &target, 30) ==
          P0_STATUS_TARGET_REJECTED);
    CHECK(control.state == P0_STATE_FAULT);
    CHECK(control.fault == P0_FAULT_LOCAL);
    CHECK(control.wheel_target[0] == 0);
    CHECK(stub.state_seen_on_zero == P0_STATE_ARMED);
}

int main(void)
{
    test_crc_known_vector();
    test_packet_round_trip();
    test_parser_rejects_bad_crc_and_length();
    test_parser_deterministic_noise();
    test_motion_locked_build_rejects_arm();
    test_arm_target_stop_and_timeout();
    test_sequence_and_protocol_errors_fail_safe();
    test_arm_requires_fresh_heartbeat();
    test_rejected_target_faults_before_ack_or_storage();
    test_m2a_calibration_command_requires_live_armed_session();
    test_m2a_calibration_rejection_faults_and_zeros();
    puts("PASS: H60 safe-control host tests");
    return EXIT_SUCCESS;
}
