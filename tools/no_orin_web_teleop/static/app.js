const clientId = `w0-${Math.random().toString(16).slice(2)}`;
let sequence = 1;
let holdTimer = null;
let fieldStopTimer = null;
let activeHoldIntent = null;
let currentState = null;
let lastFieldResult = null;
const FIELD_BROWSER_STOP_MS = 300;

const labels = {
  state: {
    DISARMED: "已失能",
    ARM_PENDING: "已申请，待按住方向（板端仍失能）",
    ARMED: "已使能",
    FAULT: "故障锁止",
  },
  direction: {
    forward: "前进",
    reverse: "后退",
    none: "无",
  },
  scenario: {
    normal: "正常",
    fault: "故障锁止",
    timeout: "响应超时",
    identity_drift: "身份漂移",
    reboot: "模拟重启",
    crc_error: "CRC 错误",
    length_error: "长度错误",
    sequence_error: "序号错误",
    real_w2_field: "W2 实板现场链路",
  },
  intent: {
    STOP: "停止",
    DISARM: "解除使能",
    ARM_REQUEST: "申请使能",
    FORWARD_LOW: "低速前进",
    REVERSE_LOW: "低速后退",
  },
  command: {
    STOP: "停止帧",
    DISARM: "失能帧",
    ARM: "使能帧",
    PROFILE_FORWARD_LOW: "低速前进剖面",
    PROFILE_REVERSE_LOW: "低速后退剖面",
  },
  event: {
    intent: "收到意图",
    reject: "拒绝意图",
    h60_command: "H60 指令",
    disconnect: "会话断开",
    fake_scenario: "切换假场景",
    fault_latched: "故障锁止",
  },
  field: {
    intent: "意图",
    client_id: "会话",
    sequence: "序号",
    reason: "原因",
    command: "指令",
    ack: "确认",
    response_reason: "响应",
    scenario: "场景",
    state_after: "之后状态",
    frame_hex: "帧",
  },
  reason: {
    ok: "正常",
    unknown_intent: "未知意图",
    stale_sequence: "旧序号",
    client_session_closed: "该网页会话已关闭，请刷新页面后重新申请",
    stop: "停止完成",
    disarm: "失能完成",
    fault_latched: "故障已锁止",
    identity_drift: "身份漂移",
    telemetry_timeout: "遥测超时",
    h60_fault: "H60 故障",
    h60_reboot: "H60 重启",
    crc_error: "CRC 错误",
    length_error: "长度错误",
    sequence_error: "序号错误",
    backend_loop_late: "后端循环迟到",
    lease_expired: "租约到期",
    lease_expired_stop: "租约到期并停止",
    field_auto_stop: "本阶段短时动作已自动停止",
    client_disconnect: "会话断开",
    audit_log_failure: "证据日志写入失败",
    disconnect_stop_disarm: "断开后停止并失能",
    web_stop: "网页停止",
    web_disarm_pre_stop: "失能前先停止",
    web_disarm: "网页失能",
    arm_requires_neutral: "使能前必须空挡",
    web_arm_request: "网页申请使能",
    arm_rejected: "使能被拒绝",
    arm_pending: "申请已记录，按住方向时才使能板端",
    arm_request_expired: "申请已过期，请重新申请",
    arm_client_mismatch: "不是原申请的网页会话",
    direction_not_enabled: "当前现场包未开放这个方向",
    profile_rejected: "运动剖面被拒绝",
    not_armed: "尚未使能",
    direction_change_requires_neutral: "换向前必须先停止",
    lease_forward: "前进租约",
    lease_reverse: "后退租约",
    forward_lease_renewed: "前进租约已续期",
    reverse_lease_renewed: "后退租约已续期",
    tick: "状态刷新",
    unknown_fake_command: "未知假指令",
    server_state_uses_fake_h60_identity: "后端只暴露假 H60 身份",
    non_fake_h60_identity_visible: "可见非假 H60 身份",
    w1_result_does_not_confirm_current_live_power_or_wiring: "W1 只证明历史冷态边界",
    fresh_field_state_required_before_any_real_device_action: "真实动作前必须重新确认现场",
    no_real_serial_flash_arm_or_motion_entry_exists_in_w1_5: "W1.5 没有真实设备入口",
    w2_requires_independent_field_package_and_exact_authorization: "W2 需要独立现场包和精确授权",
    exact_field_package: "精确现场包已绑定",
    current_package_confirmation: "本包实时确认已绑定",
    landed_motion_not_authorized: "未授权落地运动",
  },
  safetyOverall: {
    READY_FOR_W2_PACKAGE_PREP_ONLY: "仅允许准备 W2 离线包",
    ATTENTION_FAULT_LATCHED: "注意：假链路故障锁止",
    FAIL_NON_FAKE_LINK: "失败：出现非假串口身份",
    W2_FIELD_LINK_READY: "W2 实板架空链路就绪",
    W2_FIELD_LINK_STOPPED: "W2 实板链路已停止",
  },
  mode: {
    OFFLINE_FAKE_SERIAL_ONLY: "仅本机假串口",
    REAL_H60_W2_FIELD_PACKAGE: "W2 实板现场包",
  },
  liveState: {
    UNCONFIRMED_IN_THIS_SESSION: "本轮未确认",
    BOUND_TO_CURRENT_FIELD_PACKAGE: "已绑定本次现场包",
  },
  gateStatus: {
    LOCKED: "已锁定",
    PASS: "通过",
    FAIL: "失败",
    UNCONFIRMED: "未确认",
  },
  check: {
    LOCAL_FAKE_BACKEND: "本机假后端",
    W1_HISTORICAL_ONLY: "W1 仅作历史证据",
    LIVE_PHYSICAL_STATE: "实时现场状态",
    REAL_DEVICE_ACTION: "真实设备动作",
    W2_GATE: "W2 门",
    REAL_W2_PACKAGE: "W2 现场包",
    W3_GATE: "W3 落地门",
  },
  action: {
    offline_fake_serial_review: "复核离线假串口",
    stop_disarm_fake_session: "停止或解除假会话",
    prepare_w2_package_offline: "准备 W2 离线包",
    open_real_h60_serial: "打开真实 H60 串口",
    flash_firmware: "刷写固件",
    arm_real_h60: "使能真实 H60",
    connect_motors: "接入电机",
    forward_reverse_motion: "真实前进/后退",
    w2_w3_field_run: "运行 W2/W3 现场包",
    m3_or_landed_motion: "M3 或落地运动",
    stop: "停止",
    disarm: "解除使能",
    arm_for_enabled_direction: "为当前方向申请使能",
    bounded_airborne_direction: "受限架空方向动作",
    arbitrary_pwm: "任意 PWM",
    direct_direction_change: "直接换向",
    landed_motion: "落地运动",
    w3_w4_or_p2_pass: "W3/W4/P2 放行",
  },
  identity: {
    "FAKE-H60-W0": "假 H60-W0",
  },
};

