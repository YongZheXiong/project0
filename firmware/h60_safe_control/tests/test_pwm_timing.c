#include "p0_pwm_timing.h"

#include <assert.h>
#include <stdio.h>

int main(void)
{
    uint16_t duty;
    uint8_t channel;
    int8_t direction;
    p0_m2a_calibration_t calibration;
    int16_t output[4];

    /* 回归原缺陷：16MHz/800的5%脉冲小于数据手册5us要求。 */
    assert(UINT32_C(800) * UINT32_C(50) / UINT32_C(1000) <
           P0_PWM_TIMER_HZ / UINT32_C(200000));
    assert(P0_PWM_TIMER_HZ / P0_MOTOR_PWM_PERIOD_COUNTS == 5000U);
    assert(p0_pwm_compare_counts(0) == 0);
    for (duty = 0; duty <= 121; ++duty) {
        for (channel = 0; channel < 4; ++channel) {
            for (direction = -1; direction <= 1; direction += 2) {
                bool accepted;
                uint8_t i;
                assert(p0_m2a_calibration_arm(&calibration, 0));
                accepted = p0_m2a_calibration_hold(
                    &calibration, channel, direction, duty, 1, output);
                assert(accepted == (duty >= 50 && duty <= 120));
                for (i = 0; i < 4; ++i) {
                    assert(output[i] == ((accepted && i == channel) ?
                        direction * (int16_t)duty : 0));
                }
                if (accepted) {
                    uint32_t counts = p0_pwm_compare_counts(duty);
                    /* 所有接受的非零请求均>=10us，且舍入不增大占空比。 */
                    assert(counts >= P0_PWM_TIMER_HZ / UINT32_C(100000));
                    assert(counts * 1000U <=
                           (uint32_t)duty * P0_MOTOR_PWM_PERIOD_COUNTS);
                } else {
                    assert(!calibration.armed);
                }
            }
        }
    }
    assert(p0_m2a_calibration_arm(&calibration, 0));
    assert(p0_m2a_calibration_hold(&calibration, 1, 1, 50, 1, output));
    assert(p0_m2a_calibration_hold(&calibration, 1, 0, 0, 2, output));
    for (channel = 0; channel < 4; ++channel) {
        assert(output[channel] == 0);
    }
    puts("PASS: M2-A pulse timing, request range and zero release");
    return 0;
}
