#ifndef P0_UART_RX_H
#define P0_UART_RX_H

#include <stdbool.h>
#include <stdint.h>
#include <stdatomic.h>

#define P0_UART_RX_CAPACITY UINT32_C(256)

/* 单生产者ISR、单消费者主循环；满时锁错，不覆盖旧字节。 */
typedef struct {
    uint8_t data[P0_UART_RX_CAPACITY];
    atomic_uint head;
    atomic_uint tail;
    atomic_bool fault;
} p0_uart_rx_t;

void p0_uart_rx_init(p0_uart_rx_t *rx);
void p0_uart_rx_push_isr(p0_uart_rx_t *rx, uint8_t byte, bool error);
bool p0_uart_rx_pop(p0_uart_rx_t *rx, uint8_t *byte);
/* 仅在接收ISR被屏蔽时调用；返回true后必须重置解析器并使控制器故障失能。 */
bool p0_uart_rx_take_fault(p0_uart_rx_t *rx);

#endif
