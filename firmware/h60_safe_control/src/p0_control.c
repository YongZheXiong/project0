#include "p0_control.h"

static void clear_targets(p0_control_t *control)
{
    uint8_t i;

    for (i = 0; i < P0_WHEEL_COUNT; ++i) {
        control->wheel_target[i] = 0;
    }
}
static void force_zero_first(p0_control_t *control)
{
    if (control->motor.force_zero != 0) {
        control->motor.force_zero(control->motor.context);
    }
}

static void enter_disarmed(p0_control_t *control)
{
    force_zero_first(control);
    clear_targets(control);
    control->state = P0_STATE_DISARMED;
    control->fault = P0_FAULT_NONE;
    control->session_valid = false;
    control->session_id = 0;
    control->last_sequence = 0;
    control->last_heartbeat_ms = 0;
    control->last_command_ms = 0;
}

static void enter_fault(p0_control_t *control, p0_fault_t fault)
{
    force_zero_first(control);
    clear_targets(control);
    control->state = P0_STATE_FAULT;
    control->fault = fault;
    control->session_valid = false;
    control->session_id = 0;
    control->last_sequence = 0;
    control->last_heartbeat_ms = 0;
    control->last_command_ms = 0;
}

static bool time_is_fresh(uint32_t now_ms, uint32_t last_ms)
{
    return (uint32_t)(now_ms - last_ms) <= P0_CONTROL_TIMEOUT_MS;
}

static bool packet_has_new_sequence(
    const p0_control_t *control,
    const p0_packet_t *packet)
{
    return (packet->sequence != 0) &&
           (packet->sequence > control->last_sequence);
}

static bool targets_are_zero(const p0_control_t *control)
{
    uint8_t i;

    for (i = 0; i < P0_WHEEL_COUNT; ++i) {
        if (control->wheel_target[i] != 0) {
            return false;
        }
    }
    return true;
}

void p0_control_init(
    p0_control_t *control,
    p0_motor_ops_t motor,
    bool motion_output_available)
{
    control->state = P0_STATE_BOOT;
    control->fault = P0_FAULT_NONE;
    control->self_test_ok = false;
    control->motion_output_available = motion_output_available;
    control->session_valid = false;
    control->session_id = 0;
    control->last_sequence = 0;
    control->last_heartbeat_ms = 0;
    control->last_command_ms = 0;
    control->motor = motor;
    clear_targets(control);
    force_zero_first(control);
}

void p0_control_finish_boot(
    p0_control_t *control,
    bool self_test_ok)
{
    control->self_test_ok = self_test_ok;
    if (self_test_ok) {
        enter_disarmed(control);
    } else {
        enter_fault(control, P0_FAULT_SELF_TEST);
    }
}

static p0_status_t handle_heartbeat(
    p0_control_t *control,
    const p0_packet_t *packet,
    uint32_t now_ms)
{
    if (packet->payload_length != 0 || packet->session_id == 0) {
        enter_fault(control, P0_FAULT_PROTOCOL);
        return P0_STATUS_BAD_PAYLOAD;
    }

    if ((control->state != P0_STATE_DISARMED) &&
        (control->state != P0_STATE_ARMED)) {
        force_zero_first(control);
        return P0_STATUS_BAD_STATE;
    }

    if (!control->session_valid) {
        if ((control->state != P0_STATE_DISARMED) ||
            (packet->sequence == 0)) {
            enter_fault(control, P0_FAULT_SESSION);
            return P0_STATUS_BAD_SESSION;
        }
        control->session_valid = true;
        control->session_id = packet->session_id;
        control->last_sequence = packet->sequence;
        control->last_heartbeat_ms = now_ms;
        return P0_STATUS_OK;
    }

    if (packet->session_id != control->session_id) {
        enter_fault(control, P0_FAULT_SESSION);
        return P0_STATUS_BAD_SESSION;
    }
    if (!packet_has_new_sequence(control, packet)) {
        enter_fault(control, P0_FAULT_SEQUENCE);
        return P0_STATUS_BAD_SEQUENCE;
    }

    control->last_sequence = packet->sequence;
    control->last_heartbeat_ms = now_ms;
    return P0_STATUS_OK;
}

