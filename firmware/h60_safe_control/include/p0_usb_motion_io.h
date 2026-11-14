/* Isolated experimental PWM transaction, derived from the existing W2 sequence. */
#ifndef P0_USB_MOTION_IO_H
#define P0_USB_MOTION_IO_H
#ifndef P0_UM_WRITE
#define P0_UM_WRITE(reg, value) ((reg) = (value))
#endif
#define P0_UM_PWM_PERIOD_COUNTS UINT32_C(3200)
#define P0_UM_PWM_ARR UINT32_C(3199)
static void um_w2_timer_prepare(tim_regs_t *timer, bool advanced)
{
    P0_UM_WRITE(timer->CR1, UINT32_C(0x80));
    P0_UM_WRITE(timer->DIER, 0);
    if (advanced) {
        P0_UM_WRITE(timer->CR2, 0);
        P0_UM_WRITE(timer->SMCR, 0);
        P0_UM_WRITE(timer->BDTR, 0);
    }
    P0_UM_WRITE(timer->CCER, 0);
    P0_UM_WRITE(timer->PSC, 0);
    P0_UM_WRITE(timer->ARR, P0_UM_PWM_ARR);
    P0_UM_WRITE(timer->CNT, 0);
    if (advanced) P0_UM_WRITE(timer->RCR, 0);
    P0_UM_WRITE(timer->CCMR1, UINT32_C(0x6868));
    if (advanced) P0_UM_WRITE(timer->CCMR2, UINT32_C(0x6868));
    P0_UM_WRITE(timer->CCR1, P0_UM_PWM_PERIOD_COUNTS);
    P0_UM_WRITE(timer->CCR2, P0_UM_PWM_PERIOD_COUNTS);
    if (advanced) {
        P0_UM_WRITE(timer->CCR3, P0_UM_PWM_PERIOD_COUNTS);
        P0_UM_WRITE(timer->CCR4, P0_UM_PWM_PERIOD_COUNTS);
    }
    P0_UM_WRITE(timer->EGR, UINT32_C(1));
    P0_UM_WRITE(timer->SR, 0);
    P0_UM_WRITE(timer->CCER,
        advanced ? UINT32_C(0x1111) : UINT32_C(0x0011));
    if (advanced) P0_UM_WRITE(timer->BDTR, UINT32_C(0x8000));
    P0_UM_WRITE(timer->CR1, UINT32_C(0x81));
}

static void um_io_prepare(const p0_m2a_slowdrive_t *s)
{
    (void)s;
    P0_UM_WRITE(RCC_APB2ENR,
        RCC_APB2ENR | RCC_APB2_TIM1EN | RCC_APB2_TIM9EN);
    (void)RCC_APB2ENR;
    P0_UM_WRITE(RCC_APB1ENR, RCC_APB1ENR | RCC_APB1_TIM12EN);
    (void)RCC_APB1ENR;
    P0_UM_WRITE(RCC_APB2RSTR,
        RCC_APB2RSTR | RCC_APB2_TIM1EN | RCC_APB2_TIM9EN);
    P0_UM_WRITE(RCC_APB2RSTR,
        RCC_APB2RSTR & ~(RCC_APB2_TIM1EN | RCC_APB2_TIM9EN));
    P0_UM_WRITE(RCC_APB1RSTR, RCC_APB1RSTR | RCC_APB1_TIM12EN);
    P0_UM_WRITE(RCC_APB1RSTR, RCC_APB1RSTR & ~RCC_APB1_TIM12EN);

    um_w2_timer_prepare(TIM1, true);
    um_w2_timer_prepare(TIM9, false);
    um_w2_timer_prepare(TIM12, false);
    P0_UM_WRITE(GPIOE->AFR[1],
        (GPIOE->AFR[1] & ~UINT32_C(0x0FF0F0F0)) | UINT32_C(0x01101010));
    P0_UM_WRITE(GPIOE->AFR[0],
        (GPIOE->AFR[0] & ~UINT32_C(0x0FF00000)) | UINT32_C(0x03300000));
    P0_UM_WRITE(GPIOB->AFR[1],
        (GPIOB->AFR[1] & ~UINT32_C(0xFF000000)) | UINT32_C(0x99000000));
    P0_UM_WRITE(GPIOE->OSPEEDR,
        (GPIOE->OSPEEDR & ~UINT32_C(0x3CCC3C00)) | UINT32_C(0x28882800));
    P0_UM_WRITE(GPIOB->OSPEEDR,
        (GPIOB->OSPEEDR & ~UINT32_C(0xF0000000)) | UINT32_C(0xA0000000));
}

