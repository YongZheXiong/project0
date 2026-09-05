SHELL := /bin/sh

PROJECT := p0_h60_safe_control
BUILD := build
HOST_BUILD := $(BUILD)/host
ARM_BUILD := $(BUILD)/arm

COMMON_SRC := src/p0_crc32.c src/p0_protocol.c src/p0_control.c \
	src/p0_motion.c src/p0_m2a_calibration.c src/p0_uart_rx.c src/p0_m2a_slowdrive.c
ARM_SRC := $(COMMON_SRC) src/p0_runtime.c src/p0_manifest.c \
	src/p0_hw_stm32f407.c src/main.c
ARM_ASM := src/startup_stm32f407.S

HOST_CC ?= cc
HOST_CFLAGS := -std=c11 -O2 -g -Wall -Wextra -Werror -pedantic -Iinclude

ARM_GCC ?= $(shell command -v arm-none-eabi-gcc 2>/dev/null)
ifeq ($(strip $(ARM_GCC)),)
ARM_GCC := /Applications/STM32CubeIDE.app/Contents/Eclipse/plugins/com.st.stm32cube.ide.mcu.externaltools.gnu-tools-for-stm32.14.3.rel1.macosaarch64_1.0.0.202602081740/tools/bin/arm-none-eabi-gcc
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
	-DP0_M2A_CALIBRATION_BUILD=0
ARM_CFLAGS := $(ARM_CPU) -std=c11 -Os -g0 -Wall -Wextra -Werror \
	-ffreestanding -fno-builtin -fdata-sections -ffunction-sections \
	-fno-unwind-tables -fno-asynchronous-unwind-tables -Iinclude \
	$(ARM_DEFINES)
ARM_LDFLAGS := $(ARM_CPU) -nostdlib -Wl,--gc-sections -Wl,-z,noexecstack \
	-Wl,-Map=$(ARM_BUILD)/$(PROJECT).map \
	-Tlinker/stm32f407vetx.ld

HOST_TEST := $(HOST_BUILD)/test_safe_control
MOTION_TEST := $(HOST_BUILD)/test_motion_control
M2A_TEST := $(HOST_BUILD)/test_m2a_calibration
UART_TEST := $(HOST_BUILD)/test_uart_rx
UART_MAIN_TEST := $(HOST_BUILD)/test_uart_main
PWM_TIMING_TEST := $(HOST_BUILD)/test_pwm_timing
ARM_ELF := $(ARM_BUILD)/$(PROJECT).elf
ARM_BIN := $(ARM_BUILD)/$(PROJECT).bin
ARM_HEX := $(ARM_BUILD)/$(PROJECT).hex
ARM_LIST := $(ARM_BUILD)/$(PROJECT).list

.PHONY: all test bootloader-test source-safety-test sanitize firmware \
	motion-audit-firmware m2a-calibration-firmware m2a-verify \
	motion-lock-test verify clean toolchain

all: test firmware verify

test: $(HOST_TEST) $(MOTION_TEST) $(M2A_TEST) $(UART_TEST) $(UART_MAIN_TEST) $(PWM_TIMING_TEST)
	$(HOST_TEST)
	$(MOTION_TEST)
	$(M2A_TEST)
	$(UART_TEST)
	$(UART_MAIN_TEST)
	$(PWM_TIMING_TEST)

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
		tests/test_m2a_calibration.c src/p0_m2a_calibration.c \
		-o $(HOST_BUILD)/test_m2a_calibration_sanitize
	$(HOST_BUILD)/test_m2a_calibration_sanitize
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

# 独立目录；不覆盖板上M2A5K-R1对应的旧构建或回滚资产。
.PHONY: m2a-slowdrive-firmware slowdrive-test
SLOW_BUILD ?= build/m2a-slowdrive
slowdrive-test:
	python3 -m unittest -v tests/test_m2a_slowdrive_offline.py tests/test_m2a_slowdrive_console.py

m2a-slowdrive-firmware:
	$(MAKE) BUILD=$(SLOW_BUILD) \
		ARM_DEFINES="-DP0_TARGET_STM32F407=1 -DP0_MOTION_OUTPUT_COMPILED=1 \
		-DP0_M2A_CALIBRATION_BUILD=1 -DP0_M2A_SLOWDRIVE_BUILD=1 \
		-DP0_OFFLINE_MOTION_AUDIT_BUILD=0 -DP0_MOTION_CALIBRATION_VALID=0" firmware
	@$(ARM_STRINGS) $(SLOW_BUILD)/arm/$(PROJECT).elf | \
		grep -q 'FW=0.2.1-M2A-SLOW5K-MB-PLUS-50-R1'

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

toolchain:
	@test -x "$(ARM_GCC)" || { echo "ARM GCC not found: $(ARM_GCC)"; exit 1; }

ARM_C_OBJ := $(patsubst src/%.c,$(ARM_BUILD)/%.o,$(ARM_SRC))
ARM_S_OBJ := $(patsubst src/%.S,$(ARM_BUILD)/%.o,$(ARM_ASM))

$(ARM_BUILD)/%.o: src/%.c $(wildcard include/*.h) | $(ARM_BUILD)
	$(ARM_GCC) $(ARM_CFLAGS) -c $< -o $@

$(ARM_BUILD)/%.o: src/%.S | $(ARM_BUILD)
	$(ARM_GCC) $(ARM_CPU) -g0 -c $< -o $@

$(ARM_ELF): $(ARM_C_OBJ) $(ARM_S_OBJ) linker/stm32f407vetx.ld
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
	@$(ARM_STRINGS) $(ARM_ELF) | \
		grep -q 'P0_H60_SAFE;FW=0.2.0-M1;MOTION=0;CAL=0;M2A=0;TIMEOUT_MS=250'
	@shasum -a 256 $(ARM_ELF) $(ARM_BIN) $(ARM_HEX)

$(HOST_BUILD) $(ARM_BUILD):
	mkdir -p $@

clean:
	rm -rf $(BUILD)
