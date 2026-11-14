SHELL := /bin/sh

PROJECT := p0_h60_safe_control
BUILD := build
HOST_BUILD := $(BUILD)/host
ARM_BUILD := $(BUILD)/arm

COMMON_SRC := src/p0_crc32.c src/p0_protocol.c src/p0_control.c \
	src/p0_motion.c src/p0_motion_scheduler.c src/p0_m2a_calibration.c \
	src/p0_uart_rx.c src/p0_m2a_slowdrive.c \
	src/p0_iwdg_diagnostic.c src/p0_usb_quiet.c src/p0_usb_motion.c
ARM_SRC := $(COMMON_SRC) src/p0_runtime.c src/p0_manifest.c \
	src/p0_hw_stm32f407.c src/main.c
ifneq ($(filter -DP0_USB_MANUAL_BUILD=1,$(ARM_DEFINES)),)
ARM_SRC += src/p0_usb_manual.c
endif
ARM_ASM := src/startup_stm32f407.S

HOST_CC ?= cc
HOST_CFLAGS := -std=c11 -O2 -g -Wall -Wextra -Werror -pedantic -Iinclude

ARM_GCC ?= $(shell command -v arm-none-eabi-gcc 2>/dev/null)
ifeq ($(strip $(ARM_GCC)),)
ARM_GCC := arm-none-eabi-gcc
endif
ARM_BIN_DIR := $(dir $(ARM_GCC))
ARM_OBJCOPY := $(ARM_BIN_DIR)arm-none-eabi-objcopy
ARM_SIZE := $(ARM_BIN_DIR)arm-none-eabi-size
ARM_OBJDUMP := $(ARM_BIN_DIR)arm-none-eabi-objdump
ARM_STRINGS := $(ARM_BIN_DIR)arm-none-eabi-strings

ARM_CPU := -mcpu=cortex-m4 -mthumb -mfloat-abi=soft
ARM_DEFINES ?= -DP0_TARGET_STM32F407=1 \
	-DP0_MOTION_OUTPUT_COMPILED=0 \
	-DP0_OFFLINE_MOTION_AUDIT_BUILD=0 \
	-DP0_MOTION_CALIBRATION_VALID=0 \
	-DP0_M2A_CALIBRATION_BUILD=0 \
	-DP0_M2A_SLOWDRIVE_BUILD=0 \
	-DP0_H6_CHARACTERIZATION_BUILD=0 \
	-DP0_H6_EXTENDED_WINDOW_BUILD=0 \
	-DP0_W2_FOUR_WHEEL_PROFILE_BUILD=0 \
	-DP0_IWDG_DIAGNOSTIC_BUILD=0
ifneq ($(filter -DP0_USB_MOTION_TRACE_BUILD=1,$(ARM_DEFINES)),)
ARM_SRC += src/p0_usb_motion_trace.c
endif
ifneq ($(filter -DP0_USB_LINK_RECOVERY_BUILD=1,$(ARM_DEFINES)),)
ARM_SRC += src/p0_usb_link_recovery.c
endif
ifneq ($(filter -DP0_USB_RX_DIAG_BUILD=1,$(ARM_DEFINES)),)
ARM_SRC += src/p0_usb_diag.c
endif
ARM_CFLAGS := $(ARM_CPU) -std=c11 -Os -g0 -Wall -Wextra -Werror \
	-ffreestanding -fno-builtin -fdata-sections -ffunction-sections \
	-fno-unwind-tables -fno-asynchronous-unwind-tables -Iinclude \
	$(ARM_DEFINES)
ARM_LINKER ?= linker/stm32f407vetx.ld
ARM_LDFLAGS := $(ARM_CPU) -nostdlib -Wl,--gc-sections -Wl,-z,noexecstack \
	-Wl,-Map=$(ARM_BUILD)/$(PROJECT).map \
	-T$(ARM_LINKER)

ifneq ($(filter -DP0_USB_RX_DIAG_BUILD=1,$(ARM_DEFINES)),)
ARM_LDFLAGS += -Wl,--require-defined=__p0_diag_layout
endif

HOST_TEST := $(HOST_BUILD)/test_safe_control
MOTION_TEST := $(HOST_BUILD)/test_motion_control
MOTION_SCHEDULER_TEST := $(HOST_BUILD)/test_motion_scheduler
MOTION_INTEGRATION_TEST := $(HOST_BUILD)/test_motion_integration
MOTION_MAIN_TEST := $(HOST_BUILD)/test_motion_main
M2A_TEST := $(HOST_BUILD)/test_m2a_calibration
UART_TEST := $(HOST_BUILD)/test_uart_rx
UART_MAIN_TEST := $(HOST_BUILD)/test_uart_main
PWM_TIMING_TEST := $(HOST_BUILD)/test_pwm_timing
IWDG_DIAGNOSTIC_TEST := $(HOST_BUILD)/test_iwdg_diagnostic
ARM_ELF := $(ARM_BUILD)/$(PROJECT).elf
ARM_BIN := $(ARM_BUILD)/$(PROJECT).bin
ARM_HEX := $(ARM_BUILD)/$(PROJECT).hex
ARM_LIST := $(ARM_BUILD)/$(PROJECT).list

