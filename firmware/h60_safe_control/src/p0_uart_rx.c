#include "p0_uart_rx.h"

_Static_assert(ATOMIC_INT_LOCK_FREE == 2, "UART indices must be lock-free");
_Static_assert(ATOMIC_BOOL_LOCK_FREE == 2, "UART fault must be lock-free");

void p0_uart_rx_init(p0_uart_rx_t *rx)
{
    atomic_init(&rx->head, 0);
    atomic_init(&rx->tail, 0);
    atomic_init(&rx->fault, false);
}

void p0_uart_rx_push_isr(p0_uart_rx_t *rx, uint8_t byte, bool error)
{
    unsigned head;
    unsigned next;

    if (error) {
        atomic_store_explicit(&rx->fault, true, memory_order_release);
    }
    if (atomic_load_explicit(&rx->fault, memory_order_acquire)) {
        return;
    }
    head = atomic_load_explicit(&rx->head, memory_order_relaxed);
    next = (head + 1U) % P0_UART_RX_CAPACITY;
    if (next == atomic_load_explicit(&rx->tail, memory_order_acquire)) {
        atomic_store_explicit(&rx->fault, true, memory_order_release);
        return;
    }
    rx->data[head] = byte;
    atomic_store_explicit(&rx->head, next, memory_order_release);
}

bool p0_uart_rx_pop(p0_uart_rx_t *rx, uint8_t *byte)
{
    unsigned tail = atomic_load_explicit(&rx->tail, memory_order_relaxed);

    if (atomic_load_explicit(&rx->fault, memory_order_acquire) ||
        tail == atomic_load_explicit(&rx->head, memory_order_acquire)) {
        return false;
    }
    *byte = rx->data[tail];
    atomic_store_explicit(&rx->tail,
        (tail + 1U) % P0_UART_RX_CAPACITY, memory_order_release);
    return true;
}

bool p0_uart_rx_take_fault(p0_uart_rx_t *rx)
{
    /* 调用者屏蔽ISR，避免清队列与新接收交错。 */
    if (!atomic_load_explicit(&rx->fault, memory_order_acquire)) {
        return false;
    }
    atomic_store_explicit(&rx->tail,
        atomic_load_explicit(&rx->head, memory_order_relaxed),
        memory_order_relaxed);
    atomic_store_explicit(&rx->fault, false, memory_order_release);
    return true;
}
