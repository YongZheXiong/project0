#ifndef P0_UART_PINMAP_H
#define P0_UART_PINMAP_H

#include "p0_build_config.h"

/* 同一USART3的互斥映射；J5候选不驱动USB-COM芯片侧PD8/PD9。 */
#if P0_UART_J5_BUILD != 0
#define P0_UART_GPIO GPIOB
#define P0_UART_TX_PIN 10
#define P0_UART_RX_PIN 11
#define P0_UART_GPIO_CLOCKS (RCC_AHB1_GPIOBEN | RCC_AHB1_GPIODEN)
#else
#define P0_UART_GPIO GPIOD
#define P0_UART_TX_PIN 8
#define P0_UART_RX_PIN 9
#define P0_UART_GPIO_CLOCKS RCC_AHB1_GPIODEN
#endif

#endif