.PHONY: all test bootloader-test source-safety-test sanitize firmware \
	motion-audit-firmware m2a-calibration-firmware m2a-verify \
	motion-lock-test iwdg-diagnostic-firmware verify clean toolchain

all: test firmware verify

test: $(HOST_TEST) $(MOTION_TEST) $(MOTION_SCHEDULER_TEST) $(MOTION_INTEGRATION_TEST) $(MOTION_MAIN_TEST) $(M2A_TEST) $(UART_TEST) $(UART_MAIN_TEST) $(PWM_TIMING_TEST) $(IWDG_DIAGNOSTIC_TEST)
	$(HOST_TEST)
	$(MOTION_TEST)
	$(MOTION_SCHEDULER_TEST)
	$(MOTION_INTEGRATION_TEST)
	$(MOTION_MAIN_TEST)
	$(M2A_TEST)
	$(UART_TEST)
	$(UART_MAIN_TEST)
	$(PWM_TIMING_TEST)
	$(IWDG_DIAGNOSTIC_TEST)

$(IWDG_DIAGNOSTIC_TEST): tests/test_iwdg_diagnostic.c \
	src/p0_iwdg_diagnostic.c include/p0_iwdg_diagnostic.h include/p0_hw.h | $(HOST_BUILD)
	$(HOST_CC) $(HOST_CFLAGS) tests/test_iwdg_diagnostic.c \
		src/p0_iwdg_diagnostic.c -o $@

$(PWM_TIMING_TEST): tests/test_pwm_timing.c src/p0_m2a_calibration.c \
	include/p0_pwm_timing.h include/p0_m2a_calibration.h | $(HOST_BUILD)
	$(HOST_CC) $(HOST_CFLAGS) \
		-DP0_MOTION_OUTPUT_COMPILED=1 -DP0_M2A_CALIBRATION_BUILD=1 \
		tests/test_pwm_timing.c src/p0_m2a_calibration.c -o $@

bootloader-test:
	python3 -m unittest -v tests/test_stm32_uart_bootloader.py
	python3 -m unittest -v tests/test_m2a_calibration_console.py

source-safety-test:
	python3 -m unittest -v tests/test_firmware_source_safety.py

sanitize: | $(HOST_BUILD)
	$(HOST_CC) $(HOST_CFLAGS) -fsanitize=address,undefined \
		tests/test_safe_control.c $(COMMON_SRC) \
		-o $(HOST_BUILD)/test_safe_control_sanitize
	$(HOST_BUILD)/test_safe_control_sanitize
	$(HOST_CC) $(HOST_CFLAGS) -fsanitize=address,undefined \
		tests/test_motion_control.c src/p0_motion.c \
		-o $(HOST_BUILD)/test_motion_control_sanitize
	$(HOST_BUILD)/test_motion_control_sanitize
	$(HOST_CC) $(HOST_CFLAGS) -fsanitize=address,undefined \
		tests/test_motion_scheduler.c src/p0_motion_scheduler.c \
		-o $(HOST_BUILD)/test_motion_scheduler_sanitize
	$(HOST_BUILD)/test_motion_scheduler_sanitize
	$(HOST_CC) $(HOST_CFLAGS) -fsanitize=address,undefined \
		tests/test_motion_integration.c src/p0_control.c src/p0_motion.c \
		src/p0_protocol.c src/p0_crc32.c \
		-o $(HOST_BUILD)/test_motion_integration_sanitize
	$(HOST_BUILD)/test_motion_integration_sanitize
	$(HOST_CC) $(HOST_CFLAGS) -fsanitize=address,undefined \
		-DP0_MOTION_OUTPUT_COMPILED=1 -DP0_OFFLINE_MOTION_AUDIT_BUILD=1 \
		tests/test_motion_main.c $(COMMON_SRC) \
		-o $(HOST_BUILD)/test_motion_main_sanitize
	$(HOST_BUILD)/test_motion_main_sanitize
	$(HOST_CC) $(HOST_CFLAGS) -fsanitize=address,undefined \
		tests/test_m2a_calibration.c src/p0_m2a_calibration.c \
		-o $(HOST_BUILD)/test_m2a_calibration_sanitize
	$(HOST_BUILD)/test_m2a_calibration_sanitize
	$(HOST_CC) $(HOST_CFLAGS) -fsanitize=address,undefined \
		tests/test_iwdg_diagnostic.c src/p0_iwdg_diagnostic.c \
		-o $(HOST_BUILD)/test_iwdg_diagnostic_sanitize
	$(HOST_BUILD)/test_iwdg_diagnostic_sanitize
	$(HOST_CC) $(HOST_CFLAGS) -fsanitize=address,undefined \
		tests/test_uart_rx.c src/p0_uart_rx.c src/p0_protocol.c src/p0_crc32.c \
		-o $(HOST_BUILD)/test_uart_rx_sanitize
	$(HOST_BUILD)/test_uart_rx_sanitize
	$(HOST_CC) $(HOST_CFLAGS) -fsanitize=address,undefined \
		-DP0_MOTION_OUTPUT_COMPILED=1 -DP0_M2A_CALIBRATION_BUILD=1 \
		tests/test_uart_main.c $(COMMON_SRC) \
		-o $(HOST_BUILD)/test_uart_main_sanitize
	$(HOST_BUILD)/test_uart_main_sanitize