static bool um_w2_basic_timer_ready(const tim_regs_t *timer)
{
    return timer->CCR1 == P0_UM_PWM_PERIOD_COUNTS &&
        timer->CCR2 == P0_UM_PWM_PERIOD_COUNTS &&
        timer->ARR == P0_UM_PWM_ARR && timer->PSC == 0 &&
        timer->CCMR1 == UINT32_C(0x6868) &&
        timer->CCER == UINT32_C(0x0011) &&
        timer->CR1 == UINT32_C(0x81) && timer->DIER == 0;
}

static bool um_io_ready(const p0_m2a_slowdrive_t *s)
{
    (void)s;
    return TIM1->CCR1 == P0_UM_PWM_PERIOD_COUNTS &&
        TIM1->CCR2 == P0_UM_PWM_PERIOD_COUNTS &&
        TIM1->CCR3 == P0_UM_PWM_PERIOD_COUNTS &&
        TIM1->CCR4 == P0_UM_PWM_PERIOD_COUNTS &&
        TIM1->ARR == P0_UM_PWM_ARR && TIM1->PSC == 0 && TIM1->RCR == 0 &&
        TIM1->CCMR1 == UINT32_C(0x6868) &&
        TIM1->CCMR2 == UINT32_C(0x6868) &&
        TIM1->CCER == UINT32_C(0x1111) &&
        TIM1->CR1 == UINT32_C(0x81) &&
        TIM1->BDTR == UINT32_C(0x8000) && TIM1->DIER == 0 &&
        um_w2_basic_timer_ready(TIM9) && um_w2_basic_timer_ready(TIM12) &&
        (RCC_APB2ENR & (RCC_APB2_TIM1EN | RCC_APB2_TIM9EN)) ==
            (RCC_APB2_TIM1EN | RCC_APB2_TIM9EN) &&
        (RCC_APB1ENR & RCC_APB1_TIM12EN) != 0 &&
        (GPIOE->MODER & UINT32_C(0x3CCC3C00)) == UINT32_C(0x14441400) &&
        (GPIOB->MODER & UINT32_C(0xF0000000)) == UINT32_C(0x50000000) &&
        !(GPIOE->ODR & UINT32_C(0x6A60)) &&
        !(GPIOB->ODR & UINT32_C(0xC000)) &&
        (GPIOE->AFR[1] & UINT32_C(0x0FF0F0F0)) == UINT32_C(0x01101010) &&
        (GPIOE->AFR[0] & UINT32_C(0x0FF00000)) == UINT32_C(0x03300000) &&
        (GPIOB->AFR[1] & UINT32_C(0xFF000000)) == UINT32_C(0x99000000);
}

static bool um_io_is_alternate(const p0_m2a_slowdrive_t *s)
{
    (void)s;
    return (GPIOE->MODER & UINT32_C(0x3CCC3C00)) == UINT32_C(0x28882800) &&
        (GPIOB->MODER & UINT32_C(0xF0000000)) == UINT32_C(0xA0000000);
}

static bool um_io_is_safe_gpio(const p0_m2a_slowdrive_t *s)
{
    (void)s;
    return (GPIOE->MODER & UINT32_C(0x3CCC3C00)) == UINT32_C(0x14441400) &&
        (GPIOB->MODER & UINT32_C(0xF0000000)) == UINT32_C(0x50000000) &&
        !(GPIOE->ODR & UINT32_C(0x6A60)) &&
        !(GPIOB->ODR & UINT32_C(0xC000));
}

