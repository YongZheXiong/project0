"""W1.5 safety-panel state for the no-Orin web teleop tool."""

from __future__ import annotations

from typing import Any


PANEL_ID = "W1.5-NO-ORIN-SAFETY-STATE-PANEL-20260910-001"
W1_RESULT = "W1_REAL_COLD_PROBE_PASS / CLOSEOUT_OK"

PROHIBITED_ACTIONS = (
    "open_real_h60_serial",
    "flash_firmware",
    "arm_real_h60",
    "connect_motors",
    "forward_reverse_motion",
    "w2_w3_field_run",
    "m3_or_landed_motion",
)

ALLOWED_NOW = (
    "offline_fake_serial_review",
    "stop_disarm_fake_session",
    "prepare_w2_package_offline",
)


def build_safety_panel_state(controller_state: dict[str, Any]) -> dict[str, Any]:
    """Summarize W1.5 safety state without creating a device-action path."""

    h60 = controller_state.get("h60") or {}
    commands = list(controller_state.get("commands") or [])
    identity = str(h60.get("identity", ""))
    fake_serial_only = identity.startswith("FAKE-H60")
    profile_commands = [
        command
        for command in commands
        if str(command.get("command", "")).startswith("PROFILE_")
    ]
    fault_reason = controller_state.get("fault_reason")

    if not fake_serial_only:
        overall = "FAIL_NON_FAKE_LINK"
    elif fault_reason:
        overall = "ATTENTION_FAULT_LATCHED"
    else:
        overall = "READY_FOR_W2_PACKAGE_PREP_ONLY"

    return {
        "panel_id": PANEL_ID,
        "gate": "W1.5",
        "overall": overall,
        "mode": "OFFLINE_FAKE_SERIAL_ONLY",
        "historical_w1": {
            "status": W1_RESULT,
            "live_state": "NOT_CURRENT_CONFIRMATION",
            "meaning": "identity_telemetry_stop_ack_closeout_only",
        },
        "live_physical_state": "UNCONFIRMED_IN_THIS_SESSION",
        "entity_authorization": "LOCKED_PENDING_NEW_FIELD_PACKAGE",
        "next_gate": {
            "id": "W2",
            "status": "LOCKED",
            "reason": "requires fresh physical confirmation, independent package, and exact authorization",
        },
        "current_backend": {
            "state": controller_state.get("state"),
            "active_direction": controller_state.get("active_direction"),
            "fault_reason": fault_reason,
            "fake_serial_only": fake_serial_only,
            "simulated_profile_commands": len(profile_commands),
            "lease_remaining_ms": controller_state.get("lease_remaining_ms", 0),
            "h60_scenario": h60.get("scenario"),
        },
        "checks": [
            _check(
                "LOCAL_FAKE_BACKEND",
                "PASS" if fake_serial_only else "FAIL",
                "server_state_uses_fake_h60_identity" if fake_serial_only else "non_fake_h60_identity_visible",
            ),
            _check(
                "W1_HISTORICAL_ONLY",
                "PASS",
                "w1_result_does_not_confirm_current_live_power_or_wiring",
            ),
            _check(
                "LIVE_PHYSICAL_STATE",
                "UNCONFIRMED",
                "fresh_field_state_required_before_any_real_device_action",
            ),
            _check(
                "REAL_DEVICE_ACTION",
                "LOCKED",
                "no_real_serial_flash_arm_or_motion_entry_exists_in_w1_5",
            ),
            _check(
                "W2_GATE",
                "LOCKED",
                "w2_requires_independent_field_package_and_exact_authorization",
            ),
        ],
        "allowed_now": list(ALLOWED_NOW),
        "prohibited_actions": list(PROHIBITED_ACTIONS),
    }


def _check(check_id: str, status: str, reason: str) -> dict[str, str]:
    return {
        "id": check_id,
        "status": status,
        "reason": reason,
    }