$(HOST_TEST): tests/test_safe_control.c $(COMMON_SRC) | $(HOST_BUILD)
	$(HOST_CC) $(HOST_CFLAGS) $^ -o $@

$(MOTION_TEST): tests/test_motion_control.c src/p0_motion.c | $(HOST_BUILD)
	$(HOST_CC) $(HOST_CFLAGS) $^ -o $@

$(MOTION_SCHEDULER_TEST): tests/test_motion_scheduler.c \
		src/p0_motion_scheduler.c include/p0_motion_scheduler.h | $(HOST_BUILD)
	$(HOST_CC) $(HOST_CFLAGS) tests/test_motion_scheduler.c \
		src/p0_motion_scheduler.c -o $@

$(MOTION_INTEGRATION_TEST): tests/test_motion_integration.c \
	src/p0_control.c src/p0_motion.c src/p0_protocol.c src/p0_crc32.c | $(HOST_BUILD)
	$(HOST_CC) $(HOST_CFLAGS) $^ -o $@

$(MOTION_MAIN_TEST): tests/test_motion_main.c $(COMMON_SRC) | $(HOST_BUILD)
	$(HOST_CC) $(HOST_CFLAGS) \
		-DP0_MOTION_OUTPUT_COMPILED=1 -DP0_OFFLINE_MOTION_AUDIT_BUILD=1 \
		tests/test_motion_main.c $(COMMON_SRC) -o $@

$(M2A_TEST): tests/test_m2a_calibration.c src/p0_m2a_calibration.c | $(HOST_BUILD)
	$(HOST_CC) $(HOST_CFLAGS) $^ -o $@

$(UART_TEST): tests/test_uart_rx.c src/p0_uart_rx.c src/p0_protocol.c src/p0_crc32.c | $(HOST_BUILD)
	$(HOST_CC) $(HOST_CFLAGS) $^ -o $@

$(UART_MAIN_TEST): tests/test_uart_main.c $(COMMON_SRC) src/main.c | $(HOST_BUILD)
	$(HOST_CC) $(HOST_CFLAGS) \
		-DP0_MOTION_OUTPUT_COMPILED=1 -DP0_M2A_CALIBRATION_BUILD=1 \
		tests/test_uart_main.c $(COMMON_SRC) -o $@

firmware: toolchain $(ARM_ELF) $(ARM_BIN) $(ARM_HEX) $(ARM_LIST)
	$(ARM_SIZE) $(ARM_ELF)

motion-audit-firmware:
	$(MAKE) BUILD=build/motion-audit \
		ARM_DEFINES="-DP0_TARGET_STM32F407=1 \
		-DP0_MOTION_OUTPUT_COMPILED=1 \
		-DP0_OFFLINE_MOTION_AUDIT_BUILD=1 \
		-DP0_MOTION_CALIBRATION_VALID=0 \
		-DP0_M2A_CALIBRATION_BUILD=0" firmware
	@grep -q '<p0_hw_motor_apply_pwm>' \
		build/motion-audit/arm/$(PROJECT).list
	@$(ARM_STRINGS) build/motion-audit/arm/$(PROJECT).elf | \
		grep -q 'P0_H60_SAFE;FW=0.2.0-M1;MOTION=1;CAL=0;M2A=0;TIMEOUT_MS=250'

m2a-calibration-firmware:
	$(MAKE) BUILD=build/m2a \
		ARM_DEFINES="-DP0_TARGET_STM32F407=1 \
		-DP0_MOTION_OUTPUT_COMPILED=1 \
		-DP0_OFFLINE_MOTION_AUDIT_BUILD=0 \
		-DP0_MOTION_CALIBRATION_VALID=0 \
		-DP0_M2A_CALIBRATION_BUILD=1" firmware
	@grep -q '<p0_m2a_calibration_hold>' \
		build/m2a/arm/$(PROJECT).list
	@grep -q '<p0_hw_motor_apply_pwm>' \
		build/m2a/arm/$(PROJECT).list
	@$(ARM_STRINGS) build/m2a/arm/$(PROJECT).elf | \
		grep -q 'P0_H60_SAFE;FW=0.2.0-M2A;MOTION=1;CAL=0;M2A=1;TIMEOUT_MS=250'