static p0_status_t handle_arm(
    p0_control_t *control,
    const p0_packet_t *packet,
    uint32_t now_ms)
{
    if (packet->payload_length != 0) {
        enter_fault(control, P0_FAULT_PROTOCOL);
        return P0_STATUS_BAD_PAYLOAD;
    }
    if (control->state != P0_STATE_DISARMED) {
        enter_fault(control, P0_FAULT_PROTOCOL);
        return P0_STATUS_BAD_STATE;
    }
    if (!control->self_test_ok) {
        force_zero_first(control);
        return P0_STATUS_SELF_TEST_REQUIRED;
    }
    if (!control->session_valid ||
        (packet->session_id != control->session_id)) {
        enter_fault(control, P0_FAULT_SESSION);
        return P0_STATUS_BAD_SESSION;
    }
    if (!packet_has_new_sequence(control, packet)) {
        enter_fault(control, P0_FAULT_SEQUENCE);
        return P0_STATUS_BAD_SEQUENCE;
    }
    if (!time_is_fresh(now_ms, control->last_heartbeat_ms)) {
        enter_fault(control, P0_FAULT_TIMEOUT);
        return P0_STATUS_HEARTBEAT_REQUIRED;
    }
    if (!targets_are_zero(control)) {
        enter_fault(control, P0_FAULT_PROTOCOL);
        return P0_STATUS_BAD_STATE;
    }

    control->last_sequence = packet->sequence;
    if (!control->motion_output_available) {
        force_zero_first(control);
        return P0_STATUS_MOTION_LOCKED;
    }
    if ((control->motor.prepare_arm != 0) &&
        !control->motor.prepare_arm(control->motor.context, now_ms)) {
        enter_fault(control, P0_FAULT_LOCAL);
        return P0_STATUS_TARGET_REJECTED;
    }

    control->state = P0_STATE_ARMED;
    control->last_command_ms = now_ms;
    return P0_STATUS_OK;
}

static p0_status_t handle_m2a_calibration_hold(
    p0_control_t *control,
    const p0_packet_t *packet,
    uint32_t now_ms)
{
    uint8_t channel;
    int8_t direction;
    uint16_t duty_permille;

    if (packet->payload_length != UINT16_C(4)) {
        enter_fault(control, P0_FAULT_PROTOCOL);
        return P0_STATUS_BAD_PAYLOAD;
    }
    if (control->state != P0_STATE_ARMED) {
        enter_fault(control, P0_FAULT_PROTOCOL);
        return P0_STATUS_BAD_STATE;
    }
    if (!control->session_valid ||
        (packet->session_id != control->session_id)) {
        enter_fault(control, P0_FAULT_SESSION);
        return P0_STATUS_BAD_SESSION;
    }
    if (!packet_has_new_sequence(control, packet)) {
        enter_fault(control, P0_FAULT_SEQUENCE);
        return P0_STATUS_BAD_SEQUENCE;
    }
    if (!time_is_fresh(now_ms, control->last_heartbeat_ms)) {
        enter_fault(control, P0_FAULT_TIMEOUT);
        return P0_STATUS_HEARTBEAT_REQUIRED;
    }

    channel = packet->payload[0];
    direction = (int8_t)packet->payload[1];
    duty_permille = p0_read_u16_le(&packet->payload[2]);
    if ((control->motor.calibration_hold == 0) ||
        !control->motor.calibration_hold(
            control->motor.context,
            channel,
            direction,
            duty_permille,
            now_ms)) {
        enter_fault(control, P0_FAULT_LOCAL);
        return P0_STATUS_TARGET_REJECTED;
    }

    control->last_sequence = packet->sequence;
    control->last_command_ms = now_ms;
    return P0_STATUS_OK;
}

