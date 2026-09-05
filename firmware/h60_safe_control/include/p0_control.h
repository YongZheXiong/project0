#ifndef P0_CONTROL_H
#define P0_CONTROL_H

#include "p0_protocol.h"

#include <stdbool.h>
#include <stdint.h>

#define P0_CONTROL_TIMEOUT_MS UINT32_C(250)
#define P0_WHEEL_COUNT UINT8_C(4)

typedef enum {
    P0_STATE_BOOT = 0,
    P0_STATE_DISARMED = 1,
    P0_STATE_ARMED = 2,
    P0_STATE_FAULT = 3
} p0_state_t;

typedef enum {
    P0_FAULT_NONE = 0,
    P0_FAULT_SELF_TEST = 1,
    P0_FAULT_PROTOCOL = 2,
    P0_FAULT_SEQUENCE = 3,
    P0_FAULT_SESSION = 4,
    P0_FAULT_TIMEOUT = 5,
    P0_FAULT_LOCAL = 6,
    P0_FAULT_WATCHDOG_PRETRIP = 7
} p0_fault_t;

typedef enum {
    P0_STATUS_OK = 0,
    P0_STATUS_BAD_STATE = 1,
    P0_STATUS_SELF_TEST_REQUIRED = 2,
    P0_STATUS_HEARTBEAT_REQUIRED = 3,
    P0_STATUS_BAD_SESSION = 4,
    P0_STATUS_BAD_SEQUENCE = 5,
    P0_STATUS_BAD_PAYLOAD = 6,
    P0_STATUS_UNKNOWN_COMMAND = 7,
    P0_STATUS_MOTION_LOCKED = 8,
    P0_STATUS_FAULT_LATCHED = 9,
    P0_STATUS_TARGET_REJECTED = 10
} p0_status_t;

typedef struct {
    void (*force_zero)(void *context);
    bool (*prepare_arm)(void *context, uint32_t now_ms);
    bool (*set_wheel_targets)(void *context, const int16_t target[4]);
    bool (*calibration_hold)(
        void *context,
        uint8_t channel,
        int8_t direction,
        uint16_t duty_permille,
        uint32_t now_ms);
    void *context;
} p0_motor_ops_t;

typedef struct {
    p0_state_t state;
    p0_fault_t fault;
    bool self_test_ok;
    bool motion_output_available;
    bool session_valid;
    uint32_t session_id;
    uint32_t last_sequence;
    uint32_t last_heartbeat_ms;
    uint32_t last_command_ms;
    int16_t wheel_target[4];
    p0_motor_ops_t motor;
} p0_control_t;

void p0_control_init(
    p0_control_t *control,
    p0_motor_ops_t motor,
    bool motion_output_available);
void p0_control_finish_boot(
    p0_control_t *control,
    bool self_test_ok);
p0_status_t p0_control_handle_packet(
    p0_control_t *control,
    const p0_packet_t *packet,
    uint32_t now_ms);
void p0_control_tick(p0_control_t *control, uint32_t now_ms);
void p0_control_protocol_fault(p0_control_t *control);
void p0_control_local_fault(p0_control_t *control, p0_fault_t fault);

#endif
