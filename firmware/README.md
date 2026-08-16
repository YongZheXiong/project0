# Firmware Workspace

## 当前入口

- [H60 安全固件要求](h60_safety_firmware_requirements_v0_1.md)：当前正式需求，尚未实现。
- 当前目标控制器为 OpenCTR H60 V3.7；必须完成可复现构建、状态机、显式 ARM、命令超时、IWDG、异常撤 PWM 和协议边界测试。

## 历史记录

本目录内所有 `stm32_*.md` 文件记录上一 STM32 + WSDC2412D 平台的安全初始化、短脉冲、UART、编码器和迁移证据。它们只用于追溯，不是 H60 固件、引脚或运动准入依据。

当前没有可直接宣称为 H60 正式控制固件的源码或二进制。
