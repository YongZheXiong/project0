import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import vm from "node:vm";

const root = resolve(process.env.W2_UI_ROOT ?? resolve(import.meta.dirname, ".."));
const source = readFileSync(resolve(root, "static/app.js"), "utf8");
const html = readFileSync(resolve(root, "static/index.html"), "utf8");
for (const id of ["field-guide", "field-step", "field-feedback", "mode-eyebrow"]) {
  assert.match(html, new RegExp(`id="${id}"`));
}

class Element {
  constructor() {
    this.dataset = {};
    this.listeners = {};
    this.hidden = false;
    this.disabled = false;
    this.textContent = "";
  }
  addEventListener(name, callback) { this.listeners[name] = callback; }
  replaceChildren(...children) { this.children = children; }
  append(...children) { this.children = children; }
}

const elements = new Map();
const timers = new Map();
const intents = [];
let timerId = 0;
const realState = {
  state: "ARM_PENDING", fault_reason: null, lease_remaining_ms: 4000,
  active_direction: null, events: [],
  h60: {
    scenario: "real_w2_field", identity: "H60-COM", allowed_direction: "forward",
    protocol_error: null, fault: false,
  },
};
const document = {
  querySelector(selector) {
    if (!elements.has(selector)) elements.set(selector, new Element());
    return elements.get(selector);
  },
  createElement() { return new Element(); },
};
const context = vm.createContext({
  document,
  window: { addEventListener() {} },
  navigator: { sendBeacon() {} },
  Blob,
  Math,
  fetch(path, options) {
    if (options?.method === "POST") {
      intents.push(JSON.parse(options.body).intent);
      return Promise.resolve({ json: async () => ({
        result: { accepted: true, reason: "stop" }, state: realState,
      }) });
    }
    return new Promise(() => {});
  },
  setInterval(callback, delay) {
    const id = ++timerId;
    timers.set(id, { callback, delay, kind: "interval" });
    return id;
  },
  clearInterval(id) { timers.delete(id); },
  setTimeout(callback, delay) {
    const id = ++timerId;
    timers.set(id, { callback, delay, kind: "timeout" });
    return id;
  },
  clearTimeout(id) { timers.delete(id); },
});
vm.runInContext(source, context);
context.realState = realState;
vm.runInContext("render(realState)", context);
assert.equal(elements.get("#field-guide").hidden, false);
assert.equal(elements.get("#forward").disabled, false);
assert.equal(elements.get("#reverse").disabled, true);
assert.match(elements.get("#field-step").textContent, /5 秒内按住前进/);

elements.get("#forward").listeners.pointerdown();
assert.deepEqual(intents, ["FORWARD_LOW"]);
const stopTimer = [...timers.values()].find((timer) => timer.kind === "timeout");
assert.equal(stopTimer.delay, 300);
stopTimer.callback();
assert.deepEqual(intents, ["FORWARD_LOW", "STOP"]);
assert.equal([...timers.values()].filter((timer) => timer.kind === "interval").length, 1);
elements.get("#forward").listeners.pointerup();
assert.deepEqual(intents, ["FORWARD_LOW", "STOP"]);

const faultState = {
  ...realState, state: "FAULT", fault_reason: "host limit",
  h60: { ...realState.h60, protocol_error: "host limit" },
};
context.faultState = faultState;
vm.runInContext("render(faultState)", context);
assert.equal(elements.get("#forward").disabled, true);
assert.equal(elements.get("#arm").disabled, true);
assert.match(elements.get("#field-step").textContent, /断开电池.*ANOMALY/);
assert.match(elements.get("#field-feedback").textContent, /不要再点击/);

const fakeState = {
  ...realState, state: "DISARMED",
  h60: { ...realState.h60, scenario: "normal", allowed_direction: null },
};
context.fakeState = fakeState;
vm.runInContext("render(fakeState)", context);
assert.equal(elements.get("#field-guide").hidden, true);
assert.equal(elements.get("#forward").disabled, false);
console.log("field UI guidance, auto STOP and fault lock: PASS");
