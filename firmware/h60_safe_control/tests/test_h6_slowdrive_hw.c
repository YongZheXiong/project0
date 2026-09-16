/* H6通用单通道候选：MMIO/ARM指令用测试替身，其余执行实际硬件适配源码。 */
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static uint32_t peripheral[0x24000 / 4], core[0x1000 / 4];
static void *mock_addr(uint32_t address)
{
    if (address >= UINT32_C(0x40000000) && address < UINT32_C(0x40024000))
        return &peripheral[(address - UINT32_C(0x40000000)) / 4];
    assert(address >= UINT32_C(0xE000E000) && address < UINT32_C(0xE000F000));
    return &core[(address - UINT32_C(0xE000E000)) / 4];
}

static uint32_t mock_irq_lock(void);
static void mock_irq_unlock(uint32_t saved);
static void model_write(volatile uint32_t *reg, uint32_t value);
#define P0_SLOW_WRITE(reg, value) model_write(&(reg), (value))
#include "p0_hw_stm32f407_mock.c"

static uint32_t irq_mask;
static int interrupt_at;
static unsigned writes;
static bool pending;
static bool injecting;
static bool tracking;
static bool unsafe_entry;
static uint8_t selected_channel;

#if P0_W2_FOUR_WHEEL_PROFILE_BUILD == 0
static void assert_unselected_gpio_output(void)
{
    static const uint32_t e_masks[4] = {
        UINT32_C(0x00CC0000), UINT32_C(0x3C000000),
        UINT32_C(0x00003C00), 0};
    static const uint32_t e_outputs[4] = {
        UINT32_C(0x00440000), UINT32_C(0x14000000),
        UINT32_C(0x00001400), 0};
    for (uint8_t channel = 0; channel < 3; ++channel) {
        if (channel != selected_channel)
            assert((GPIOE->MODER & e_masks[channel]) == e_outputs[channel]);
    }
    if (selected_channel != 3)
        assert((GPIOB->MODER & UINT32_C(0xF0000000)) == UINT32_C(0x50000000));
}
#endif

static void assert_transition_safe(void)
{
#if P0_W2_FOUR_WHEEL_PROFILE_BUILD != 0
    const bool port_e_alternate =
        (GPIOE->MODER & UINT32_C(0x3CCC3C00)) == UINT32_C(0x28882800);
    const bool port_b_alternate =
        (GPIOB->MODER & UINT32_C(0xF0000000)) == UINT32_C(0xA0000000);

    assert(port_e_alternate ||
        (GPIOE->MODER & UINT32_C(0x3CCC3C00)) == UINT32_C(0x14441400));
    assert(port_b_alternate ||
        (GPIOB->MODER & UINT32_C(0xF0000000)) == UINT32_C(0x50000000));
    if (port_e_alternate || port_b_alternate) {
        volatile uint32_t *pairs[][2] = {
            {&TIM1->CCR1, &TIM1->CCR2}, {&TIM1->CCR3, &TIM1->CCR4},
            {&TIM9->CCR1, &TIM9->CCR2}, {&TIM12->CCR1, &TIM12->CCR2},
        };
        assert(TIM1->CR1 == UINT32_C(0x81));
        assert(TIM9->CR1 == UINT32_C(0x81));
        assert(TIM12->CR1 == UINT32_C(0x81));
        assert(TIM1->CCER == UINT32_C(0x1111));
        assert(TIM9->CCER == UINT32_C(0x0011));
        assert(TIM12->CCER == UINT32_C(0x0011));
        assert(TIM1->BDTR == UINT32_C(0x8000));
        for (unsigned i = 0; i < 4; ++i) {
            assert(*pairs[i][0] <= P0_SLOW_PWM_PERIOD_COUNTS);
            assert(*pairs[i][1] <= P0_SLOW_PWM_PERIOD_COUNTS);
            assert(*pairs[i][0] == P0_SLOW_PWM_PERIOD_COUNTS ||
                   *pairs[i][1] == P0_SLOW_PWM_PERIOD_COUNTS);
        }
    }
#else
    p0_slow_io_t io;
    assert(slow_io_select(selected_channel, &io));
    assert_unselected_gpio_output();
    if ((io.gpio->MODER & io.mode_mask) == io.alternate_mode) {
        assert(io.timer->CR1 == UINT32_C(0x81));
        assert(io.timer->CCER == io.ccer_enable);
        assert(io.timer->ARR == P0_SLOW_PWM_ARR);
        assert(*io.ccr_1 <= P0_SLOW_PWM_PERIOD_COUNTS);
        assert(*io.ccr_2 <= P0_SLOW_PWM_PERIOD_COUNTS);
        assert(*io.ccr_1 == P0_SLOW_PWM_PERIOD_COUNTS ||
               *io.ccr_2 == P0_SLOW_PWM_PERIOD_COUNTS);
        if (io.advanced_timer) assert(io.timer->BDTR == UINT32_C(0x8000));
    } else {
        assert((io.gpio->MODER & io.mode_mask) == io.output_mode);
    }
#endif
}

