/* Host-only H60 control/protocol/motion integration with synthetic dynamics. */
#include "p0_control.h"
#include "p0_motion.h"
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
    p0_motion_controller_t motion;
    int16_t output[4];
    unsigned force_zero_count;
} fixture_t;

static void force_zero(void *context)
{
    fixture_t *fixture = context;
    p0_motion_reset(&fixture->motion);
    memset(fixture->output, 0, sizeof(fixture->output));
    ++fixture->force_zero_count;
}

static bool prepare_arm(void *context, uint32_t now_ms)
{
    (void)context;
    (void)now_ms;
    return true;
}

static bool set_targets(void *context, const int16_t target[4])
{
    fixture_t *fixture = context;
    return p0_motion_set_targets(&fixture->motion, target);
}

static bool reject_calibration(
    void *context,
    uint8_t channel,
    int8_t direction,
    uint16_t duty_permille,
    uint32_t now_ms)
{
    (void)context;
    (void)channel;
    (void)direction;
    (void)duty_permille;
    (void)now_ms;
    return false;
}

static p0_motion_config_t synthetic_h60_config(void)
{
    p0_motion_config_t config = {0};
    const uint32_t cpr[4] = {2926, 2923, 2929, 2922};
    const uint8_t bits[4] = {32, 16, 32, 16};
    uint8_t i;

    config.control_period_ms = P0_MOTION_CONTROL_PERIOD_MS;
    config.maximum_target_mm_s = UINT16_C(200);
    config.acceleration_mm_s2 = UINT16_C(10000);
    config.deceleration_mm_s2 = UINT16_C(10000);
    config.reversal_zero_hold_ms = UINT16_C(20);
    config.zero_speed_threshold_mm_s = UINT16_C(40);
    config.maximum_output_permille = UINT16_C(300);
    config.kp_q10 = P0_MOTION_GAIN_SCALE;
    config.ki_q10_per_s = 0;
    for (i = 0; i < P0_MOTION_CHANNEL_COUNT; ++i) {
        config.encoder_counts_per_revolution[i] = cpr[i];
        config.maximum_encoder_delta_counts[i] = UINT32_C(1000);
        config.wheel_circumference_mm[i] = UINT32_C(1000);
        config.encoder_counter_bits[i] = bits[i];
        config.encoder_polarity[i] = INT8_C(-1);
    }
    return config;
}

static p0_status_t deliver(
    p0_control_t *control,
    const p0_packet_t *source,
    uint32_t now_ms)
{
    uint8_t frame[P0_PROTOCOL_MAX_FRAME];
    p0_parser_t parser;
    p0_packet_t decoded = {0};
    p0_parse_result_t result = P0_PARSE_MORE;
    size_t length = p0_packet_encode(source, frame, sizeof(frame));
    size_t i;

    CHECK(length != 0);
    p0_parser_init(&parser);
    for (i = 0; i < length; ++i) {
        result = p0_parser_feed(&parser, frame[i], &decoded);
    }
    CHECK(result == P0_PARSE_PACKET);
    return p0_control_handle_packet(control, &decoded, now_ms);
}

static p0_packet_t session_packet(uint8_t type, uint32_t sequence)
{
    p0_packet_t packet = {0};
    packet.type = type;
    packet.session_id = UINT32_C(0xA5A55A5A);
    packet.sequence = sequence;
    return packet;
}

static p0_packet_t wheel_packet(uint32_t sequence, const int16_t target[4])
{
    p0_packet_t packet = session_packet(P0_MSG_WHEEL_TARGET, sequence);
    uint8_t i;
    packet.payload_length = UINT16_C(8);
    for (i = 0; i < P0_MOTION_CHANNEL_COUNT; ++i) {
        p0_write_i16_le(&packet.payload[(size_t)i * 2U], target[i]);
    }
    return packet;
}

