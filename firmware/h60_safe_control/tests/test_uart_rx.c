#include "p0_uart_rx.h"
#include "p0_protocol.h"

#include <assert.h>
#include <stdio.h>

int main(void)
{
    p0_uart_rx_t rx;
    p0_parser_t parser;
    p0_packet_t input = {0}, output;
    uint8_t frame[P0_PROTOCOL_MAX_FRAME], byte;
    unsigned i, round, packets = 0;
    size_t length;

    input.type = P0_MSG_M2A_CALIBRATION_HOLD;
    input.session_id = 77;
    input.sequence = 4;
    input.payload_length = 4;
    input.payload[0] = 1;
    input.payload[1] = 1;
    input.payload[2] = 50;
    length = p0_packet_encode(&input, frame, sizeof(frame));
    assert(length == 22);
    p0_uart_rx_init(&rx);
    p0_parser_init(&parser);

    /* 模拟主循环在TX中停读：IRQ仍保存整帧，多次跨环边界不丢序。
       旧轮询只有一个未读DR槽，等同窗口只能留下首字节，无法成帧。 */
    assert(p0_parser_feed(&parser, frame[0], &output) == P0_PARSE_MORE);
    p0_parser_init(&parser);
    for (round = 0; round < 1000; ++round) {
        for (i = 0; i < length; ++i) {
            p0_uart_rx_push_isr(&rx, frame[i], false);
        }
        while (p0_uart_rx_pop(&rx, &byte)) {
            p0_parse_result_t result = p0_parser_feed(&parser, byte, &output);
            assert(result >= 0);
            if (result == P0_PARSE_PACKET) {
                assert(output.sequence == 4 && output.payload[2] == 50);
                ++packets;
            }
        }
        assert(!p0_uart_rx_take_fault(&rx));
    }
    assert(packets == 1000);

    for (i = 0; i < P0_UART_RX_CAPACITY; ++i) {
        p0_uart_rx_push_isr(&rx, (uint8_t)i, false);
    }
    assert(!p0_uart_rx_pop(&rx, &byte));
    assert(p0_uart_rx_take_fault(&rx));
    assert(!p0_uart_rx_pop(&rx, &byte));
    assert(!p0_uart_rx_take_fault(&rx));

    p0_uart_rx_push_isr(&rx, 0xAA, false);
    p0_uart_rx_push_isr(&rx, 0xBB, true);
    p0_uart_rx_push_isr(&rx, 0xCC, false);
    assert(!p0_uart_rx_pop(&rx, &byte));
    assert(p0_uart_rx_take_fault(&rx));
    assert(!p0_uart_rx_pop(&rx, &byte));
    p0_uart_rx_push_isr(&rx, 0xDD, false);
    assert(p0_uart_rx_pop(&rx, &byte) && byte == 0xDD);
    puts("PASS: UART RX overlapping-TX, wrap, overflow and error recovery");
    return 0;
}
