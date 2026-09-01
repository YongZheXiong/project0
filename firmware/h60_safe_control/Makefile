SHELL := /bin/sh

PROJECT := p0_h60_safe_control
BUILD := build
HOST_BUILD := $(BUILD)/host
ARM_BUILD := $(BUILD)/arm

COMMON_SRC := src/p0_crc32.c src/p0_protocol.c src/p0_control.c
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
ARM_CFLAGS := $(ARM_CPU) -std=c11 -Os -g0 -Wall -Wextra -Werror \
	-ffreestanding -fno-builtin -fdata-sections -ffunction-sections \
	-fno-unwind-tables -fno-asynchronous-unwind-tables -Iinclude \
	-DP0_TARGET_STM32F407=1 -DP0_MOTION_OUTPUT_COMPILED=0
ARM_LDFLAGS := $(ARM_CPU) -nostdlib -Wl,--gc-sections -Wl,-z,noexecstack \
	-Wl,-Map=$(ARM_BUILD)/$(PROJECT).map \
	-Tlinker/stm32f407vetx.ld

HOST_TEST := $(HOST_BUILD)/test_safe_control
ARM_ELF := $(ARM_BUILD)/$(PROJECT).elf
ARM_BIN := $(ARM_BUILD)/$(PROJECT).bin
ARM_HEX := $(ARM_BUILD)/$(PROJECT).hex
ARM_LIST := $(ARM_BUILD)/$(PROJECT).list

.PHONY: all test bootloader-test source-safety-test sanitize firmware verify clean toolchain

all: test firmware verify

test: $(HOST_TEST)
	$(HOST_TEST)

bootloader-test:
	python3 -m unittest -v tests/test_stm32_uart_bootloader.py

source-safety-test:
	python3 -m unittest -v tests/test_firmware_source_safety.py

sanitize: | $(HOST_BUILD)
	$(HOST_CC) $(HOST_CFLAGS) -fsanitize=address,undefined \
		tests/test_safe_control.c $(COMMON_SRC) \
		-o $(HOST_BUILD)/test_safe_control_sanitize
	$(HOST_BUILD)/test_safe_control_sanitize

$(HOST_TEST): tests/test_safe_control.c $(COMMON_SRC) | $(HOST_BUILD)
	$(HOST_CC) $(HOST_CFLAGS) $^ -o $@

firmware: toolchain $(ARM_ELF) $(ARM_BIN) $(ARM_HEX) $(ARM_LIST)
	$(ARM_SIZE) $(ARM_ELF)

toolchain:
	@test -x "$(ARM_GCC)" || { echo "ARM GCC not found: $(ARM_GCC)"; exit 1; }

ARM_C_OBJ := $(patsubst src/%.c,$(ARM_BUILD)/%.o,$(ARM_SRC))
ARM_S_OBJ := $(patsubst src/%.S,$(ARM_BUILD)/%.o,$(ARM_ASM))

$(ARM_BUILD)/%.o: src/%.c | $(ARM_BUILD)
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

verify: test bootloader-test source-safety-test firmware
	@grep -q '<HardFault_Handler>' $(ARM_LIST)
	@grep -q '<p0_hw_motor_force_safe>' $(ARM_LIST)
	@grep -q '<SysTick_Handler>' $(ARM_LIST)
	@$(ARM_STRINGS) $(ARM_ELF) | \
		grep -q 'P0_H60_SAFE;FW=0.1.1;MOTION=0;TIMEOUT_MS=250'
	@shasum -a 256 $(ARM_ELF) $(ARM_BIN) $(ARM_HEX)

$(HOST_BUILD) $(ARM_BUILD):
	mkdir -p $@

clean:
	rm -rf $(BUILD)