iwdg-diagnostic-firmware:
	$(MAKE) BUILD=build/iwdg-diagnostic \
		ARM_DEFINES="-DP0_TARGET_STM32F407=1 \
		-DP0_MOTION_OUTPUT_COMPILED=0 \
		-DP0_OFFLINE_MOTION_AUDIT_BUILD=0 \
		-DP0_MOTION_CALIBRATION_VALID=0 \
		-DP0_M2A_CALIBRATION_BUILD=0 \
		-DP0_M2A_SLOWDRIVE_BUILD=0 \
		-DP0_IWDG_DIAGNOSTIC_BUILD=1" firmware
	@grep -q '<p0_hw_iwdg_diagnostic_stall>' \
		build/iwdg-diagnostic/arm/$(PROJECT).list
	@grep -q '<p0_hw_exception_diagnostic_trigger>' \
		build/iwdg-diagnostic/arm/$(PROJECT).list
	@sed -n '/<p0_hw_exception_diagnostic_trigger>:/,/^$$/p' \
		build/iwdg-diagnostic/arm/$(PROJECT).list | \
		grep -q '000f4240'
	@sed -n '/<p0_hw_exception_diagnostic_trigger>:/,/^$$/p' \
		build/iwdg-diagnostic/arm/$(PROJECT).list | \
		grep -q '40004800'
	@sed -n '/<p0_hw_exception_diagnostic_trigger>:/,/^$$/p' \
		build/iwdg-diagnostic/arm/$(PROJECT).list | \
		grep -q 'udf.*#0'
	@$(ARM_STRINGS) build/iwdg-diagnostic/arm/$(PROJECT).elf | \
		grep -q 'P0_H60_SAFE;FW=0.2.10-RESET-DIAG-R2;MOTION=0;CAL=0;M2A=0;TIMEOUT_MS=250;UART_RX=IRQ256-R1;IWDG_HARDFAULT_DIAG=1;TRIGGER_MS=1500;MOTION_LOCKED=1'

# 独立目录；不覆盖板上M2A5K-R1对应的旧构建或回滚资产。
.PHONY: m2a-slowdrive-firmware slowdrive-test \
	h6-characterization-firmware h6-characterization-test \
	h6-extended-window-firmware h6-extended-window-test \
	w2-four-wheel-profile-firmware w2-four-wheel-profile-test \
	w2-five-second-link-loss-firmware w2-five-second-link-loss-test
SLOW_BUILD ?= build/m2a-slowdrive
H6_BUILD ?= build/h6-characterization
H6_R2_BUILD ?= build/h6-extended-window
W2_BUILD ?= build/w2-four-wheel-profile
W2_LINK5_BUILD ?= build/w2-five-second-link-loss-offline
slowdrive-test:
	python3 -m unittest -v tests/test_m2a_slowdrive_offline.py tests/test_m2a_slowdrive_console.py

m2a-slowdrive-firmware:
	$(MAKE) BUILD=$(SLOW_BUILD) \
		ARM_DEFINES="-DP0_TARGET_STM32F407=1 -DP0_MOTION_OUTPUT_COMPILED=1 \
		-DP0_M2A_CALIBRATION_BUILD=1 -DP0_M2A_SLOWDRIVE_BUILD=1 \
		-DP0_H6_CHARACTERIZATION_BUILD=0 \
		-DP0_OFFLINE_MOTION_AUDIT_BUILD=0 -DP0_MOTION_CALIBRATION_VALID=0" firmware
	@$(ARM_STRINGS) $(SLOW_BUILD)/arm/$(PROJECT).elf | \
		grep -q 'FW=0.2.1-M2A-SLOW5K-MB-PLUS-50-R1'

h6-characterization-test:
	python3 -m unittest -v tests/test_m2a_slowdrive_offline.py \
		tests/test_m2a_slowdrive_console.py tests/test_h6_parameter_analysis.py \
		tests/test_h6_field_batch.py

h6-characterization-firmware:
	$(MAKE) BUILD=$(H6_BUILD) \
		ARM_DEFINES="-DP0_TARGET_STM32F407=1 -DP0_MOTION_OUTPUT_COMPILED=1 \
		-DP0_M2A_CALIBRATION_BUILD=1 -DP0_M2A_SLOWDRIVE_BUILD=1 \
		-DP0_H6_CHARACTERIZATION_BUILD=1 -DP0_OFFLINE_MOTION_AUDIT_BUILD=0 \
		-DP0_MOTION_CALIBRATION_VALID=0 -DP0_IWDG_DIAGNOSTIC_BUILD=0" firmware
	@grep -q '<p0_hw_slow_commit>' $(H6_BUILD)/arm/$(PROJECT).list
	@$(ARM_STRINGS) $(H6_BUILD)/arm/$(PROJECT).elf | \
		grep -q 'P0_H60_SAFE;FW=0.2.11-H6-SINGLE-R1;MOTION=1;CAL=0;M2A=1;TIMEOUT_MS=250;UART_RX=IRQ256-R1;PWM=H6-SINGLE-5K-R1;WAKE_MS=3;STOP=GPIO00;ONE_CHANNEL_PER_ARM=1;MIN_DUTY=50;MAX_DUTY=120;HOLD_LEASE_MS=75;MAX_ARMED_MS=1000'

h6-extended-window-test:
	python3 -m unittest -v tests/test_m2a_slowdrive_offline.py \
		tests/test_m2a_slowdrive_console.py