static bool is_reserved_two_channel_register(volatile uint32_t *reg)
{
    tim_regs_t *timers[] = {TIM9, TIM12};
    for (unsigned i = 0; i < 2; ++i) {
        tim_regs_t *timer = timers[i];
        if (reg == &timer->CR2 || reg == &timer->SMCR || reg == &timer->RCR ||
            reg == &timer->CCMR2 || reg == &timer->CCR3 || reg == &timer->CCR4 ||
            reg == &timer->BDTR)
            return true;
    }
    return false;
}

static void trip_now(void)
{
    injecting = true;
    for (unsigned i = 0; i < 101; ++i) SysTick_Handler();
    injecting = false;
    assert(g_supervisor_trip);
}

static uint32_t mock_irq_lock(void)
{
    uint32_t old = irq_mask;
    irq_mask = 1;
    return old;
}

static void mock_irq_unlock(uint32_t saved)
{
    irq_mask = saved;
    if (!irq_mask && pending && !injecting) {
        pending = false;
        trip_now();
    }
}

static void model_write(volatile uint32_t *reg, uint32_t value)
{
    if (tracking && !injecting) assert(!is_reserved_two_channel_register(reg));
    *reg = value;
    if (reg == &GPIOE->BSRR)
        GPIOE->ODR = (GPIOE->ODR | (value & UINT32_C(0xFFFF))) & ~(value >> 16);
    if (reg == &GPIOB->BSRR)
        GPIOB->ODR = (GPIOB->ODR | (value & UINT32_C(0xFFFF))) & ~(value >> 16);
    if (tracking && !injecting) {
        if (!unsafe_entry) assert_transition_safe();
        if ((int)writes == interrupt_at) pending = true;
        ++writes;
    }
}

static void setup(uint8_t channel)
{
    tracking = false;
    memset(peripheral, 0, sizeof(peripheral));
    memset(core, 0, sizeof(core));
    irq_mask = 0;
    pending = false;
    injecting = false;
    unsafe_entry = false;
    interrupt_at = -1;
    writes = 0;
    selected_channel = channel;
    p0_hw_motor_force_safe(0);
    g_millis = 0;
    g_supervisor_trip = 0;
    p0_uart_rx_init(&g_uart_rx);
    tracking = true;
}

static void assert_all_safe(void)
{
    assert((GPIOE->MODER & UINT32_C(0x3CCC3C00)) == UINT32_C(0x14441400));
    assert((GPIOB->MODER & UINT32_C(0xF0000000)) == UINT32_C(0x50000000));
    assert(!(GPIOE->ODR & UINT32_C(0x6A60)));
    assert(!(GPIOB->ODR & UINT32_C(0xC000)));
    assert(TIM1->CR1 == 0 && TIM9->CR1 == 0 && TIM12->CR1 == 0);
    assert(TIM1->CCER == 0 && TIM9->CCER == 0 && TIM12->CCER == 0);
}

