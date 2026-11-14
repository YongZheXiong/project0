# H60 安全控制固件

本目录面向 OpenCTR H60 V3.7 和 STM32F407。默认构建保持 `MOTION=0 / CAL=0`，编译与宿主检查无需连接控制板。需要 C 编译器、Python 3 和 GNU Arm 交叉工具链。可把 `arm-none-eabi-gcc` 所在目录加入 PATH，或者给 `make` 传入 `ARM_GCC` 路径。

```sh
make verify
```

## 复编 v1.1.3 的归档试验制品

[v1.1.3 架空试验报告](../../reports/nano_h60_raised_control_v1_1_3.md)对应的是 28R2 工程构建。以下命令只在独立目录生成制品，用于复现和比较散列。试验制品包含运动能力，默认验证使用上面的无运动构建。

```sh
make BUILD=build/review-28r2 ARM_LINKER=linker/stm32f407vetx_diag.ld \
  ARM_DEFINES='-DP0_TARGET_STM32F407=1 -DP0_USB_MOTION_BUILD=1 -DP0_MOTION_OUTPUT_COMPILED=1 -DP0_USB_FOUR_WHEEL_CANDIDATE_BUILD=1 -DP0_USB_ENCODER_FILTER_BUILD=1 -DP0_USB_RX_DIAG_BUILD=1 -DP0_USB_CONTROL_DIAG_BUILD=1 -DP0_USB_INTEGRATED_BUILD=1 -DP0_USB_MANUAL_BUILD=1' firmware
shasum -a 256 build/review-28r2/arm/p0_h60_safe_control.bin
```

使用 GNU Tools for STM32 14.3.rel1（GCC 14.3.1）时，预期 BIN 约 12 KB，SHA-256 为 `1d03e39d628a4cf32c1e698a30120fc6b2bbd0a842887f58d7f77678ba873f5e`。SHA 匹配说明复现了归档构建，适用的物理结果见报告。