h6-extended-window-firmware:
	$(MAKE) BUILD=$(H6_R2_BUILD) \
		ARM_DEFINES="-DP0_TARGET_STM32F407=1 -DP0_MOTION_OUTPUT_COMPILED=1 \
		-DP0_M2A_CALIBRATION_BUILD=1 -DP0_M2A_SLOWDRIVE_BUILD=1 \
		-DP0_H6_CHARACTERIZATION_BUILD=1 -DP0_H6_EXTENDED_WINDOW_BUILD=1 \
		-DP0_OFFLINE_MOTION_AUDIT_BUILD=0 -DP0_MOTION_CALIBRATION_VALID=0 \
		-DP0_IWDG_DIAGNOSTIC_BUILD=0" firmware
	@grep -q '<p0_hw_slow_commit>' $(H6_R2_BUILD)/arm/$(PROJECT).list
	@$(ARM_STRINGS) $(H6_R2_BUILD)/arm/$(PROJECT).elf | \
		grep -q 'P0_H60_SAFE;FW=0.2.12-H6-SINGLE-R2;MOTION=1;CAL=0;M2A=1;TIMEOUT_MS=250;UART_RX=IRQ256-R1;PWM=H6-SINGLE-5K-R2;WAKE_MS=3;STOP=GPIO00;ONE_CHANNEL_PER_ARM=1;MC_PLUS_80_ONLY=1;HOLD_LEASE_MS=75;MAX_ARMED_MS=2500;ENVELOPE_MS=300,1200,300;HOST_NONZERO_MAX_MS=1800'

w2-four-wheel-profile-test:
	python3 -m unittest -v tests/test_m2a_slowdrive_offline.py

w2-four-wheel-profile-firmware:
	$(MAKE) BUILD=$(W2_BUILD) \
		ARM_DEFINES="-DP0_TARGET_STM32F407=1 -DP0_MOTION_OUTPUT_COMPILED=1 \
		-DP0_M2A_CALIBRATION_BUILD=1 -DP0_M2A_SLOWDRIVE_BUILD=1 \
		-DP0_H6_CHARACTERIZATION_BUILD=1 -DP0_W2_FOUR_WHEEL_PROFILE_BUILD=1 \
		-DP0_H6_EXTENDED_WINDOW_BUILD=0 -DP0_OFFLINE_MOTION_AUDIT_BUILD=0 \
		-DP0_MOTION_CALIBRATION_VALID=0 -DP0_IWDG_DIAGNOSTIC_BUILD=0" firmware
	@grep -q '<p0_hw_slow_commit>' $(W2_BUILD)/arm/$(PROJECT).list
	@$(ARM_STRINGS) $(W2_BUILD)/arm/$(PROJECT).elf | \
		grep -q 'P0_H60_SAFE;FW=0.2.13-W2-FWDREV-R1;MOTION=1;CAL=0;M2A=1;TIMEOUT_MS=250;UART_RX=IRQ256-R1;PWM=W2-FOUR-5K-R1;WAKE_MS=3;STOP=GPIO00;FOUR_CHANNEL_PROFILE=1;PROFILE_CHANNEL=240;FORWARD_SIGNS=-1,+1,-1,+1;DUTY=80;HOLD_LEASE_MS=75;MAX_ARMED_MS=1000;DIRECTION_CHANGE_REARM=1'

# 隔离的离线候选；不复用已消费 W2 包的固件目录或版本标识。
w2-five-second-link-loss-test:
	@mkdir -p $(W2_LINK5_BUILD)
	$(HOST_CC) $(HOST_CFLAGS) \
		-DP0_MOTION_OUTPUT_COMPILED=1 -DP0_M2A_CALIBRATION_BUILD=1 \
		-DP0_M2A_SLOWDRIVE_BUILD=1 -DP0_H6_CHARACTERIZATION_BUILD=1 \
		-DP0_W2_FOUR_WHEEL_PROFILE_BUILD=1 \
		-DP0_W2_FIVE_SECOND_LINK_LOSS_BUILD=1 \
		tests/test_w2_five_second_link_loss.c src/p0_m2a_slowdrive.c \
		-o $(W2_LINK5_BUILD)/test_w2_five_second_link_loss
	$(W2_LINK5_BUILD)/test_w2_five_second_link_loss

w2-five-second-link-loss-firmware:
	$(MAKE) BUILD=$(W2_LINK5_BUILD) \
		ARM_DEFINES="-DP0_TARGET_STM32F407=1 -DP0_MOTION_OUTPUT_COMPILED=1 \
		-DP0_M2A_CALIBRATION_BUILD=1 -DP0_M2A_SLOWDRIVE_BUILD=1 \
		-DP0_H6_CHARACTERIZATION_BUILD=1 -DP0_W2_FOUR_WHEEL_PROFILE_BUILD=1 \
		-DP0_W2_FIVE_SECOND_LINK_LOSS_BUILD=1 \
		-DP0_H6_EXTENDED_WINDOW_BUILD=0 -DP0_OFFLINE_MOTION_AUDIT_BUILD=0 \
		-DP0_MOTION_CALIBRATION_VALID=0 -DP0_IWDG_DIAGNOSTIC_BUILD=0" firmware
	@grep -q '<p0_hw_slow_commit>' $(W2_LINK5_BUILD)/arm/$(PROJECT).list
	@$(ARM_STRINGS) $(W2_LINK5_BUILD)/arm/$(PROJECT).elf | \
		grep -q 'P0_H60_SAFE;FW=0.2.14-W2-LINK5-OFFLINE-R1;MOTION=1;CAL=0;M2A=1;TIMEOUT_MS=250;UART_RX=IRQ256-R1;PWM=W2-FOUR-5K-R1;WAKE_MS=3;STOP=GPIO00;FOUR_CHANNEL_PROFILE=1;PROFILE_CHANNEL=240;FORWARD_SIGNS=-1,+1,-1,+1;DUTY=80;HOLD_LEASE_MS=75;MAX_ARMED_MS=5000;DIRECTION_CHANGE_REARM=1;LINK_LOSS_CANDIDATE=1'

