#ifndef P0_BUILD_CONFIG_H
#define P0_BUILD_CONFIG_H

#include <stdint.h>

#ifndef P0_MOTION_OUTPUT_COMPILED
#define P0_MOTION_OUTPUT_COMPILED 0
#endif

#ifndef P0_OFFLINE_MOTION_AUDIT_BUILD
#define P0_OFFLINE_MOTION_AUDIT_BUILD 0
#endif

#ifndef P0_MOTION_CALIBRATION_VALID
#define P0_MOTION_CALIBRATION_VALID 0
#endif

#ifndef P0_M2A_CALIBRATION_BUILD
#define P0_M2A_CALIBRATION_BUILD 0
#endif

#ifndef P0_M2A_SLOWDRIVE_BUILD
#define P0_M2A_SLOWDRIVE_BUILD 0
#endif

#if (P0_M2A_SLOWDRIVE_BUILD != 0) && \
    ((P0_M2A_SLOWDRIVE_BUILD != 1) || (P0_M2A_CALIBRATION_BUILD != 1) || \
     (P0_MOTION_OUTPUT_COMPILED != 1) || (P0_OFFLINE_MOTION_AUDIT_BUILD != 0))
#error "Slowdrive requires the explicit isolated M2-A PWM build"
#endif

#if (P0_MOTION_OUTPUT_COMPILED != 0) && \
    (P0_OFFLINE_MOTION_AUDIT_BUILD == 0) && \
    (P0_M2A_CALIBRATION_BUILD == 0)
#error "Motion code requires the audit target or the explicit M2-A build"
#endif

#if (P0_OFFLINE_MOTION_AUDIT_BUILD != 0) && \
    (P0_M2A_CALIBRATION_BUILD != 0)
#error "Offline audit and M2-A calibration modes are mutually exclusive"
#endif

#if (P0_M2A_CALIBRATION_BUILD != 0) && \
    (P0_MOTION_OUTPUT_COMPILED == 0)
#error "M2-A calibration mode requires the guarded PWM implementation"
#endif

#if P0_MOTION_CALIBRATION_VALID != 0
#error "M1 has no frozen H60 channel, encoder or wheel calibration"
#endif

#define P0_MOTION_RUNTIME_AVAILABLE \
    ((P0_MOTION_OUTPUT_COMPILED != 0) && \
     (P0_MOTION_CALIBRATION_VALID != 0))

#define P0_M2A_RUNTIME_AVAILABLE \
    ((P0_MOTION_OUTPUT_COMPILED != 0) && \
     (P0_M2A_CALIBRATION_BUILD != 0) && \
     (P0_MOTION_CALIBRATION_VALID == 0))

#if P0_M2A_SLOWDRIVE_BUILD != 0
#define P0_FIRMWARE_BUILD_LABEL "0.2.1-M2A-SLOW5K-MB-PLUS-50-R1"
#define P0_FIRMWARE_CAPABILITIES UINT8_C(2)
#elif P0_M2A_CALIBRATION_BUILD != 0
#define P0_FIRMWARE_BUILD_LABEL "0.2.0-M2A"
#define P0_FIRMWARE_CAPABILITIES UINT8_C(2)
#else
#define P0_FIRMWARE_BUILD_LABEL "0.2.0-M1"
#define P0_FIRMWARE_CAPABILITIES UINT8_C(0)
#endif

#define P0_FIRMWARE_VERSION_MAJOR 0
#define P0_FIRMWARE_VERSION_MINOR 2
#if P0_M2A_SLOWDRIVE_BUILD != 0
#define P0_FIRMWARE_VERSION_PATCH 1
#else
#define P0_FIRMWARE_VERSION_PATCH 0
#endif

#endif
