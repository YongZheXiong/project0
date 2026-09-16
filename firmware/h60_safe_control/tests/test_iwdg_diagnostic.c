#include "p0_iwdg_diagnostic.h"
#include "p0_hw.h"

#include <assert.h>
#include <stdio.h>

int main(void)
{
    p0_iwdg_diagnostic_t diagnostic;

    p0_iwdg_diagnostic_init(&diagnostic, P0_HW_FAULT_NONE, UINT32_C(100));
    assert(diagnostic.phase == P0_IWDG_DIAGNOSTIC_ARMED);
    assert(!p0_iwdg_diagnostic_should_stall(&diagnostic, UINT32_C(1599)));
    assert(p0_iwdg_diagnostic_should_stall(&diagnostic, UINT32_C(1600)));
    assert(!p0_iwdg_diagnostic_should_stall(&diagnostic, UINT32_C(9999)));
    assert(!p0_iwdg_diagnostic_should_trigger_exception(
        &diagnostic, UINT32_MAX));

    p0_iwdg_diagnostic_init(
        &diagnostic, P0_HW_FAULT_IWDG_RESET, UINT32_C(0));
    assert(diagnostic.phase == P0_IWDG_DIAGNOSTIC_EXCEPTION_ARMED);
    assert(!p0_iwdg_diagnostic_should_trigger_exception(
        &diagnostic, P0_IWDG_DIAGNOSTIC_TRIGGER_MS - UINT32_C(1)));
    assert(p0_iwdg_diagnostic_should_trigger_exception(
        &diagnostic, P0_IWDG_DIAGNOSTIC_TRIGGER_MS));
    assert(!p0_iwdg_diagnostic_should_trigger_exception(
        &diagnostic, UINT32_MAX));

    p0_iwdg_diagnostic_init(
        &diagnostic, P0_HW_FAULT_HARD, UINT32_C(0));
    assert(diagnostic.phase == P0_IWDG_DIAGNOSTIC_COMPLETE);
    assert(!p0_iwdg_diagnostic_should_stall(&diagnostic, UINT32_MAX));

    p0_iwdg_diagnostic_init(
        &diagnostic, P0_HW_FAULT_BUS, UINT32_C(0));
    assert(diagnostic.phase == P0_IWDG_DIAGNOSTIC_BLOCKED);
    assert(!p0_iwdg_diagnostic_should_stall(&diagnostic, UINT32_MAX));

    p0_iwdg_diagnostic_init(
        &diagnostic, P0_HW_FAULT_NONE, UINT32_MAX - UINT32_C(500));
    assert(!p0_iwdg_diagnostic_should_stall(&diagnostic, UINT32_C(998)));
    assert(p0_iwdg_diagnostic_should_stall(&diagnostic, UINT32_C(999)));

    puts("PASS: one-shot IWDG/HardFault diagnostic sequence and wraparound");
    return 0;
}