m2a-verify: test source-safety-test m2a-calibration-firmware
	@grep -q '<p0_hw_motor_force_safe>' \
		build/m2a/arm/$(PROJECT).list
	@shasum -a 256 \
		build/m2a/arm/$(PROJECT).elf \
		build/m2a/arm/$(PROJECT).bin \
		build/m2a/arm/$(PROJECT).hex

motion-lock-test: toolchain | $(ARM_BUILD)
	@if $(ARM_GCC) $(ARM_CPU) -std=c11 -Iinclude \
		-DP0_TARGET_STM32F407=1 \
		-DP0_MOTION_OUTPUT_COMPILED=1 \
		-DP0_OFFLINE_MOTION_AUDIT_BUILD=0 \
		-DP0_MOTION_CALIBRATION_VALID=0 \
		-c src/p0_manifest.c -o $(ARM_BUILD)/forbidden_motion.o \
		>/dev/null 2>&1; then \
		echo "ERROR: non-audit motion build was accepted"; \
		rm -f $(ARM_BUILD)/forbidden_motion.o; \
		exit 1; \
	else \
		echo "PASS: non-audit motion build rejected"; \
	fi
	@if $(ARM_GCC) $(ARM_CPU) -std=c11 -Iinclude \
		-DP0_TARGET_STM32F407=1 \
		-DP0_MOTION_OUTPUT_COMPILED=0 \
		-DP0_OFFLINE_MOTION_AUDIT_BUILD=0 \
		-DP0_MOTION_CALIBRATION_VALID=0 \
		-DP0_M2A_CALIBRATION_BUILD=1 \
		-c src/p0_manifest.c -o $(ARM_BUILD)/forbidden_m2a.o \
		>/dev/null 2>&1; then \
		echo "ERROR: M2-A build without PWM was accepted"; \
		rm -f $(ARM_BUILD)/forbidden_m2a.o; \
		exit 1; \
	else \
		echo "PASS: malformed M2-A build rejected"; \
	fi
	@if $(ARM_GCC) $(ARM_CPU) -std=c11 -Iinclude \
		-DP0_TARGET_STM32F407=1 \
		-DP0_MOTION_OUTPUT_COMPILED=1 \
		-DP0_OFFLINE_MOTION_AUDIT_BUILD=0 \
		-DP0_MOTION_CALIBRATION_VALID=0 \
		-DP0_M2A_CALIBRATION_BUILD=0 \
		-DP0_M2A_SLOWDRIVE_BUILD=0 \
		-DP0_IWDG_DIAGNOSTIC_BUILD=1 \
		-c src/p0_manifest.c -o $(ARM_BUILD)/forbidden_iwdg_diag.o \
		>/dev/null 2>&1; then \
		echo "ERROR: IWDG diagnostic build with motion output was accepted"; \
		rm -f $(ARM_BUILD)/forbidden_iwdg_diag.o; \
		exit 1; \
	else \
		echo "PASS: motion-capable IWDG diagnostic build rejected"; \
	fi

toolchain:
	@test -x "$(ARM_GCC)" || { echo "ARM GCC not found: $(ARM_GCC)"; exit 1; }

ARM_C_OBJ := $(patsubst src/%.c,$(ARM_BUILD)/%.o,$(ARM_SRC))
ARM_S_OBJ := $(patsubst src/%.S,$(ARM_BUILD)/%.o,$(ARM_ASM))

