# H60 safe-control firmware

> 2026-09-04本次：MA-minus0.2.6已完成一次官方写入/校验及刷前、刷后各512KiB独立读取。刷前匹配MA-plus0.2.5；刷后新BIN一致、首扇区余部FF、其他扇区不变，实际全片SHA2452a717…通过。串口已关闭，冷启动通信/反向短测尚未执行；本次拔DEBUG/关主开关/断电池收尾待反馈，M2/H6未通过。 详见慢衰减35.2。

> 2026-09-04当前：用户回复“声音没听。其他正常”，按本次清单确认MA试转实际停车、紧固及拔COM/关主开关/物理断开电池收尾正常；声音记NOT_OBSERVED，不写无异常声音。MA/plus/8%后转、净−175与数字停车通过的证据保持。下一同右前/同好线/同MA口的minus8%独立候选正在纯数字准备，尚未完成执行包、未获新包批准、未刷写或开窗口，M2/H6未通过。 详见慢衰减34.9。

> 2026-09-04当前：MA恢复空口检查与唯一8%短测数字通过，用户报告右前轮向后转动；MA净计数−175，其余三路0，最终失能/零增量且串口关闭。本次声音、物理停车、紧固及拔COM/关主开关/断电池收尾尚待回复，不能沿用测试前确认。原10533首片段CRC失败保留；恢复303和原MA唯一运动均已消费，不重开或重复试转，M2/H6未通过。 详见慢衰减34.8。

> 2026-09-04当前：用户已确认拔COM/DEBUG、关主开关、断电池且无异常，并报告板上无接线，随后再次要求继续。一次恢复已激活，121项恢复冻结/122项后续冻结通过；原107项及空口失败保留。接线提示不再假定好线电机端位置；新空口通过后，完全断电下用同一根已验证右前好线连接右前与MA，真实回车后唯一短测。新窗口状态以实际记录为准，M2/H6未通过。 详见慢衰减34.7。

> 2026-09-03当前：MA窗口10533在空口原始流CRC核验处停止，未进入运动：仅1 STOP、46连续安全遥测与有效ACK，串口关闭；首46字节残片不满足既定补头CRC规则，原失败保留。未发ARM/驱动，MA固件与完整回读仍有效。本次收尾/实际接线待确认；同固件同审核的一次恢复入口已准备、尚未批准或打开，M2/H6未通过。 详见慢衰减34.6。

> 2026-09-03最新：右后C同MC/同好线手拨净+3934，350安全帧/零发送/关闭，用户无异常及完整断电收尾确认；右后原线束总成按不可靠件停用，具体坏点未分离。本轮A/B/C收束；MC0.2.4固定8%独立候选离线就绪、整包未批准未刷写，板内仍MD0.2.3。见慢衰减32.2–33，M2/H6与风险等级保持。

> 最新（慢衰减31.1–32）：同MC已知右前整组+3001、349安全帧/零发送/关闭通过，用户无异常/断电拔线确认，MC读取能工作；下一右后C保持MC和右前整线、只换电机端，已准备未打开。具体坏点未分离，M2/H6和风险等级保持。

> 最新（慢衰减30.4–31）：右后MC提示后实拨一圈仍全零，349安全帧、初始丢弃39字节、零发送/关闭通过，用户无异常及断电拔线确认；下一同MC接已验证右前整组只读分离通路，未判具体坏件，M2/H6与风险等级保持。

> 最新（慢衰减30.3）：用户确认右后MC实拨/无异常/已断电但手拨时序不明；旧全零不判故障。修正窗口Terminal7714已打开，提示后手拨，零发送、不刷写，实际新结果待读取。M2/H6及风险等级保持。

> 最新（慢衰减30.2）：MC349帧全零、零发送/关闭通过，但首段提示漏显且曾发出暂停提醒，实拨/配置/收尾待用户补明，不能判硬件故障。提示已在新未开入口修复，旧证据保留，M2/H6保持。

> 最新（慢衰减30.1）：右前无异常补充已确认、完整收尾；右后MC原线束只读30秒窗口Terminal7641已打开，零发送、不刷写，实际配置/结果待真实回车与采集。M2/H6及风险等级保持。

> 最新（慢衰减29.1–30）：右前MA手拨净+3114、349帧安全遥测/零发送/关闭通过，用户已断电拔线，异常项尚未填明；右后MC只读包已准备未打开。驱动/CPR/M2/H6及风险等级不提升。

> 最新（慢衰减28.2–29/P2-E095）：左后未手拨/向前−112/正常停车/无异常/断电拔线已确认，本轮收束；下一右前原线束接MA的30秒只读手拨，零发送、不刷写。新实体配置/样本待实际窗口，风险等级与M2/H6保持。

