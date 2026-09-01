#ifndef P0_HW_H
#define P0_HW_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define P0_HW_FAULT_MAGIC UINT32_C(0x50304654)

typedef enum {
    P0_HW_FAULT_NONE = 0,
    P0_HW_FAULT_NMI = 1,
    P0_HW_FAULT_HARD = 2,
    P0_HW_FAULT_MEMMANAGE = 3,
    P0_HW_FAULT_BUS = 4,
    P0_HW_FAULT_USAGE = 5,
    P0_HW_FAULT_DEFAULT_IRQ = 6,
    P0_HW_FAULT_ASSERT = 7
} p0_hw_fault_code_t;

typedef struct {
    uint32_t magic;
    uint32_t code;
    uint32_t inverted_code;
} p0_hw_retained_fault_t;

void p0_hw_early_safe_init(void);
void p0_hw_init(void);
void p0_hw_motor_force_safe(void *unused);
void p0_hw_motor_apply_targets(void *unused, const int16_t target[4]);

uint32_t p0_hw_millis(void);
void p0_hw_main_alive(void);
bool p0_hw_supervisor_tripped(void);

bool p0_hw_uart_read_byte(uint8_t *byte);
void p0_hw_uart_write(const uint8_t *data, size_t length);

void p0_hw_encoder_read(int32_t count[4]);
bool p0_hw_vin_read(uint16_t *raw, uint16_t *nominal_mv);

void p0_hw_watchdog_start(void);
void p0_hw_watchdog_feed(void);

uint32_t p0_hw_take_retained_fault(void);
void p0_hw_fault_trap(uint32_t code) __attribute__((noreturn));

#define P0_HW_ASSERT(condition)                                                \
    do {                                                                       \
        if (!(condition)) {                                                    \
            p0_hw_fault_trap(P0_HW_FAULT_ASSERT);                              \
        }                                                                      \
    } while (0)

void SysTick_Handler(void);
void NMI_Handler(void);
void HardFault_Handler(void);
void MemManage_Handler(void);
void BusFault_Handler(void);
void UsageFault_Handler(void);
void Default_Handler(void);

#endif