static void test_forward_reverse_stop_and_timeout_chain(void)
{
    const int16_t forward[4] = {-100, 100, -100, 100};
    const int16_t reverse[4] = {100, -100, 100, -100};
    p0_motion_config_t config = synthetic_h60_config();
    fixture_t fixture = {0};
    p0_motor_ops_t operations = {
        force_zero, prepare_arm, set_targets, reject_calibration, &fixture};
    p0_control_t control;
    p0_packet_t packet;
    int32_t counts[4] = {0, 0, 0, 0};
    int16_t previous[4];
    uint8_t i;

    CHECK(p0_motion_init(&fixture.motion, &config));
    p0_control_init(&control, operations, true);
    p0_control_finish_boot(&control, true);
    CHECK(control.state == P0_STATE_DISARMED);

    packet = session_packet(P0_MSG_HEARTBEAT, UINT32_C(1));
    CHECK(deliver(&control, &packet, UINT32_C(0)) == P0_STATUS_OK);
    packet = session_packet(P0_MSG_ARM, UINT32_C(2));
    CHECK(deliver(&control, &packet, UINT32_C(1)) == P0_STATUS_OK);
    CHECK(control.state == P0_STATE_ARMED);

    packet = wheel_packet(UINT32_C(3), forward);
    CHECK(deliver(&control, &packet, UINT32_C(2)) == P0_STATUS_OK);
    CHECK(p0_motion_step(&fixture.motion, counts, fixture.output));
    for (i = 0; i < P0_MOTION_CHANNEL_COUNT; ++i) {
        CHECK(fixture.output[i] == 0);
    }

    counts[0] = 1;
    counts[1] = 65535;
    counts[2] = 1;
    counts[3] = 65535;
    CHECK(p0_motion_step(&fixture.motion, counts, fixture.output));
    for (i = 0; i < P0_MOTION_CHANNEL_COUNT; ++i) {
        CHECK((int32_t)fixture.output[i] * forward[i] > 0);
        CHECK((int32_t)fixture.motion.measured_speed_mm_s[i] * forward[i] > 0);
        previous[i] = fixture.output[i];
    }

    packet = wheel_packet(UINT32_C(4), reverse);
    CHECK(deliver(&control, &packet, UINT32_C(3)) == P0_STATUS_OK);
    for (i = 0; i < UINT8_C(3); ++i) {
        uint8_t channel;
        CHECK(p0_motion_step(&fixture.motion, counts, fixture.output));
        for (channel = 0; channel < P0_MOTION_CHANNEL_COUNT; ++channel) {
            CHECK(!((previous[channel] > 0) && (fixture.output[channel] < 0)));
            CHECK(!((previous[channel] < 0) && (fixture.output[channel] > 0)));
            previous[channel] = fixture.output[channel];
        }
    }
    for (i = 0; i < P0_MOTION_CHANNEL_COUNT; ++i) {
        CHECK((int32_t)fixture.output[i] * reverse[i] > 0);
    }

    p0_control_tick(&control, P0_CONTROL_TIMEOUT_MS + UINT32_C(1));
    CHECK(control.state == P0_STATE_FAULT);
    CHECK(control.fault == P0_FAULT_TIMEOUT);
    for (i = 0; i < P0_MOTION_CHANNEL_COUNT; ++i) {
        CHECK(fixture.output[i] == 0);
        CHECK(fixture.motion.requested_target_mm_s[i] == 0);
    }

    memset(&packet, 0, sizeof(packet));
    packet.type = P0_MSG_STOP;
    CHECK(deliver(&control, &packet, UINT32_C(300)) == P0_STATUS_OK);
    CHECK(control.state == P0_STATE_DISARMED);
    CHECK(fixture.force_zero_count >= 3U);
}

int main(void)
{
    test_forward_reverse_stop_and_timeout_chain();
    puts("PASS: synthetic H60 protocol/control/motion integration");
    return EXIT_SUCCESS;
}