> 最新实际结果（慢衰减28.1/P2-E094）：左后第二次报告向前、MD净−112，其他三路0，数字停车通过；本次未手拨/现场停车/异常/断电拔线待统一补充。旧窗口不可重开，风险等级和M2/H6保持。

> 下一活动包（慢衰减28/P2-E094）：左后同MD/已验证线束，不手拨，冷启动一次8%/600ms自然停位检查；已完成数字准备，实际结果待执行。固件/保护/风险等级及M2/H6保持。

> 最新实际结果（慢衰减27.3/P2-E093）：左后换线后MD/plus/8%驱动，用户报告向前，MD净−138，其余三路0，通信/数字停车通过。用户按整包清单回复“一切正常”，本次正常停车/无异常/断电拔线已确认；与旧向后记录的差异未解，M2/H6及风险等级保持，禁止重开已消费入口。

> 最新入口：旧6413未开串口即超时；新窗口6640对应md_feedback_reopen__z8whpig，同参数同固件，已打开不可重开。

> 当前入口（慢衰减27）：Terminal6413为换用C线束后的单MD8%反馈验证；板内0.2.3/原候选不变，无需刷写。使用本次md_feedback_known_cable_fra_6bj7入口，已经打开，不能重开；首快照无新实测结果。

> 最新C（慢衰减26/P2-E092）：更换B已验证线束后的只读采集取得MD净−4261，349帧安全遥测/零发送/串口关闭。用户已确认手拨1圈多一点、断电拔线且无异常；原线束/接触为优先调查对象，未判具体坏件，固件和M2/H6边界保持。

> 最新反馈对照：左前接MD手拨取得−2603，说明当前0.2.3的MD读取路径能够工作；C只换左后电机、沿用已验证线束的只读检查待新任务恢复。固件不变。见[慢衰减25](../../docs/06_testing/p2_m2a_slowdrive_offline_verification_2026-09-02.md)。


> B只读对照已获新确认并打开Terminal 5170；板内0.2.3保持。只用本次B入口，待实际结果。见[慢衰减24.3](../../docs/06_testing/p2_m2a_slowdrive_offline_verification_2026-09-02.md)。


> 当前反馈诊断：左后实际手拨后350帧全零；B尚未测。板内0.2.3保持，B单独30秒零发送入口仅准备。见[慢衰减24.2](../../docs/06_testing/p2_m2a_slowdrive_offline_verification_2026-09-02.md)。


> 历史只读诊断窗口（已结束）曾改为30秒手拨复测（Terminal 4928），固件不变，旧Terminal4812已停止。见[慢衰减24.1](../../docs/06_testing/p2_m2a_slowdrive_offline_verification_2026-09-02.md)。


> 最新MD实体结果：8%明显向后，但四路编码器全零。源码计数通道审查未见明确遗漏，保持0.2.3固件并改做零发送手拨对照。见[慢衰减第24节](../../docs/06_testing/p2_m2a_slowdrive_offline_verification_2026-09-02.md)。


> 当前板内为0.2.3-M2A-SLOW5K-MD-PLUS-80-R1，单MD固定8%；官方写入及独立完整回读已通过。只用md80_offline_fro5qpog/candidate及当前连续入口，本次实体结果见上方第24节。见[慢衰减第23节](../../docs/06_testing/p2_m2a_slowdrive_offline_verification_2026-09-02.md)。

> 2026-09-03 历史MB状态（已由MD取代）：已批准并刷入0.2.2-M2A-SLOW5K-MB-PLUS-80-R1，完整独立回读通过。本目录生产源码/profile仍保留5%0.2.1；此前MB使用冻结的slow80_offline_9m8bwf2z/candidate，不从本目录默认构建或旧主机推断当前板内身份。8%三次明确向前、净−252/−254/−271且通信/STOP通过，仅作为当前左前架空暂定基线，完整可靠性未关闭；实际结果见[慢衰减第21节](../../docs/06_testing/p2_m2a_slowdrive_offline_verification_2026-09-02.md)。

> 2026-09-03历史5%观察：慢衰减0.2.1两次同参单左前MB/plus/5%数字命令/STOP通过：首次未见轮转、净+1；第二次明显向前、净−113，用户已断电且无异常。用户确认两次间拨过左前轮；当前优先解释起转差异、沿用慢衰减候选完善，暂停其他轮。起转可靠性/唯一根因及M2/H6未关闭，无第三次授权。 见 [实现与验证](../../docs/06_testing/p2_m2a_slowdrive_offline_verification_2026-09-02.md)。下文原0.2.0条目保留对应历史范围。

