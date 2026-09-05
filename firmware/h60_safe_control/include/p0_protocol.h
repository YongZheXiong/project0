#ifndef P0_PROTOCOL_H
#define P0_PROTOCOL_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define P0_PROTOCOL_SOF0 UINT8_C(0xA5)
#define P0_PROTOCOL_SOF1 UINT8_C(0x5A)
#define P0_PROTOCOL_VERSION UINT8_C(1)
#define P0_PROTOCOL_MAX_PAYLOAD UINT16_C(48)
#define P0_PROTOCOL_FIXED_BYTES UINT16_C(18)
#define P0_PROTOCOL_MAX_FRAME \
    ((size_t)P0_PROTOCOL_FIXED_BYTES + (size_t)P0_PROTOCOL_MAX_PAYLOAD)

typedef enum {
    P0_MSG_HEARTBEAT = 0x01,
    P0_MSG_ARM = 0x02,
    P0_MSG_DISARM = 0x03,
    P0_MSG_STOP = 0x04,
    P0_MSG_WHEEL_TARGET = 0x05,
    P0_MSG_CLEAR_FAULT = 0x06,
    P0_MSG_M2A_CALIBRATION_HOLD = 0x07,
    P0_MSG_TELEMETRY = 0x80,
    P0_MSG_ACK = 0x81,
    P0_MSG_NACK = 0x82
} p0_message_type_t;

typedef struct {
    uint8_t type;
    uint16_t payload_length;
    uint32_t session_id;
    uint32_t sequence;
    uint8_t payload[P0_PROTOCOL_MAX_PAYLOAD];
} p0_packet_t;

typedef enum {
    P0_PARSE_MORE = 0,
    P0_PARSE_PACKET = 1,
    P0_PARSE_ERROR_LENGTH = -1,
    P0_PARSE_ERROR_VERSION = -2,
    P0_PARSE_ERROR_CRC = -3
} p0_parse_result_t;

typedef struct {
    uint8_t frame[P0_PROTOCOL_MAX_FRAME];
    size_t count;
    size_t expected;
} p0_parser_t;

void p0_parser_init(p0_parser_t *parser);
p0_parse_result_t p0_parser_feed(
    p0_parser_t *parser,
    uint8_t byte,
    p0_packet_t *packet);

size_t p0_packet_encode(
    const p0_packet_t *packet,
    uint8_t *output,
    size_t output_capacity);

uint16_t p0_read_u16_le(const uint8_t *data);
int16_t p0_read_i16_le(const uint8_t *data);
uint32_t p0_read_u32_le(const uint8_t *data);
void p0_write_u16_le(uint8_t *data, uint16_t value);
void p0_write_i16_le(uint8_t *data, int16_t value);
void p0_write_u32_le(uint8_t *data, uint32_t value);

#endif