$(ARM_BUILD)/%.o: src/%.c $(wildcard include/*.h) | $(ARM_BUILD)
	$(ARM_GCC) $(ARM_CFLAGS) -c $< -o $@

$(ARM_BUILD)/%.o: src/%.S | $(ARM_BUILD)
	$(ARM_GCC) $(ARM_CPU) -g0 -c $< -o $@

$(ARM_ELF): $(ARM_C_OBJ) $(ARM_S_OBJ) $(ARM_LINKER)
	$(ARM_GCC) $(ARM_LDFLAGS) $(ARM_C_OBJ) $(ARM_S_OBJ) -lgcc -o $@

$(ARM_BIN): $(ARM_ELF)
	$(ARM_OBJCOPY) -O binary $< $@

$(ARM_HEX): $(ARM_ELF)
	$(ARM_OBJCOPY) -O ihex $< $@

$(ARM_LIST): $(ARM_ELF)
	$(ARM_OBJDUMP) -d -S $< > $@

verify: test bootloader-test source-safety-test motion-lock-test firmware
	@grep -q '<HardFault_Handler>' $(ARM_LIST)
	@grep -q '<p0_hw_motor_force_safe>' $(ARM_LIST)
	@grep -q '<SysTick_Handler>' $(ARM_LIST)
	@if grep -q '<p0_hw_exception_diagnostic_trigger>' $(ARM_LIST); then \
		echo "ERROR: diagnostic exception trigger leaked into production build"; \
		exit 1; \
	else \
		echo "PASS: diagnostic exception trigger absent from production build"; \
	fi
	@if $(ARM_STRINGS) $(ARM_ELF) | grep -q 'RESET-DIAG-R2'; then \
		echo "ERROR: diagnostic R2 manifest leaked into production build"; \
		exit 1; \
	else \
		echo "PASS: diagnostic R2 manifest absent from production build"; \
	fi
	@$(ARM_STRINGS) $(ARM_ELF) | \
		grep -q 'P0_H60_SAFE;FW=0.2.0-M1;MOTION=0;CAL=0;M2A=0;TIMEOUT_MS=250'
	@shasum -a 256 $(ARM_ELF) $(ARM_BIN) $(ARM_HEX)

$(HOST_BUILD) $(ARM_BUILD):
	mkdir -p $@

clean:
	rm -rf $(BUILD)

# Isolated default-off candidate, no flash/port entry point.
.PHONY: usb-quiet-test usb-quiet-firmware
usb-quiet-test: | $(HOST_BUILD)
	$(HOST_CC) $(HOST_CFLAGS) -DP0_USB_QUIET_BUILD=1 \
		tests/test_usb_quiet_main.c $(COMMON_SRC) -o $(HOST_BUILD)/test_usb_quiet_main
	$(HOST_BUILD)/test_usb_quiet_main
	python3 -m unittest -v tests/test_usb_quiet_build.py

usb-quiet-firmware:
	$(MAKE) BUILD=$(BUILD)/usb-quiet ARM_DEFINES="-DP0_TARGET_STM32F407=1 -DP0_USB_QUIET_BUILD=1" firmware

# J5独立无电机候选，保留USB静默协议/保护；无刷写或设备入口。
.PHONY: j5-uart-test j5-uart-firmware
j5-uart-test: | $(HOST_BUILD)
	$(HOST_CC) $(HOST_CFLAGS) -DP0_USB_QUIET_BUILD=1 -DP0_UART_J5_BUILD=1 \
		tests/test_usb_quiet_main.c $(COMMON_SRC) -o $(HOST_BUILD)/test_j5_uart_main
	$(HOST_BUILD)/test_j5_uart_main
	python3 -m unittest -v tests/test_j5_uart_build.py

j5-uart-firmware:
	$(MAKE) BUILD=$(BUILD)/j5-uart ARM_DEFINES="-DP0_TARGET_STM32F407=1 -DP0_USB_QUIET_BUILD=1 -DP0_UART_J5_BUILD=1" firmware

# Default-off experimental USB motion candidate; no device/flash target.
.PHONY: usb-motion-firmware usb-motion-test
usb-motion-firmware:
	$(MAKE) BUILD=$(BUILD)/usb-motion ARM_DEFINES="-DP0_TARGET_STM32F407=1 -DP0_USB_MOTION_BUILD=1 -DP0_MOTION_OUTPUT_COMPILED=1" firmware

usb-motion-test: | $(HOST_BUILD)
	$(HOST_CC) $(HOST_CFLAGS) -DP0_USB_MOTION_BUILD=1 -DP0_MOTION_OUTPUT_COMPILED=1 \
		tests/test_usb_motion_main.c $(COMMON_SRC) -o $(HOST_BUILD)/test_usb_motion_main
	$(HOST_BUILD)/test_usb_motion_main
	python3 -m unittest -v tests/test_usb_motion_build.py

# 独立RAM诊断候选，仅离线构建/测试；无设备或Flash目标。
.PHONY: usb-motion-trace-firmware usb-motion-trace-test
usb-motion-trace-firmware:
	$(MAKE) BUILD=$(BUILD)/usb-motion-trace ARM_DEFINES="-DP0_TARGET_STM32F407=1 -DP0_USB_MOTION_BUILD=1 -DP0_MOTION_OUTPUT_COMPILED=1 -DP0_USB_MOTION_TRACE_BUILD=1" firmware

usb-motion-trace-test:
	python3 -m unittest -v tests/test_usb_motion_trace_build.py

.PHONY: usb-startup-candidate-firmware usb-startup-candidate-test
usb-startup-candidate-firmware:
	$(MAKE) BUILD=$(BUILD)/usb-startup-candidate ARM_DEFINES="-DP0_TARGET_STM32F407=1 -DP0_USB_MOTION_BUILD=1 -DP0_MOTION_OUTPUT_COMPILED=1 -DP0_USB_MOTION_TRACE_BUILD=1 -DP0_USB_STARTUP_CANDIDATE_BUILD=1" firmware

usb-startup-candidate-test:
	python3 -m unittest -v tests/test_usb_startup_candidate.py

.PHONY: usb-four-candidate-firmware usb-four-candidate-test
usb-four-candidate-firmware:
	$(MAKE) BUILD=$(BUILD)/usb-four-candidate ARM_DEFINES="-DP0_TARGET_STM32F407=1 -DP0_USB_MOTION_BUILD=1 -DP0_MOTION_OUTPUT_COMPILED=1 -DP0_USB_FOUR_WHEEL_CANDIDATE_BUILD=1" firmware

usb-four-candidate-test:
	python3 -m unittest -v tests/test_usb_four_candidate.py

# 只构建离线候选，不包含下载、串口或设备命令。
.PHONY: usb-link-recovery-firmware usb-link-recovery-test
usb-link-recovery-firmware:
	$(MAKE) BUILD=$(BUILD)/usb-link-recovery ARM_DEFINES="-DP0_TARGET_STM32F407=1 -DP0_USB_MOTION_BUILD=1 -DP0_MOTION_OUTPUT_COMPILED=1 -DP0_USB_MOTION_TRACE_BUILD=1 -DP0_USB_STARTUP_CANDIDATE_BUILD=1 -DP0_USB_LINK_RECOVERY_BUILD=1" firmware

usb-link-recovery-test:
	python3 -m unittest -v tests/test_usb_link_recovery_build.py

# 默认关闭，仅离线生成独立输入滤波候选；不包含设备操作。
.PHONY: usb-encoder-filter-firmware usb-encoder-filter-test
usb-encoder-filter-firmware:
	$(MAKE) BUILD=$(BUILD)/usb-encoder-filter ARM_DEFINES="-DP0_TARGET_STM32F407=1 -DP0_USB_MOTION_BUILD=1 -DP0_MOTION_OUTPUT_COMPILED=1 -DP0_USB_MOTION_TRACE_BUILD=1 -DP0_USB_STARTUP_CANDIDATE_BUILD=1 -DP0_USB_ENCODER_FILTER_BUILD=1" firmware

usb-encoder-filter-test:
	python3 -m unittest -v tests/test_usb_encoder_filter_build.py

# 独立默认关闭；不包含下载、串口或执行现场包。
.PHONY: usb-rx-diag-firmware usb-rx-diag-test
usb-rx-diag-firmware:
	$(MAKE) BUILD=$(BUILD)/usb-rx-diag ARM_LINKER=linker/stm32f407vetx_diag.ld ARM_DEFINES="-DP0_TARGET_STM32F407=1 -DP0_USB_MOTION_BUILD=1 -DP0_MOTION_OUTPUT_COMPILED=1 -DP0_USB_MOTION_TRACE_BUILD=1 -DP0_USB_STARTUP_CANDIDATE_BUILD=1 -DP0_USB_ENCODER_FILTER_BUILD=1 -DP0_USB_RX_DIAG_BUILD=1" firmware

usb-rx-diag-test:
	python3 -m unittest -v tests/test_usb_diag_build.py

# 第1步数字衔接；无下载、端口或现场执行目标，保留独立SRAM布局。
.PHONY: usb-control-candidate-firmware usb-control-candidate-test
usb-control-candidate-firmware:
	$(MAKE) BUILD=$(BUILD)/usb-control-candidate ARM_LINKER=linker/stm32f407vetx_diag.ld ARM_DEFINES="-DP0_TARGET_STM32F407=1 -DP0_USB_MOTION_BUILD=1 -DP0_MOTION_OUTPUT_COMPILED=1 -DP0_USB_FOUR_WHEEL_CANDIDATE_BUILD=1 -DP0_USB_ENCODER_FILTER_BUILD=1 -DP0_USB_RX_DIAG_BUILD=1 -DP0_USB_CONTROL_DIAG_BUILD=1" firmware

usb-control-candidate-test:
	python3 -m unittest -v tests/test_usb_control_candidate.py

# 同界限单轮TRACE调速候选；不含下载或现场动作。
.PHONY: usb-velocity-candidate-firmware usb-velocity-candidate-test
usb-velocity-candidate-firmware:
	$(MAKE) BUILD=$(BUILD)/usb-velocity-candidate ARM_LINKER=linker/stm32f407vetx_diag.ld ARM_DEFINES="-DP0_TARGET_STM32F407=1 -DP0_USB_MOTION_BUILD=1 -DP0_MOTION_OUTPUT_COMPILED=1 -DP0_USB_MOTION_TRACE_BUILD=1 -DP0_USB_STARTUP_CANDIDATE_BUILD=1 -DP0_USB_ENCODER_FILTER_BUILD=1 -DP0_USB_RX_DIAG_BUILD=1 -DP0_USB_VELOCITY_DIAG_BUILD=1" firmware

usb-velocity-candidate-test:
	python3 -m unittest -v tests/test_usb_velocity_candidate.py

.PHONY: usb-integrated-candidate-firmware usb-integrated-candidate-test
usb-integrated-candidate-firmware:
	$(MAKE) BUILD=$(BUILD)/usb-integrated-candidate ARM_LINKER=linker/stm32f407vetx_diag.ld ARM_DEFINES="-DP0_TARGET_STM32F407=1 -DP0_USB_MOTION_BUILD=1 -DP0_MOTION_OUTPUT_COMPILED=1 -DP0_USB_FOUR_WHEEL_CANDIDATE_BUILD=1 -DP0_USB_ENCODER_FILTER_BUILD=1 -DP0_USB_RX_DIAG_BUILD=1 -DP0_USB_CONTROL_DIAG_BUILD=1 -DP0_USB_INTEGRATED_BUILD=1" firmware

usb-integrated-candidate-test:
	PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=../../tools/nano_bench:tests python3 -m unittest -v tests.test_usb_integrated_candidate