static void um_io_wake(const p0_m2a_slowdrive_t *s)
{
    (void)s;
    P0_UM_WRITE(GPIOE->BSRR, UINT32_C(0x6A60));
    P0_UM_WRITE(GPIOB->BSRR, UINT32_C(0xC000));
    P0_UM_WRITE(GPIOE->MODER,
        (GPIOE->MODER & ~UINT32_C(0x3CCC3C00)) | UINT32_C(0x28882800));
    P0_UM_WRITE(GPIOB->MODER,
        (GPIOB->MODER & ~UINT32_C(0xF0000000)) | UINT32_C(0xA0000000));
}

static void um_w2_apply_pair(int8_t direction, uint32_t drive_counts,
    volatile uint32_t *ccr_1, volatile uint32_t *ccr_2)
{
    if (direction > 0) {
        P0_UM_WRITE(*ccr_1, P0_UM_PWM_PERIOD_COUNTS);
        P0_UM_WRITE(*ccr_2, P0_UM_PWM_PERIOD_COUNTS - drive_counts);
    } else {
        P0_UM_WRITE(*ccr_1, P0_UM_PWM_PERIOD_COUNTS - drive_counts);
        P0_UM_WRITE(*ccr_2, P0_UM_PWM_PERIOD_COUNTS);
    }
}

static void um_io_off(void)
{
    const uint32_t port_e_pins = UINT32_C(0x6A60);
    const uint32_t port_b_pins = UINT32_C(0xC000);

    P0_UM_WRITE(GPIOE->BSRR, port_e_pins << 16);
    P0_UM_WRITE(GPIOB->BSRR, port_b_pins << 16);
    P0_UM_WRITE(GPIOE->MODER,
        (GPIOE->MODER & ~UINT32_C(0x3CCC3C00)) | UINT32_C(0x14441400));
    P0_UM_WRITE(GPIOB->MODER,
        (GPIOB->MODER & ~UINT32_C(0xF0000000)) | UINT32_C(0x50000000));
    P0_UM_WRITE(TIM1->BDTR, 0);
    P0_UM_WRITE(TIM1->CR1, 0);
    P0_UM_WRITE(TIM9->CR1, 0);
    P0_UM_WRITE(TIM12->CR1, 0);
    P0_UM_WRITE(TIM1->CCER, 0);
    P0_UM_WRITE(TIM9->CCER, 0);
    P0_UM_WRITE(TIM12->CCER, 0);
    P0_UM_WRITE(TIM1->DIER, 0);
    P0_UM_WRITE(TIM9->DIER, 0);
    P0_UM_WRITE(TIM12->DIER, 0);
    P0_UM_WRITE(TIM1->CCR1, 0);
    P0_UM_WRITE(TIM1->CCR2, 0);
    P0_UM_WRITE(TIM1->CCR3, 0);
    P0_UM_WRITE(TIM1->CCR4, 0);
    P0_UM_WRITE(TIM9->CCR1, 0);
    P0_UM_WRITE(TIM9->CCR2, 0);
    P0_UM_WRITE(TIM12->CCR1, 0);
    P0_UM_WRITE(TIM12->CCR2, 0);
}

static void um_io_run(const int16_t output[4])
{
    static const int8_t signs[4] = {-1, 1, -1, 1};
    volatile uint32_t *pairs[4][2] = {
        {&TIM1->CCR1, &TIM1->CCR2}, {&TIM1->CCR3, &TIM1->CCR4},
        {&TIM9->CCR1, &TIM9->CCR2}, {&TIM12->CCR1, &TIM12->CCR2},
    };
    for (uint8_t i = 0; i < 4; ++i) {
        int16_t value = (int16_t)(output[i] * signs[i]);
        uint32_t magnitude = (uint32_t)(value < 0 ? -value : value);
        um_w2_apply_pair(value > 0 ? 1 : -1,
            P0_UM_PWM_PERIOD_COUNTS * magnitude / UINT32_C(1000),
            pairs[i][0], pairs[i][1]);
    }
}
#endif