static void run_case(uint8_t channel, int8_t direction, uint16_t duty)
{
    p0_m2a_slowdrive_t state;
#if P0_W2_FOUR_WHEEL_PROFILE_BUILD == 0
    p0_slow_io_t io;
#endif
    uint32_t drive;

    setup(channel);
    p0_slow_arm(&state, 0, p0_hw_motor_stop_generation());
    assert(p0_slow_hold(&state, channel, direction, duty, 0,
                        p0_hw_motor_stop_generation()) == P0_SLOW_WAKE);
    assert(p0_hw_slow_commit(&state, P0_SLOW_WAKE, 0));
#if P0_W2_FOUR_WHEEL_PROFILE_BUILD != 0
    assert((GPIOE->MODER & UINT32_C(0x3CCC3C00)) == UINT32_C(0x28882800));
    assert((GPIOB->MODER & UINT32_C(0xF0000000)) == UINT32_C(0xA0000000));
    assert(TIM1->CCR1 == P0_SLOW_PWM_PERIOD_COUNTS);
    assert(TIM1->CCR2 == P0_SLOW_PWM_PERIOD_COUNTS);
    assert(TIM1->CCR3 == P0_SLOW_PWM_PERIOD_COUNTS);
    assert(TIM1->CCR4 == P0_SLOW_PWM_PERIOD_COUNTS);
    assert(TIM9->CCR1 == P0_SLOW_PWM_PERIOD_COUNTS);
    assert(TIM9->CCR2 == P0_SLOW_PWM_PERIOD_COUNTS);
    assert(TIM12->CCR1 == P0_SLOW_PWM_PERIOD_COUNTS);
    assert(TIM12->CCR2 == P0_SLOW_PWM_PERIOD_COUNTS);
#else
    assert(slow_io_select(channel, &io));
    assert((io.gpio->MODER & io.mode_mask) == io.alternate_mode);
    assert(*io.ccr_1 == P0_SLOW_PWM_PERIOD_COUNTS);
    assert(*io.ccr_2 == P0_SLOW_PWM_PERIOD_COUNTS);
#endif
    g_millis = P0_SLOW_WAKE_MS;
    assert(p0_slow_service(&state, g_millis,
                           p0_hw_motor_stop_generation()) == P0_SLOW_RUN);
    drive = (P0_SLOW_PWM_PERIOD_COUNTS * state.duty_permille) /
        UINT32_C(1000);
    assert(p0_hw_slow_commit(&state, P0_SLOW_RUN, 0));
#if P0_W2_FOUR_WHEEL_PROFILE_BUILD != 0
    if (direction == P0_W2_PROFILE_FORWARD_DIRECTION) {
        assert(TIM1->CCR1 == P0_SLOW_PWM_PERIOD_COUNTS - drive);
        assert(TIM1->CCR2 == P0_SLOW_PWM_PERIOD_COUNTS);
        assert(TIM1->CCR3 == P0_SLOW_PWM_PERIOD_COUNTS);
        assert(TIM1->CCR4 == P0_SLOW_PWM_PERIOD_COUNTS - drive);
        assert(TIM9->CCR1 == P0_SLOW_PWM_PERIOD_COUNTS - drive);
        assert(TIM9->CCR2 == P0_SLOW_PWM_PERIOD_COUNTS);
        assert(TIM12->CCR1 == P0_SLOW_PWM_PERIOD_COUNTS);
        assert(TIM12->CCR2 == P0_SLOW_PWM_PERIOD_COUNTS - drive);
    } else {
        assert(TIM1->CCR1 == P0_SLOW_PWM_PERIOD_COUNTS);
        assert(TIM1->CCR2 == P0_SLOW_PWM_PERIOD_COUNTS - drive);
        assert(TIM1->CCR3 == P0_SLOW_PWM_PERIOD_COUNTS - drive);
        assert(TIM1->CCR4 == P0_SLOW_PWM_PERIOD_COUNTS);
        assert(TIM9->CCR1 == P0_SLOW_PWM_PERIOD_COUNTS);
        assert(TIM9->CCR2 == P0_SLOW_PWM_PERIOD_COUNTS - drive);
        assert(TIM12->CCR1 == P0_SLOW_PWM_PERIOD_COUNTS - drive);
        assert(TIM12->CCR2 == P0_SLOW_PWM_PERIOD_COUNTS);
    }
#else
    if (direction > 0) {
        assert(*io.ccr_1 == P0_SLOW_PWM_PERIOD_COUNTS);
        assert(*io.ccr_2 == P0_SLOW_PWM_PERIOD_COUNTS - drive);
    } else {
        assert(*io.ccr_1 == P0_SLOW_PWM_PERIOD_COUNTS - drive);
        assert(*io.ccr_2 == P0_SLOW_PWM_PERIOD_COUNTS);
    }
#endif
    /* 重复WAKE必须在任何重配置前拒绝并统一失能。 */
    assert(!p0_hw_slow_commit(&state, P0_SLOW_WAKE, 0));
    assert_all_safe();
}

