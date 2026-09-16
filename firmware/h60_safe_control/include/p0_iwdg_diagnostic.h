#ifndef P0_IWDG_DIAGNOSTIC_H
#define P0_IWDG_DIAGNOSTIC_H

#include <stdbool.h>
#include <stdint.h>

#define P0_IWDG_DIAGNOSTIC_TRIGGER_MS UINT32_C(1500)

typedef enum {
    P0_IWDG_DIAGNOSTIC_BLOCKED = 0,
    P0_IWDG_DIAGNOSTIC_ARMED = 1,
    P0_IWDG_DIAGNOSTIC_EXCEPTION_ARMED = 2,
    P0_IWDG_DIAGNOSTIC_COMPLETE = 3
} p0_iwdg_diagnostic_phase_t;

typedef struct {
    p0_iwdg_diagnostic_phase_t phase;
    uint32_t armed_at_ms;
} p0_iwdg_diagnostic_t;

void p0_iwdg_diagnostic_init(
    p0_iwdg_diagnostic_t *diagnostic,
    uint32_t boot_fault_code,
    uint32_t now_ms);
bool p0_iwdg_diagnostic_should_stall(
    p0_iwdg_diagnostic_t *diagnostic,
    uint32_t now_ms);
bool p0_iwdg_diagnostic_should_trigger_exception(
    p0_iwdg_diagnostic_t *diagnostic,
    uint32_t now_ms);

#endif