This directory contains the first Project0-owned firmware for the OpenCTR H60
V3.7 / STM32F407VET6.

## Safety status

2026-09-02 最新更正：用户说明 12.10 V 是口误，实际报告断电 0 V、上电约 0 V。
只记录约零定性观察，不补写精确值/容差 PASS，不继续对撤回数值排故。
最新入口见M2-A18.45/18.46：用户取消左后旁支，回到左前未动；独立MB12%候选34项离线通过但未授权真实运行。仓库原控制台SHA8feb7e2c…和板上M2A5K-R1不变，候选仅在仓库外，未烧录或接设备。
查到20kHz/5%高电平仅2.5us，不满足AT8236至少5us唤醒要求；M2-A专用载波改5kHz，非零范围收窄50–120‰、最低高10us，零释放/单通道/75ms/1s与主机5%/600ms限制不变，默认/审计20kHz不改。
新5456字节候选`build/m2a-pwm-wake/arm/p0_h60_safe_control.bin`，SHA-256 `4dbf1d10ae460ea2856f79175b001c7cc4e0b23b4e59572c68fa4ab4070a8a8c`，manifest `PWM=M2A5K-R1;MIN_DUTY=50`；6组C、7项源码、22项主机、11项ROM、两个错误构建门、两组相关内存安全及两种ARM构建通过。默认BIN逐字节不变。
最新18.25已将5456字节M2A5K-R1写入并官方验证、独立512KiB回读通过，完整SHA `f1f7c3ac28e86273dc0fb4a2e8f7b84660873f97985c9df9100abaa4d52314c7`；前缀/sector0尾部/其他区域检查通过，串口关闭。旧IRQ256-R1/原M2-A/v0.1.1回滚保留。18.27新固件冷启动与120心跳/3 STOP ACK/25帧安全遥测通过，串口关闭；18.28单次真实回车短测已完成，18.29数字PASS；18.30用户确认未动、断电及USB拔除，异常/紧固反馈已按用户“无”收束。

仅M1/MB已接时的静止检查使用独立 `tools/m2a_mb_passive_check.py`，不发送任何命令；6项伪串口测试通过。本次已按第18.8节确认执行，结果与可用Python运行时见第18.9节；不自动重跑。

无电机通信复验入口是 `tools/m2a_no_motor_recheck.py`，不是会自动 ARM 的校准控制台。
它要求当前 COM 身份及无电机确认，按 1 秒接入/3 秒正式窗口保留完整原始流；
所有阶段 CRC/状态/序号异常均停止，唯一发送命令为一次 STOP，随后关闭串口。
运行前按 M2-A 包第 13 节确认现场；17 项离线测试通过不代表实体复验通过。

The H60 board now contains the dedicated `0.2.0-M2A` one-channel calibration
image. On 2026-09-02, official download/verify and an independent full 512-KiB
readback passed with MA-MD disconnected. A subsequent no-motor communication
recheck passed: 47 consecutive safe telemetry frames, no parser errors or
discarded bytes, and one successful STOP acknowledgement. The earlier failed
receive-prefix capture is preserved. The user subsequently reported approximately
zero static DMM output; this is qualitative evidence, not exact per-channel data.
用户已在新任务确认断电收好；约零定性观察不升级为完整电气 PASS。
ARM, motor connection and motion are not authorized by this result. The
physically validated `v0.1.1-safe-bringup` image remains available for rollback.
The separate `0.2.0-M1` offline motion design has not been flashed.

The default `0.2.0-M1` build remains intentionally motion locked:

- `P0_MOTION_OUTPUT_COMPILED=0` and `P0_MOTION_CALIBRATION_VALID=0`;
- no PWM peripheral is configured by the default build;
- during early application initialization, all eight H-bridge input pins are
  latched low before being configured as GPIO outputs;
- ARM is rejected with `P0_STATUS_MOTION_LOCKED`;
- application initialization, protocol error, sequence rollback, timeout,
  local fault, assertion and Cortex-M exception paths call the same motor-safe
  primitive first.

An explicit `motion-audit-firmware` target compiles the guarded PWM path only
to prove that it builds for ARM. Its calibration gate is still zero, so it also
rejects ARM. A normal motion-enabled build and every calibration-valid build
are compile-time errors in M1.

Neither M1 artifact is approved for flashing, motor connection or motion.