const els = {
  state: document.querySelector("#state"),
  fault: document.querySelector("#fault"),
  lease: document.querySelector("#lease"),
  direction: document.querySelector("#direction"),
  events: document.querySelector("#events"),
  serial: document.querySelector("#serial"),
  armHint: document.querySelector("#arm small"),
  eyebrow: document.querySelector("#mode-eyebrow"),
  subtitle: document.querySelector("#mode-subtitle"),
  fieldGuide: document.querySelector("#field-guide"),
  fieldStep: document.querySelector("#field-step"),
  fieldFeedback: document.querySelector("#field-feedback"),
  backendDescription: document.querySelector("#backend-description"),
  deviceActionDescription: document.querySelector("#device-action-description"),
  scenario: document.querySelector("#scenario"),
  safetyStatus: document.querySelector("#safety-status"),
  safetyMode: document.querySelector("#safety-mode"),
  liveState: document.querySelector("#live-state"),
  nextGate: document.querySelector("#next-gate"),
  safetyChecks: document.querySelector("#safety-checks"),
  allowedNow: document.querySelector("#allowed-now"),
  prohibited: document.querySelector("#prohibited"),
};

async function post(path, body) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return response.json();
}

async function sendIntent(intent, { refreshPanel = true } = {}) {
  const payload = await post("/api/intent", {
    intent,
    client_id: clientId,
    sequence: sequence++,
  });
  if (payload.state?.h60?.scenario === "real_w2_field") {
    lastFieldResult = payload.result;
  }
  render(payload.state);
  if (refreshPanel) {
    await refreshSafety();
  }
}

async function refresh() {
  const [stateResponse, safetyResponse] = await Promise.all([
    fetch("/api/state"),
    fetch("/api/safety"),
  ]);
  render(await stateResponse.json());
  renderSafety(await safetyResponse.json());
}

async function refreshSafety() {
  const response = await fetch("/api/safety");
  renderSafety(await response.json());
}

function label(table, value, fallback = "未识别") {
  if (value === undefined || value === null || value === "") {
    return fallback;
  }
  return Object.prototype.hasOwnProperty.call(table, value) ? table[value] : fallback;
}

function setRawData(element, value) {
  if (value === undefined || value === null) {
    delete element.dataset.raw;
    return;
  }
  element.dataset.raw = typeof value === "string" ? value : JSON.stringify(value);
}

function toneForState(state) {
  if (state === "FAULT") return "is-bad";
  if (state === "ARMED") return "is-good";
  return "is-neutral";
}

function toneForOverall(overall) {
  if (String(overall).includes("FAIL")) return "is-bad";
  if (String(overall).includes("ATTENTION")) return "is-warn";
  return "is-good";
}

