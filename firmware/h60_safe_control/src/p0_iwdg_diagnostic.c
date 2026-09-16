#include "p0_iwdg_diagnostic.h"
#include "p0_hw.h"

void p0_iwdg_diagnostic_init(
    p0_iwdg_diagnostic_t *diagnostic,
    uint32_t boot_fault_code,
    uint32_t now_ms)
{
    diagnostic->armed_at_ms = now_ms;
    if (boot_fault_code == P0_HW_FAULT_HARD) {
        diagnostic->phase = P0_IWDG_DIAGNOSTIC_COMPLETE;
    } else if (boot_fault_code == P0_HW_FAULT_IWDG_RESET) {
        diagnostic->phase = P0_IWDG_DIAGNOSTIC_EXCEPTION_ARMED;
    } else if (boot_fault_code == P0_HW_FAULT_NONE) {
        diagnostic->phase = P0_IWDG_DIAGNOSTIC_ARMED;
    } else {
        diagnostic->phase = P0_IWDG_DIAGNOSTIC_BLOCKED;
    }
}

bool p0_iwdg_diagnostic_should_trigger_exception(
    p0_iwdg_diagnostic_t *diagnostic,
    uint32_t now_ms)
{
    if ((diagnostic->phase != P0_IWDG_DIAGNOSTIC_EXCEPTION_ARMED) ||
        ((uint32_t)(now_ms - diagnostic->armed_at_ms) <
         P0_IWDG_DIAGNOSTIC_TRIGGER_MS)) {
        return false;
    }
    diagnostic->phase = P0_IWDG_DIAGNOSTIC_BLOCKED;
    return true;
}

bool p0_iwdg_diagnostic_should_stall(
    p0_iwdg_diagnostic_t *diagnostic,
    uint32_t now_ms)
{
    if ((diagnostic->phase != P0_IWDG_DIAGNOSTIC_ARMED) ||
        ((uint32_t)(now_ms - diagnostic->armed_at_ms) <
         P0_IWDG_DIAGNOSTIC_TRIGGER_MS)) {
        return false;
    }
    diagnostic->phase = P0_IWDG_DIAGNOSTIC_BLOCKED;
    return true;
}
