# 无 Orin 本机安全控制台

这是 Project0 在最终上位机不可用期间使用的 localhost-only 控制核心公开版。当前公开入口只连接 `FakeH60Serial`，不会枚举或打开真实串口。

```text
Browser -> 127.0.0.1 HTTP backend -> WebTeleopController -> FakeH60Serial
```

## 能力

- STOP、DISARM、ARM 请求、低速前进/后退意图；
- 客户端单调序号与旧请求拒绝；
- 浏览器断开、租约超时、主循环迟到时 fail-closed；
- 故障锁止、身份漂移、遥测超时及 CRC/长度/序号错误注入；
- localhost 绑定限制、JSONL 审计失败时强制 STOP；
- 中文安全状态面板和当前允许/禁止动作提示。

## 运行离线演示

```bash
PYTHONPATH=src/p0_base_bridge:tools/no_orin_web_teleop \
python3 tools/no_orin_web_teleop/run_w0_server.py
```

然后打开 `http://127.0.0.1:8765/`。页面中的运动只是 fake serial 状态机演练。

## 测试

```bash
PYTHONPATH=src/p0_base_bridge:tools/no_orin_web_teleop \
python3 -m unittest discover -s tools/no_orin_web_teleop/tests -p 'test_*.py' -v

node tools/no_orin_web_teleop/tests/test_field_ui.mjs
```

## 安全说明

公开版不包含真实设备身份、一次性现场包、运行授权或真实串口适配器。不要把 fake serial 通过、网页可用或历史 H60-only 证据解释为真实车辆运动准入。
