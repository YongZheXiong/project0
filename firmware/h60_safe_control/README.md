# H60 safe-control firmware v0.1

This directory contains the first Project0-owned firmware for the OpenCTR H60
V3.7 / STM32F407VET6.

## Safety status

`v0.1.1-safe-bringup` is intentionally motion locked:

- `P0_MOTION_OUTPUT_COMPILED` is fixed to `0` in the production build;
- no PWM peripheral is configured;
- during early application initialization, all eight H-bridge input pins are
  latched low before being configured as GPIO outputs;
- ARM is rejected with `P0_STATUS_MOTION_LOCKED`;
- application initialization, protocol error, sequence rollback, timeout,
  local fault, assertion and Cortex-M exception paths call the same motor-safe
  primitive first.

The produced firmware completed its first approved motor-disconnected backup,
flash and bring-up sequence. It is not approved for motor connection or motion.

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
- The validated factory image is not distributed in this repository; the
  checked-in source and build steps are the reproducible public artifact.

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
```

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

- motor PWM and closed-loop speed control are intentionally absent;
- VIN conversion is an uncalibrated nominal estimate (`3.3 V`, divider `11:1`);
- encoder direction, CPR, gear ratio and wheel mapping are not frozen;
- UART single-side power and backfeed behavior still requires physical testing;
- no-output waveform verification, loaded-output behavior and hardware fault
  injection have not been performed;
- motor connection and motion remain prohibited.
