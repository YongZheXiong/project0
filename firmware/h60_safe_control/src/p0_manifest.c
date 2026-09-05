#include "p0_build_config.h"

#define P0_STRINGIFY_INNER(value) #value
#define P0_STRINGIFY(value) P0_STRINGIFY_INNER(value)

const char p0_firmware_manifest[]
    __attribute__((used, section(".firmware_manifest"))) =
        "P0_H60_SAFE;FW=" P0_FIRMWARE_BUILD_LABEL ";MOTION="
        P0_STRINGIFY(P0_MOTION_OUTPUT_COMPILED)
        ";CAL=" P0_STRINGIFY(P0_MOTION_CALIBRATION_VALID)
        ";M2A=" P0_STRINGIFY(P0_M2A_CALIBRATION_BUILD)
        ";TIMEOUT_MS=250;UART_RX=IRQ256-R1"
#if P0_M2A_SLOWDRIVE_BUILD != 0
        ";PWM=SLOW5K-MB-PLUS-50-R1;WAKE_MS=3;STOP=GPIO00"
#elif P0_M2A_CALIBRATION_BUILD != 0
        ";PWM=M2A5K-R1;MIN_DUTY=50"
#endif
        ;