An explicit `m2a-calibration-firmware` target is the only build that can ARM
before real vehicle calibration exists. It is isolated from the M1 closed-loop
controller and hard-limited to one MA-MD channel, 120 permille duty, a 75 ms
non-zero hold lease and a 1000 ms absolute armed session. Invalid commands,
lease/session expiry and every existing fail-safe path clear the output. The
companion `tools/m2a_calibration_console.py` adds an 850 ms host limit, explicit
port/artifact/hash checks and a repeated-space deadman input.

This is a reviewed digital preparation path, not general motion enablement.
Its build, flash/readback/rollback sequence and suspended one-channel test plan
are recorded in
`../../docs/06_testing/p2_m2a_h60_single_channel_calibration_package_2026-09-02.md`.
It must not be flashed or run without a fresh physical-state review and the
user's explicit per-run authorization.

## Bring-up status

- v0.1.0 was flashed and independently read back, but its first cold-start
  bring-up produced no USB-COM telemetry because IWDG initialization waited for
  update flags before the start key had forced the LSI clock on.
- v0.1.1 starts IWDG first, bounds the update wait and retains the same
  compile-time motion lock. It has been flashed, officially verified,
  independently read back and cold-started with all motors disconnected.
- Cold-start telemetry reported `0.1.1`, `DISARMED`, no fault, self-test passed,
  motion output unavailable and boot fault code zero. STOP was acknowledged;
  ARM was rejected with `P0_STATUS_MOTION_LOCKED`; final state remained
  `DISARMED`.
- The user measured `0 V` differential output on MA-MD, both unpowered and
  powered, using a motor-disconnected cable as a test extension. This is a
  no-load DMM observation rather than a waveform or loaded-output test.
- The validated factory image is stored outside Git; its path and SHA-256 are
  recorded in `BUILD_RECORD_2026-08-22.md`.

## Protocol

All multi-byte fields are little-endian.

```text
A5 5A | version | type | payload_len:u16 | session:u32 | seq:u32 |
payload[0..48] | crc32:u32
```

CRC is CRC-32/IEEE over `version` through the end of payload. Maximum payload
length is 48 bytes. Commands include heartbeat, ARM, DISARM, STOP, wheel target
and clear-fault. STOP and DISARM are fail-safe commands and always zero outputs
after a structurally and cryptographically valid frame is received.

## Build

The build has no source dependency on the vendor example. It uses Project0
register definitions and the GNU ARM Embedded toolchain bundled with
STM32CubeIDE.

```bash
make test
make firmware
make verify
make motion-audit-firmware
make m2a-verify
```

`make verify` builds the default `MOTION=0 / CAL=0` image and proves that a
non-audit `MOTION=1` build is rejected. `make motion-audit-firmware` produces a
separate ignored artifact with `MOTION=1 / CAL=0`; it is for offline inspection
only and remains runtime locked. `make m2a-verify` builds and verifies the
separate `MOTION=1 / CAL=0 / M2A=1` one-channel candidate; it does not authorize
flashing or physical execution.

Override the compiler when required:

```bash
make firmware ARM_GCC=/absolute/path/to/arm-none-eabi-gcc
```

Outputs are written to `build/` and are ignored by Git.

## Read-only factory backup

`tools/stm32_uart_bootloader.py` contains only the STM32 ROM operations needed
to identify the MCU and read flash. It has no erase, write, unprotect,
option-byte or execution command. The backup path must not already exist. A
512-KiB image is accepted only after chip-ID, length, non-blank content, initial
stack pointer and reset-vector checks pass.

Run its offline tests with:

```bash
make bootloader-test
```

The physical probe and backup require VIN and USB-DEBUG while all four motor
cables remain disconnected. The exact hardware command is issued only inside
the approved, supervised bring-up procedure.

## Current limitations

- the M1 source contains guarded 20 kHz paired-input PWM, configurable encoder
  speed estimation, PI control, limits, anti-windup, ramping and reversal zero
  hold, but all real vehicle calibration values remain invalid;
- the M2-A source can bootstrap direction/count-sign facts only; it does not
  measure CPR, tune the closed loop or establish production motion readiness;
- MA-MD to physical-wheel mapping, Motor +/- direction, encoder polarity, CPR,
  wheel circumference and safe control gains/limits are not frozen;
- VIN conversion is an uncalibrated nominal estimate (`3.3 V`, divider `11:1`);
- UART single-side power and backfeed behavior still requires physical testing;
- no-output waveform verification, loaded-output behavior and hardware fault
  injection have not been performed;
- motor connection and motion remain prohibited until the M2-A package is
  separately reviewed and explicitly authorized for that physical run.

The complete M1 scope, test vectors, build hashes and M2 boundary are recorded
in
`../../docs/06_testing/p2_m1_h60_motion_firmware_offline_verification_2026-09-02.md`.