int main(void)
{
    unsigned cases = 0;
#if P0_H6_EXTENDED_WINDOW_BUILD == 0 && P0_W2_FOUR_WHEEL_PROFILE_BUILD == 0
    const uint16_t duties[] = {50, 80, 120};
#endif

    assert(P0_H6_CHARACTERIZATION_BUILD == 1);
#if P0_W2_FOUR_WHEEL_PROFILE_BUILD != 0
    assert(P0_W2_FOUR_WHEEL_PROFILE_BUILD == 1);
    run_case(P0_W2_PROFILE_CHANNEL, P0_W2_PROFILE_FORWARD_DIRECTION,
             P0_W2_TARGET_DUTY_PERMILLE);
    run_case(P0_W2_PROFILE_CHANNEL, P0_W2_PROFILE_REVERSE_DIRECTION,
             P0_W2_TARGET_DUTY_PERMILLE);
    cases += 2;
#elif P0_H6_EXTENDED_WINDOW_BUILD != 0
    assert(P0_H6_EXTENDED_WINDOW_BUILD == 1);
    run_case(P0_H6_R2_CHANNEL, P0_H6_R2_DIRECTION,
             P0_H6_R2_TARGET_DUTY_PERMILLE);
    ++cases;
#else
    for (uint8_t channel = 0; channel < 4; ++channel) {
        for (int8_t direction = -1; direction <= 1; direction += 2) {
            for (unsigned i = 0; i < sizeof(duties) / sizeof(duties[0]); ++i) {
                run_case(channel, direction, duties[i]);
                ++cases;
            }
        }
    }
#endif

    /* 任一未选通道不在GPIO低电平时，不得开始所选定时器准备。 */
    {
        p0_m2a_slowdrive_t state;
#if P0_W2_FOUR_WHEEL_PROFILE_BUILD != 0
        uint8_t channel = P0_W2_PROFILE_CHANNEL;
        int8_t direction = P0_W2_PROFILE_FORWARD_DIRECTION;
        uint16_t duty = P0_W2_TARGET_DUTY_PERMILLE;
#elif P0_H6_EXTENDED_WINDOW_BUILD != 0
        uint8_t channel = P0_H6_R2_CHANNEL;
        int8_t direction = P0_H6_R2_DIRECTION;
        uint16_t duty = P0_H6_R2_TARGET_DUTY_PERMILLE;
#else
        uint8_t channel = 0;
        int8_t direction = 1;
        uint16_t duty = 80;
#endif
        setup(channel);
        unsafe_entry = true;
        GPIOE->MODER = (GPIOE->MODER & ~P0_SLOW_MB_MODES) | P0_SLOW_MB_AF;
        p0_slow_arm(&state, 0, p0_hw_motor_stop_generation());
        assert(p0_slow_hold(&state, channel, direction, duty, 0,
                            p0_hw_motor_stop_generation()) == P0_SLOW_WAKE);
        assert(!p0_hw_slow_commit(&state, P0_SLOW_WAKE, 0));
#if P0_W2_FOUR_WHEEL_PROFILE_BUILD == 0
        assert(writes == 22); /* 只允许统一失能事务，没有定时器准备。 */
#endif
        assert_all_safe();
        ++cases;
    }

    /* 每种定时器路径均在提交事务的每个写点注入监督停车。 */
    {
#if P0_W2_FOUR_WHEEL_PROFILE_BUILD != 0
        const uint8_t channels[] = {P0_W2_PROFILE_CHANNEL};
        const int write_points = 96;
#elif P0_H6_EXTENDED_WINDOW_BUILD != 0
        const uint8_t channels[] = {P0_H6_R2_CHANNEL};
        const int write_points = 32;
#else
        const uint8_t channels[] = {0, 1, 2, 3};
        const int write_points = 32;
#endif
        for (unsigned channel_index = 0;
             channel_index < sizeof(channels) / sizeof(channels[0]);
            ++channel_index) {
            uint8_t channel = channels[channel_index];
            for (int point = 0; point < write_points; ++point) {
                p0_m2a_slowdrive_t state;
#if P0_W2_FOUR_WHEEL_PROFILE_BUILD != 0
                int8_t direction = P0_W2_PROFILE_FORWARD_DIRECTION;
                uint16_t duty = P0_W2_TARGET_DUTY_PERMILLE;
#elif P0_H6_EXTENDED_WINDOW_BUILD != 0
                int8_t direction = P0_H6_R2_DIRECTION;
                uint16_t duty = P0_H6_R2_TARGET_DUTY_PERMILLE;
#else
                int8_t direction = 1;
                uint16_t duty = 80;
#endif
                setup(channel);
                interrupt_at = point;
                p0_slow_arm(&state, 0, p0_hw_motor_stop_generation());
                assert(p0_slow_hold(&state, channel, direction, duty, 0,
                                    p0_hw_motor_stop_generation()) ==
                    P0_SLOW_WAKE);
                (void)p0_hw_slow_commit(&state, P0_SLOW_WAKE, 0);
                if (point < (int)writes) {
                    assert(g_supervisor_trip);
                    assert_all_safe();
                    ++cases;
                }
            }
        }
    }

    printf("PASS: H6/W2 hardware %u profile/direction/duty/ISR cases\n", cases);
}
