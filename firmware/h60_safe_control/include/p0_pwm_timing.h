#ifndef P0_PWM_TIMING_H
#define P0_PWM_TIMING_H

#include "p0_build_config.h"
#include "p0_m2a_calibration.h"

/* 板级时钟保持HSI 16MHz、APB不分频，PWM定时器PSC=0。 */
#define P0_PWM_TIMER_HZ UINT32_C(16000000)
#if P0_M2A_CALIBRATION_BUILD != 0
/* AT8236休眠唤醒需至少5us高电平；5%在5kHz下为10us。 */
#define P0_MOTOR_PWM_PERIOD_COUNTS UINT32_C(3200)
_Static_assert(P0_MOTOR_PWM_PERIOD_COUNTS * P0_M2A_MIN_DUTY_PERMILLE /
                   UINT32_C(1000) >= P0_PWM_TIMER_HZ / UINT32_C(100000),
               "M2-A minimum pulse must allow at least 10 us for wake-up");
#else
#define P0_MOTOR_PWM_PERIOD_COUNTS UINT32_C(800)
#endif

static inline uint32_t p0_pwm_compare_counts(uint16_t permille)
{
    return ((uint32_t)permille * P0_MOTOR_PWM_PERIOD_COUNTS) /
           UINT32_C(1000);
}

#endif