static p0_status_t handle_wheel_target(
    p0_control_t *control,
    const p0_packet_t *packet,
    uint32_t now_ms)
{
    int16_t target[4];
    uint8_t i;

    if (packet->payload_length != UINT16_C(8)) {
        enter_fault(control, P0_FAULT_PROTOCOL);
        return P0_STATUS_BAD_PAYLOAD;
    }
    if (control->state != P0_STATE_ARMED) {
        enter_fault(control, P0_FAULT_PROTOCOL);
        return P0_STATUS_BAD_STATE;
    }
    if (!control->session_valid ||
        (packet->session_id != control->session_id)) {
        enter_fault(control, P0_FAULT_SESSION);
        return P0_STATUS_BAD_SESSION;
    }
    if (!packet_has_new_sequence(control, packet)) {
        enter_fault(control, P0_FAULT_SEQUENCE);
        return P0_STATUS_BAD_SEQUENCE;
    }
    if (!time_is_fresh(now_ms, control->last_heartbeat_ms)) {
        enter_fault(control, P0_FAULT_TIMEOUT);
        return P0_STATUS_HEARTBEAT_REQUIRED;
    }

    for (i = 0; i < P0_WHEEL_COUNT; ++i) {
        target[i] = p0_read_i16_le(&packet->payload[(size_t)i * 2U]);
    }
    if ((control->motor.set_wheel_targets == 0) ||
        !control->motor.set_wheel_targets(control->motor.context, target)) {
        enter_fault(control, P0_FAULT_LOCAL);
        return P0_STATUS_TARGET_REJECTED;
    }
    for (i = 0; i < P0_WHEEL_COUNT; ++i) {
        control->wheel_target[i] = target[i];
    }
    control->last_sequence = packet->sequence;
    control->last_command_ms = now_ms;
    return P0_STATUS_OK;
}

static p0_status_t handle_clear_fault(
    p0_control_t *control,
    const p0_packet_t *packet)
{
    if (packet->payload_length != 0) {
        force_zero_first(control);
        return P0_STATUS_BAD_PAYLOAD;
    }
    if (control->state != P0_STATE_FAULT) {
        force_zero_first(control);
        return P0_STATUS_BAD_STATE;
    }
    if (!control->self_test_ok) {
        force_zero_first(control);
        return P0_STATUS_SELF_TEST_REQUIRED;
    }
    enter_disarmed(control);
    return P0_STATUS_OK;
}

p0_status_t p0_control_handle_packet(
    p0_control_t *control,
    const p0_packet_t *packet,
    uint32_t now_ms)
{
    switch (packet->type) {
    case P0_MSG_STOP:
    case P0_MSG_DISARM:
        if (packet->payload_length != 0) {
            enter_fault(control, P0_FAULT_PROTOCOL);
            return P0_STATUS_BAD_PAYLOAD;
        }
        enter_disarmed(control);
        return P0_STATUS_OK;
    case P0_MSG_CLEAR_FAULT:
        return handle_clear_fault(control, packet);
    default:
        break;
    }

    if (control->state == P0_STATE_FAULT) {
        force_zero_first(control);
        return P0_STATUS_FAULT_LATCHED;
    }

    switch (packet->type) {
    case P0_MSG_HEARTBEAT:
        return handle_heartbeat(control, packet, now_ms);
    case P0_MSG_ARM:
        return handle_arm(control, packet, now_ms);
    case P0_MSG_WHEEL_TARGET:
        return handle_wheel_target(control, packet, now_ms);
    case P0_MSG_M2A_CALIBRATION_HOLD:
        return handle_m2a_calibration_hold(control, packet, now_ms);
    default:
        enter_fault(control, P0_FAULT_PROTOCOL);
        return P0_STATUS_UNKNOWN_COMMAND;
    }
}

void p0_control_tick(p0_control_t *control, uint32_t now_ms)
{
    if (control->state != P0_STATE_ARMED) {
        return;
    }
    if (!time_is_fresh(now_ms, control->last_heartbeat_ms) ||
        !time_is_fresh(now_ms, control->last_command_ms)) {
        enter_fault(control, P0_FAULT_TIMEOUT);
    }
}

void p0_control_protocol_fault(p0_control_t *control)
{
    enter_fault(control, P0_FAULT_PROTOCOL);
}

void p0_control_local_fault(p0_control_t *control, p0_fault_t fault)
{
    if (fault == P0_FAULT_NONE) {
        fault = P0_FAULT_LOCAL;
    }
    enter_fault(control, fault);
}