## M2-A 回车单次观察模式（2026-09-02）

`tools/m2a_calibration_console.py --trigger-mode one-shot`要求独立`--approval-code M2A-ONE-SHOT-REVIEWED`，最多50‰及ARM起算600 ms。真实终端回车后固定3秒倒计时，之前不打开设备；无需空格。任意后续键、终端退出、通信/状态异常或50 ms发送间隔异常停止；固件75 ms/1 s硬限制不改。旧hold-space保持默认及原批准码。两个模式都只运行一次，不能把数字测试通过作为新实体运行结果。

第18.14现场包已经执行失败，禁止重用；18.18新固件刷写回读通过，当前18.19仅冷启动与无电机双向通信。新增m2a_uart_duplex_check.py（4项离线测试），只发心跳/STOP，120ACK逐条20ms内确认及失能收尾；旧STOP-only工具不变，未实际运行新通信工具。

### MB80单次配置

用户已授权的一次MB/plus/80‰/600ms使用`--trigger-mode one-shot --one-shot-profile mb-plus-80`和独立批准标识；standard-50默认仍限50‰。28项离线测试通过，控制台SHA `8feb7e2cbbe08e95e46e699d8a3b4906cfd282d61e466bbc0f37fcbee076a1f1`；真实回车/3秒倒计时/一次ARM/所有故障STOP不变。入口、实体前置和收尾以M2-A18.32为准；板上固件未改，不自动重试或提高下一档。

## 左前慢衰减独立候选

纯离线入口为 `make slowdrive-test` 与 `make m2a-slowdrive-firmware`；默认关闭 `P0_M2A_SLOWDRIVE_BUILD`，新制品写入 `build/m2a-slowdrive/arm/`，不覆盖旧M2A5K-R1。独立主机配置为 `--one-shot-profile mb-plus-50-slow5k-r1`，必须单次MB/plus/50‰、最长600ms、精确新版本/BIN散列和独立 `--run-approval`；一次调用即消费入口。当前没有真实批准文件或刷写/运行授权，完整依据以候选验证记录为准。

## 2026-09-03 只读起转记录审查

已完成直接相关自主离线工作：新增只读M2-A日志审查器及21项测试，补充真实主循环3组/硬件模型12组STOP后重复启动回归；合计25项测试方法通过。四份旧实测重算与原记录一致，旧快衰减5%/8%均0，慢衰减首次为小幅往返净+1、次轮连续负计数净−113。未发现第二次自动加强输出的软件路径；位置相关起转假设仍未作因果确认。

`tools/m2a_run_review.py`接收一个或多个已结束的m2a_run目录，只读result.json/serial.jsonl并输出JSON，不打开设备。它报告日志一致性、计数形态与连续区间，物理起转/方向/停车始终NOT_ASSESSED；不能由数字PASS自动推进现场门。测试入口为`tests/test_m2a_run_review.py`，重复启动回归并入现有慢衰减测试。详见慢衰减验证第14节。生产固件/控制台和板上制品不变，下一现场对照仅为草案、尚未批准。

### 2026-09-03 主机校准控制台截止修复

m2a_calibration_console.py在会话剩余时间不超过20ms时停止发送新的HEARTBEAT/HOLD，保留原ACK超时和按时STOP；避免截止前刚发出的正常命令被立即判未确认。6项针对性回归及原主机/慢衰减总40项通过，含真实PTY伪设备。固件未重新构建/刷写，原A实测FAIL保留；新的连续位置对照与真实回车/异常停止见慢衰减验证第17节，实体起转仍未通过。

### 2026-09-04 MA-minus0.2.6刷写后执行点

板内MA-minus0.2.6已由全片回读确认；用户已批准右前MA/minus/80‰/5kHz/主机会话设置600ms唯一短测。130项运行冻结通过，Terminal 3915已打开且停在四口全空COM冷启动真实回车门。此时尚未打开COM、发送STOP/ARM/HOLD或取得运动结果；一次性入口已消费，不得重开或自动重试。保留默认旧5%源与板内候选的差异，M2/H6未通过。

### 2026-09-04 MA-minus实际短测收束

唯一MA/minus/80‰运行已完成：MA净`+193`、其余三路0，STOP确认，最终DISARMED/零增量/无故障且串口关闭。用户确认胎顶向车头，声音/停止/支撑紧固无异常，并完成COM拔除、主开关关闭与电池物理断开。该结果只记录当前右前组合下minus=向前/正计数，不把板内隔离候选合并回默认生产源，不证明其他通道或M2/H6完成。窗口和入口已消费，禁止重开/补跑。