function faultText(reason) {
  if (!reason) return "无故障";
  if (String(reason).includes("direction duration limit reached")) {
    return "方向动作超时，已停车并锁止";
  }
  return label(labels.reason, reason, "故障已锁止，请断电收尾");
}

function render(state) {
  currentState = state;
  els.state.textContent = label(labels.state, state.state);
  els.state.className = `pill ${toneForState(state.state)}`;
  setRawData(els.state, state.state);

  els.fault.textContent = faultText(state.fault_reason);
  els.fault.className = `pill ${state.fault_reason ? "is-bad" : "is-good"}`;
  setRawData(els.fault, state.fault_reason || "OK");

  els.lease.textContent = `${state.lease_remaining_ms} ms`;
  els.direction.textContent = label(labels.direction, state.active_direction || "none");
  setRawData(els.direction, state.active_direction || "none");

  const identity = label(labels.identity, state.h60.identity, "H60 链路");
  const scenario = label(labels.scenario, state.h60.scenario);
  els.serial.textContent = `${identity} / ${scenario}`;
  setRawData(els.serial, `${state.h60.identity} / ${state.h60.scenario}`);
  const isRealW2 = state.h60.scenario === "real_w2_field";
  els.armHint.textContent = isRealW2 ? "先申请，按住方向时板端使能" : "仅假链路";
  els.eyebrow.textContent = isRealW2 ? "W2 / 实板架空现场" : "W1.5 / 本机假串口";
  els.subtitle.textContent = isRealW2
    ? "真实 H60 已连接 · 只执行本次获批的架空方向 · 故障立即断电收尾"
    : "假 H60 离线链路 · 真实串口 / 使能 / 运动保持锁定";
  els.backendDescription.textContent = isRealW2 ? "真实 H60 / 仅本包" : "仅假 H60";
  els.deviceActionDescription.textContent = isRealW2 ? "受限架空方向" : "等待独立现场包";
  els.scenario.disabled = isRealW2;
  els.scenario.value = isRealW2 ? "normal" : state.h60.scenario;
  renderFieldGuide(state, isRealW2);

  const events = state.events.slice(-20).reverse();
  els.events.replaceChildren(...events.map(renderEvent));
}

function renderFieldGuide(state, isRealW2) {
  els.fieldGuide.hidden = !isRealW2;
  if (!isRealW2) {
    for (const id of ["#arm", "#forward", "#reverse"]) {
      document.querySelector(id).disabled = false;
    }
    return;
  }
  const allowed = state.h60.allowed_direction;
  const direction = label(labels.direction, allowed, "本阶段方向");
  const faulted = state.state === "FAULT" || state.h60.protocol_error || state.h60.fault;
  if (faulted) {
    if (activeHoldIntent) endHold();
    els.fieldStep.textContent = "故障已锁止：停止点击，关主开关并断开电池，在终端输入 ANOMALY。";
  } else if (state.state === "ARM_PENDING") {
    els.fieldStep.textContent = `申请已收到，板端仍失能。请在 5 秒内按住${direction}；网页约 0.3 秒自动停车。`;
  } else if (state.state === "ARMED") {
    els.fieldStep.textContent = `正在执行${direction}；网页会自动停车。松开后观察四轮并回终端确认。`;
  } else {
    els.fieldStep.textContent = `本阶段只测${direction}：先点一次“申请使能”，看到待按方向后再按住方向。自动停车后检查四轮，再回终端确认。`;
  }
  const reason = lastFieldResult?.reason;
  els.fieldFeedback.textContent = faulted
    ? "不要再点击申请或方向；完成物理断电与终端异常收尾。"
    : lastFieldResult && !lastFieldResult.accepted
    ? reason === "not_armed" || reason === "arm_request_expired"
      ? "这次方向请求没有执行；申请已过期，请重新申请后再按。"
      : `本次请求未执行：${label(labels.reason, reason, "故障或条件不满足")}`
    : "一次只做一个方向；若 5 秒内没按，重新申请。任何故障都不继续测试。";
  document.querySelector("#arm").disabled = faulted || state.state === "ARMED";
  for (const [id, intent, value] of [
    ["#forward", "FORWARD_LOW", "forward"],
    ["#reverse", "REVERSE_LOW", "reverse"],
  ]) {
    document.querySelector(id).disabled =
      faulted || allowed !== value || (state.state !== "ARM_PENDING" && activeHoldIntent !== intent);
  }
}

function renderEvent(event) {
  const li = document.createElement("li");
  const eventName = label(labels.event, event.event, "事件");
  const fields = Object.entries(event)
    .filter(([key, value]) => key !== "now_ms" && key !== "event" && value !== null)
    .map(formatField)
    .filter(Boolean);
  li.textContent = fields.length ? `${eventName}：${fields.join("；")}` : eventName;
  setRawData(li, event);
  return li;
}

