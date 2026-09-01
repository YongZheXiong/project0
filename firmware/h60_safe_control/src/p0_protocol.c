#include "p0_protocol.h"

#include "p0_crc32.h"

uint16_t p0_read_u16_le(const uint8_t *data)
{
    return (uint16_t)((uint16_t)data[0] | ((uint16_t)data[1] << 8));
}
int16_t p0_read_i16_le(const uint8_t *data)
{
    return (int16_t)p0_read_u16_le(data);
}

uint32_t p0_read_u32_le(const uint8_t *data)
{
    return (uint32_t)data[0] |
           ((uint32_t)data[1] << 8) |
           ((uint32_t)data[2] << 16) |
           ((uint32_t)data[3] << 24);
}

void p0_write_u16_le(uint8_t *data, uint16_t value)
{
    data[0] = (uint8_t)(value & UINT16_C(0xFF));
    data[1] = (uint8_t)(value >> 8);
}

void p0_write_i16_le(uint8_t *data, int16_t value)
{
    p0_write_u16_le(data, (uint16_t)value);
}

void p0_write_u32_le(uint8_t *data, uint32_t value)
{
    data[0] = (uint8_t)(value & UINT32_C(0xFF));
    data[1] = (uint8_t)((value >> 8) & UINT32_C(0xFF));
    data[2] = (uint8_t)((value >> 16) & UINT32_C(0xFF));
    data[3] = (uint8_t)((value >> 24) & UINT32_C(0xFF));
}

void p0_parser_init(p0_parser_t *parser)
{
    parser->count = 0;
    parser->expected = 0;
}

static void parser_restart_from_byte(p0_parser_t *parser, uint8_t byte)
{
    parser->count = 0;
    parser->expected = 0;
    if (byte == P0_PROTOCOL_SOF0) {
        parser->frame[0] = byte;
        parser->count = 1;
    }
}

static p0_parse_result_t parser_finish(
    p0_parser_t *parser,
    p0_packet_t *packet)
{
    uint16_t payload_length = p0_read_u16_le(&parser->frame[4]);
    size_t crc_offset = (size_t)14 + (size_t)payload_length;
    uint32_t expected_crc = p0_read_u32_le(&parser->frame[crc_offset]);
    uint32_t actual_crc = p0_crc32_ieee(
        &parser->frame[2],
        (size_t)12 + (size_t)payload_length);
    size_t i;

    if (parser->frame[2] != P0_PROTOCOL_VERSION) {
        p0_parser_init(parser);
        return P0_PARSE_ERROR_VERSION;
    }
    if (actual_crc != expected_crc) {
        p0_parser_init(parser);
        return P0_PARSE_ERROR_CRC;
    }

    packet->type = parser->frame[3];
    packet->payload_length = payload_length;
    packet->session_id = p0_read_u32_le(&parser->frame[6]);
    packet->sequence = p0_read_u32_le(&parser->frame[10]);
    for (i = 0; i < (size_t)payload_length; ++i) {
        packet->payload[i] = parser->frame[14 + i];
    }
    p0_parser_init(parser);
    return P0_PARSE_PACKET;
}

p0_parse_result_t p0_parser_feed(
    p0_parser_t *parser,
    uint8_t byte,
    p0_packet_t *packet)
{
    if (parser->count == 0) {
        if (byte == P0_PROTOCOL_SOF0) {
            parser->frame[0] = byte;
            parser->count = 1;
        }
        return P0_PARSE_MORE;
    }

    if (parser->count == 1) {
        if (byte == P0_PROTOCOL_SOF1) {
            parser->frame[1] = byte;
            parser->count = 2;
        } else {
            parser_restart_from_byte(parser, byte);
        }
        return P0_PARSE_MORE;
    }

    if (parser->count >= P0_PROTOCOL_MAX_FRAME) {
        parser_restart_from_byte(parser, byte);
        return P0_PARSE_ERROR_LENGTH;
    }

    parser->frame[parser->count++] = byte;
    if (parser->count == 6) {
        uint16_t payload_length = p0_read_u16_le(&parser->frame[4]);
        if (payload_length > P0_PROTOCOL_MAX_PAYLOAD) {
            p0_parser_init(parser);
            return P0_PARSE_ERROR_LENGTH;
        }
        parser->expected = (size_t)P0_PROTOCOL_FIXED_BYTES +
                           (size_t)payload_length;
    }

    if ((parser->expected != 0) && (parser->count == parser->expected)) {
        return parser_finish(parser, packet);
    }
    return P0_PARSE_MORE;
}

size_t p0_packet_encode(
    const p0_packet_t *packet,
    uint8_t *output,
    size_t output_capacity)
{
    size_t total;
    size_t i;
    size_t crc_offset;
    uint32_t crc;

    if (packet->payload_length > P0_PROTOCOL_MAX_PAYLOAD) {
        return 0;
    }
    total = (size_t)P0_PROTOCOL_FIXED_BYTES +
            (size_t)packet->payload_length;
    if (output_capacity < total) {
        return 0;
    }

    output[0] = P0_PROTOCOL_SOF0;
    output[1] = P0_PROTOCOL_SOF1;
    output[2] = P0_PROTOCOL_VERSION;
    output[3] = packet->type;
    p0_write_u16_le(&output[4], packet->payload_length);
    p0_write_u32_le(&output[6], packet->session_id);
    p0_write_u32_le(&output[10], packet->sequence);
    for (i = 0; i < (size_t)packet->payload_length; ++i) {
        output[14 + i] = packet->payload[i];
    }

    crc_offset = (size_t)14 + (size_t)packet->payload_length;
    crc = p0_crc32_ieee(
        &output[2],
        (size_t)12 + (size_t)packet->payload_length);
    p0_write_u32_le(&output[crc_offset], crc);
    return total;
}