function formatField([key, value]) {
  if (key === "frame_hex" && !value) return "";
  if (key === "client_id") return `${labels.field.client_id}=网页会话`;
  if (key === "ack") return `${labels.field.ack}=${value ? "是" : "否"}`;
  if (key === "sequence") return `${labels.field.sequence}=${value}`;
  if (key === "intent") return `${labels.field.intent}=${label(labels.intent, value)}`;
  if (key === "command") return `${labels.field.command}=${label(labels.command, value)}`;
  if (key === "reason" || key === "response_reason") {
    return `${labels.field[key]}=${label(labels.reason, value)}`;
  }
  if (key === "scenario") return `${labels.field.scenario}=${label(labels.scenario, value)}`;
  if (key === "state_after") return `${labels.field.state_after}=${label(labels.state, value)}`;
  if (key === "frame_hex") return `${labels.field.frame_hex}=已记录`;
  return `字段=${String(value)}`;
}

function renderSafety(safety) {
  els.safetyStatus.textContent = label(labels.safetyOverall, safety.overall);
  els.safetyStatus.className = toneForOverall(safety.overall);
  setRawData(els.safetyStatus, safety.overall);

  els.safetyMode.textContent = label(labels.mode, safety.mode);
  setRawData(els.safetyMode, safety.mode);

  els.liveState.textContent = label(labels.liveState, safety.live_physical_state);
  els.liveState.className = "pill is-warn";
  setRawData(els.liveState, safety.live_physical_state);

  els.nextGate.textContent = `${safety.next_gate.id} / ${label(labels.gateStatus, safety.next_gate.status)}`;
  setRawData(els.nextGate, safety.next_gate);

  els.safetyChecks.replaceChildren(
    ...safety.checks.map((check) => {
      const li = document.createElement("li");
      li.dataset.status = check.status;
      setRawData(li, check);

      const name = document.createElement("span");
      name.textContent = label(labels.check, check.id);

      const status = document.createElement("strong");
      status.textContent = label(labels.gateStatus, check.status);

      const reason = document.createElement("small");
      reason.textContent = label(labels.reason, check.reason);

      li.append(name, status, reason);
      return li;
    }),
  );

  els.allowedNow.textContent = joinActions(safety.allowed_now);
  els.prohibited.textContent = joinActions(safety.prohibited_actions);
  setRawData(els.allowedNow, safety.allowed_now);
  setRawData(els.prohibited, safety.prohibited_actions);
}

function joinActions(actions) {
  return actions.map((action) => label(labels.action, action, "未识别项")).join("、") || "无";
}

function beginHold(intent) {
  if (activeHoldIntent) return;
  const realW2 = currentState?.h60?.scenario === "real_w2_field";
  const expectedDirection = intent === "FORWARD_LOW" ? "forward" : "reverse";
  if (realW2 && (
    currentState.state !== "ARM_PENDING"
    || currentState.h60.allowed_direction !== expectedDirection
  )) return;
  activeHoldIntent = intent;
  sendIntent(intent, { refreshPanel: false });
  holdTimer = setInterval(() => sendIntent(intent, { refreshPanel: false }), 25);
  if (realW2) fieldStopTimer = setTimeout(endHold, FIELD_BROWSER_STOP_MS);
}

function endHold() {
  if (!activeHoldIntent) return;
  activeHoldIntent = null;
  if (holdTimer) {
    clearInterval(holdTimer);
    holdTimer = null;
  }
  if (fieldStopTimer) {
    clearTimeout(fieldStopTimer);
    fieldStopTimer = null;
  }
  sendIntent("STOP");
}

document.querySelector("#stop").addEventListener("click", () => sendIntent("STOP"));
document.querySelector("#disarm").addEventListener("click", () => sendIntent("DISARM"));
document.querySelector("#arm").addEventListener("click", () => sendIntent("ARM_REQUEST"));

for (const [id, intent] of [
  ["#forward", "FORWARD_LOW"],
  ["#reverse", "REVERSE_LOW"],
]) {
  const button = document.querySelector(id);
  button.addEventListener("pointerdown", () => beginHold(intent));
  button.addEventListener("pointerup", endHold);
  button.addEventListener("pointercancel", endHold);
  button.addEventListener("pointerleave", endHold);
}

els.scenario.addEventListener("change", async () => {
  const payload = await post("/api/fake_serial/scenario", {
    scenario: els.scenario.value,
  });
  render(payload.state);
  await refreshSafety();
});

window.addEventListener("beforeunload", () => {
  navigator.sendBeacon(
    "/api/disconnect",
    new Blob([JSON.stringify({ client_id: clientId })], {
      type: "application/json",
    }),
  );
});

setInterval(refresh, 120);
refresh();
