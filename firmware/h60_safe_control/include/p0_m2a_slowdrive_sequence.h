/* 内部寄存器事务；生产与离线定时器模型共用同一写入顺序。
   调用者持有短PRIMASK事务并检查停止代次；本文件不等待、不发送串口。 */
#ifndef P0_M2A_SLOWDRIVE_SEQUENCE_H
#define P0_M2A_SLOWDRIVE_SEQUENCE_H

#ifndef P0_SLOW_WRITE
#define P0_SLOW_WRITE(reg, value) ((reg) = (value))
#endif

#if P0_H6_CHARACTERIZATION_BUILD != 0

#define P0_SLOW_PWM_PERIOD_COUNTS UINT32_C(3200)
#define P0_SLOW_PWM_ARR UINT32_C(3199)
#define P0_SLOW_MB_PINS UINT32_C(0x6000)
#define P0_SLOW_MB_MODES UINT32_C(0x3C000000)
#define P0_SLOW_MB_OUTPUT UINT32_C(0x14000000)
#define P0_SLOW_MB_AF UINT32_C(0x28000000)

#if P0_W2_FOUR_WHEEL_PROFILE_BUILD == 0
typedef struct {
    gpio_regs_t *gpio;
    tim_regs_t *timer;
    volatile uint32_t *clock_enable;
    volatile uint32_t *clock_reset;
    volatile uint32_t *ccr_1;
    volatile uint32_t *ccr_2;
    uint32_t clock_mask;
    uint32_t pin_mask;
    uint32_t mode_mask;
    uint32_t output_mode;
    uint32_t alternate_mode;
    uint32_t alternate_mask;
    uint32_t alternate_value;
    uint8_t alternate_index;
    uint32_t ccer_enable;
    bool advanced_timer;
} p0_slow_io_t;

static bool slow_io_select(uint8_t channel, p0_slow_io_t *io)
{
    if (io == 0) return false;
    if (channel == UINT8_C(0)) {
        *io = (p0_slow_io_t){
            GPIOE, TIM1, &RCC_APB2ENR, &RCC_APB2RSTR,
            &TIM1->CCR1, &TIM1->CCR2, RCC_APB2_TIM1EN,
            UINT32_C(0x0A00), UINT32_C(0x00CC0000),
            UINT32_C(0x00440000), UINT32_C(0x00880000),
            UINT32_C(0x0000F0F0), UINT32_C(0x00001010),
            UINT8_C(1), UINT32_C(0x0011), true};
        return true;
    }
    if (channel == UINT8_C(1)) {
        *io = (p0_slow_io_t){
            GPIOE, TIM1, &RCC_APB2ENR, &RCC_APB2RSTR,
            &TIM1->CCR3, &TIM1->CCR4, RCC_APB2_TIM1EN,
            UINT32_C(0x6000), UINT32_C(0x3C000000),
            UINT32_C(0x14000000), UINT32_C(0x28000000),
            UINT32_C(0x0FF00000), UINT32_C(0x01100000),
            UINT8_C(1), UINT32_C(0x1100), true};
        return true;
    }
    if (channel == UINT8_C(2)) {
        *io = (p0_slow_io_t){
            GPIOE, TIM9, &RCC_APB2ENR, &RCC_APB2RSTR,
            &TIM9->CCR1, &TIM9->CCR2, RCC_APB2_TIM9EN,
            UINT32_C(0x0060), UINT32_C(0x00003C00),
            UINT32_C(0x00001400), UINT32_C(0x00002800),
            UINT32_C(0x0FF00000), UINT32_C(0x03300000),
            UINT8_C(0), UINT32_C(0x0011), false};
        return true;
    }
    if (channel == UINT8_C(3)) {
        *io = (p0_slow_io_t){
            GPIOB, TIM12, &RCC_APB1ENR, &RCC_APB1RSTR,
            &TIM12->CCR1, &TIM12->CCR2, RCC_APB1_TIM12EN,
            UINT32_C(0xC000), UINT32_C(0xF0000000),
            UINT32_C(0x50000000), UINT32_C(0xA0000000),
            UINT32_C(0xFF000000), UINT32_C(0x99000000),
            UINT8_C(1), UINT32_C(0x0011), false};
        return true;
    }
    return false;
}
#endif

#if P0_W2_FOUR_WHEEL_PROFILE_BUILD != 0

static void slow_w2_timer_prepare(tim_regs_t *timer, bool advanced)
{
    P0_SLOW_WRITE(timer->CR1, UINT32_C(0x80));
    P0_SLOW_WRITE(timer->DIER, 0);
    if (advanced) {
        P0_SLOW_WRITE(timer->CR2, 0);
        P0_SLOW_WRITE(timer->SMCR, 0);
        P0_SLOW_WRITE(timer->BDTR, 0);
    }
    P0_SLOW_WRITE(timer->CCER, 0);
    P0_SLOW_WRITE(timer->PSC, 0);
    P0_SLOW_WRITE(timer->ARR, P0_SLOW_PWM_ARR);
    P0_SLOW_WRITE(timer->CNT, 0);
    if (advanced) P0_SLOW_WRITE(timer->RCR, 0);
    P0_SLOW_WRITE(timer->CCMR1, UINT32_C(0x6868));
    if (advanced) P0_SLOW_WRITE(timer->CCMR2, UINT32_C(0x6868));
    P0_SLOW_WRITE(timer->CCR1, P0_SLOW_PWM_PERIOD_COUNTS);
    P0_SLOW_WRITE(timer->CCR2, P0_SLOW_PWM_PERIOD_COUNTS);
    if (advanced) {
        P0_SLOW_WRITE(timer->CCR3, P0_SLOW_PWM_PERIOD_COUNTS);
        P0_SLOW_WRITE(timer->CCR4, P0_SLOW_PWM_PERIOD_COUNTS);
    }
    P0_SLOW_WRITE(timer->EGR, UINT32_C(1));
    P0_SLOW_WRITE(timer->SR, 0);
    P0_SLOW_WRITE(timer->CCER,
        advanced ? UINT32_C(0x1111) : UINT32_C(0x0011));
    if (advanced) P0_SLOW_WRITE(timer->BDTR, UINT32_C(0x8000));
    P0_SLOW_WRITE(timer->CR1, UINT32_C(0x81));
}

static void slow_io_prepare(const p0_m2a_slowdrive_t *s)
{
    (void)s;
    P0_SLOW_WRITE(RCC_APB2ENR,
        RCC_APB2ENR | RCC_APB2_TIM1EN | RCC_APB2_TIM9EN);
    (void)RCC_APB2ENR;
    P0_SLOW_WRITE(RCC_APB1ENR, RCC_APB1ENR | RCC_APB1_TIM12EN);
    (void)RCC_APB1ENR;
    P0_SLOW_WRITE(RCC_APB2RSTR,
        RCC_APB2RSTR | RCC_APB2_TIM1EN | RCC_APB2_TIM9EN);
    P0_SLOW_WRITE(RCC_APB2RSTR,
        RCC_APB2RSTR & ~(RCC_APB2_TIM1EN | RCC_APB2_TIM9EN));
    P0_SLOW_WRITE(RCC_APB1RSTR, RCC_APB1RSTR | RCC_APB1_TIM12EN);
    P0_SLOW_WRITE(RCC_APB1RSTR, RCC_APB1RSTR & ~RCC_APB1_TIM12EN);

    slow_w2_timer_prepare(TIM1, true);
    slow_w2_timer_prepare(TIM9, false);
    slow_w2_timer_prepare(TIM12, false);
    P0_SLOW_WRITE(GPIOE->AFR[1],
        (GPIOE->AFR[1] & ~UINT32_C(0x0FF0F0F0)) | UINT32_C(0x01101010));
    P0_SLOW_WRITE(GPIOE->AFR[0],
        (GPIOE->AFR[0] & ~UINT32_C(0x0FF00000)) | UINT32_C(0x03300000));
    P0_SLOW_WRITE(GPIOB->AFR[1],
        (GPIOB->AFR[1] & ~UINT32_C(0xFF000000)) | UINT32_C(0x99000000));
    P0_SLOW_WRITE(GPIOE->OSPEEDR,
        (GPIOE->OSPEEDR & ~UINT32_C(0x3CCC3C00)) | UINT32_C(0x28882800));
    P0_SLOW_WRITE(GPIOB->OSPEEDR,
        (GPIOB->OSPEEDR & ~UINT32_C(0xF0000000)) | UINT32_C(0xA0000000));
}

static bool slow_w2_basic_timer_ready(const tim_regs_t *timer)
{
    return timer->CCR1 == P0_SLOW_PWM_PERIOD_COUNTS &&
        timer->CCR2 == P0_SLOW_PWM_PERIOD_COUNTS &&
        timer->ARR == P0_SLOW_PWM_ARR && timer->PSC == 0 &&
        timer->CCMR1 == UINT32_C(0x6868) &&
        timer->CCER == UINT32_C(0x0011) &&
        timer->CR1 == UINT32_C(0x81) && timer->DIER == 0;
}

static bool slow_io_ready(const p0_m2a_slowdrive_t *s)
{
    (void)s;
    return TIM1->CCR1 == P0_SLOW_PWM_PERIOD_COUNTS &&
        TIM1->CCR2 == P0_SLOW_PWM_PERIOD_COUNTS &&
        TIM1->CCR3 == P0_SLOW_PWM_PERIOD_COUNTS &&
        TIM1->CCR4 == P0_SLOW_PWM_PERIOD_COUNTS &&
        TIM1->ARR == P0_SLOW_PWM_ARR && TIM1->PSC == 0 && TIM1->RCR == 0 &&
        TIM1->CCMR1 == UINT32_C(0x6868) &&
        TIM1->CCMR2 == UINT32_C(0x6868) &&
        TIM1->CCER == UINT32_C(0x1111) &&
        TIM1->CR1 == UINT32_C(0x81) &&
        TIM1->BDTR == UINT32_C(0x8000) && TIM1->DIER == 0 &&
        slow_w2_basic_timer_ready(TIM9) && slow_w2_basic_timer_ready(TIM12) &&
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

static bool slow_io_is_alternate(const p0_m2a_slowdrive_t *s)
{
    (void)s;
    return (GPIOE->MODER & UINT32_C(0x3CCC3C00)) == UINT32_C(0x28882800) &&
        (GPIOB->MODER & UINT32_C(0xF0000000)) == UINT32_C(0xA0000000);
}

static bool slow_io_is_safe_gpio(const p0_m2a_slowdrive_t *s)
{
    (void)s;
    return (GPIOE->MODER & UINT32_C(0x3CCC3C00)) == UINT32_C(0x14441400) &&
        (GPIOB->MODER & UINT32_C(0xF0000000)) == UINT32_C(0x50000000) &&
        !(GPIOE->ODR & UINT32_C(0x6A60)) &&
        !(GPIOB->ODR & UINT32_C(0xC000));
}

static void slow_io_wake(const p0_m2a_slowdrive_t *s)
{
    (void)s;
    P0_SLOW_WRITE(GPIOE->BSRR, UINT32_C(0x6A60));
    P0_SLOW_WRITE(GPIOB->BSRR, UINT32_C(0xC000));
    P0_SLOW_WRITE(GPIOE->MODER,
        (GPIOE->MODER & ~UINT32_C(0x3CCC3C00)) | UINT32_C(0x28882800));
    P0_SLOW_WRITE(GPIOB->MODER,
        (GPIOB->MODER & ~UINT32_C(0xF0000000)) | UINT32_C(0xA0000000));
}

static void slow_w2_apply_pair(int8_t direction, uint32_t drive_counts,
    volatile uint32_t *ccr_1, volatile uint32_t *ccr_2)
{
    if (direction > 0) {
        P0_SLOW_WRITE(*ccr_1, P0_SLOW_PWM_PERIOD_COUNTS);
        P0_SLOW_WRITE(*ccr_2, P0_SLOW_PWM_PERIOD_COUNTS - drive_counts);
    } else {
        P0_SLOW_WRITE(*ccr_1, P0_SLOW_PWM_PERIOD_COUNTS - drive_counts);
        P0_SLOW_WRITE(*ccr_2, P0_SLOW_PWM_PERIOD_COUNTS);
    }
}

static void slow_io_run(const p0_m2a_slowdrive_t *s)
{
    uint32_t drive_counts =
        (P0_SLOW_PWM_PERIOD_COUNTS * s->duty_permille) / UINT32_C(1000);

    /* MA/MB/MC/MD车体前向符号为[-1,+1,-1,+1]。 */
    slow_w2_apply_pair((int8_t)-s->direction, drive_counts,
        &TIM1->CCR1, &TIM1->CCR2);
    slow_w2_apply_pair(s->direction, drive_counts,
        &TIM1->CCR3, &TIM1->CCR4);
    slow_w2_apply_pair((int8_t)-s->direction, drive_counts,
        &TIM9->CCR1, &TIM9->CCR2);
    slow_w2_apply_pair(s->direction, drive_counts,
        &TIM12->CCR1, &TIM12->CCR2);
}

#else

static void slow_timer_clear_unselected(uint8_t channel)
{
    if (channel == UINT8_C(0)) {
        P0_SLOW_WRITE(TIM1->CCR3, 0);
        P0_SLOW_WRITE(TIM1->CCR4, 0);
    } else if (channel == UINT8_C(1)) {
        P0_SLOW_WRITE(TIM1->CCR1, 0);
        P0_SLOW_WRITE(TIM1->CCR2, 0);
    }
}

static void slow_io_prepare(const p0_m2a_slowdrive_t *s)
{
    p0_slow_io_t io;

    if (!slow_io_select(s->channel, &io)) return;
    P0_SLOW_WRITE(*io.clock_enable, *io.clock_enable | io.clock_mask);
    (void)*io.clock_enable;
    P0_SLOW_WRITE(*io.clock_reset, *io.clock_reset | io.clock_mask);
    P0_SLOW_WRITE(*io.clock_reset, *io.clock_reset & ~io.clock_mask);
    P0_SLOW_WRITE(io.timer->CR1, UINT32_C(0x80));
    P0_SLOW_WRITE(io.timer->DIER, 0);
    if (io.advanced_timer) {
        P0_SLOW_WRITE(io.timer->CR2, 0);
        P0_SLOW_WRITE(io.timer->SMCR, 0);
        P0_SLOW_WRITE(io.timer->BDTR, 0);
    }
    P0_SLOW_WRITE(io.timer->CCER, 0);
    P0_SLOW_WRITE(io.timer->PSC, 0);
    P0_SLOW_WRITE(io.timer->ARR, P0_SLOW_PWM_ARR);
    P0_SLOW_WRITE(io.timer->CNT, 0);
    if (io.advanced_timer) {
        P0_SLOW_WRITE(io.timer->RCR, 0);
        P0_SLOW_WRITE(io.timer->CCMR1,
            s->channel == UINT8_C(1) ? 0 : UINT32_C(0x6868));
        P0_SLOW_WRITE(io.timer->CCMR2,
            s->channel == UINT8_C(1) ? UINT32_C(0x6868) : 0);
    } else {
        /* TIM9/TIM12是两通道定时器，不访问它们的保留寄存器窗口。 */
        P0_SLOW_WRITE(io.timer->CCMR1, UINT32_C(0x6868));
    }
    P0_SLOW_WRITE(*io.ccr_1, P0_SLOW_PWM_PERIOD_COUNTS);
    P0_SLOW_WRITE(*io.ccr_2, P0_SLOW_PWM_PERIOD_COUNTS);
    slow_timer_clear_unselected(s->channel);
    P0_SLOW_WRITE(io.timer->EGR, UINT32_C(1));
    P0_SLOW_WRITE(io.timer->SR, 0);
    P0_SLOW_WRITE(io.gpio->AFR[io.alternate_index],
        (io.gpio->AFR[io.alternate_index] & ~io.alternate_mask) |
        io.alternate_value);
    P0_SLOW_WRITE(io.gpio->OSPEEDR,
        (io.gpio->OSPEEDR & ~io.mode_mask) | io.alternate_mode);
    P0_SLOW_WRITE(io.timer->CCER, io.ccer_enable);
    if (io.advanced_timer) P0_SLOW_WRITE(io.timer->BDTR, UINT32_C(0x8000));
    P0_SLOW_WRITE(io.timer->CR1, UINT32_C(0x81));
}

static bool slow_io_ready(const p0_m2a_slowdrive_t *s)
{
    p0_slow_io_t io;
    bool timer_ready;

    if (!slow_io_select(s->channel, &io)) return false;
    timer_ready = *io.ccr_1 == P0_SLOW_PWM_PERIOD_COUNTS &&
        *io.ccr_2 == P0_SLOW_PWM_PERIOD_COUNTS &&
        io.timer->ARR == P0_SLOW_PWM_ARR && io.timer->PSC == 0 &&
        io.timer->CCER == io.ccer_enable &&
        io.timer->CR1 == UINT32_C(0x81) && io.timer->DIER == 0 &&
        (*io.clock_enable & io.clock_mask) != 0;
    if (io.advanced_timer) {
        timer_ready = timer_ready && io.timer->RCR == 0 &&
            io.timer->BDTR == UINT32_C(0x8000) &&
            io.timer->CCMR1 == (s->channel == UINT8_C(1) ? 0 : UINT32_C(0x6868)) &&
            io.timer->CCMR2 == (s->channel == UINT8_C(1) ? UINT32_C(0x6868) : 0) &&
            (s->channel == UINT8_C(0) ?
                (TIM1->CCR3 == 0 && TIM1->CCR4 == 0) :
                (TIM1->CCR1 == 0 && TIM1->CCR2 == 0));
    } else {
        timer_ready = timer_ready && io.timer->CCMR1 == UINT32_C(0x6868);
    }
    return timer_ready &&
        (io.gpio->MODER & io.mode_mask) == io.output_mode &&
        !(io.gpio->ODR & io.pin_mask) &&
        (io.gpio->AFR[io.alternate_index] & io.alternate_mask) ==
            io.alternate_value;
}

static bool slow_io_is_alternate(const p0_m2a_slowdrive_t *s)
{
    p0_slow_io_t io;
    return slow_io_select(s->channel, &io) &&
        (io.gpio->MODER & io.mode_mask) == io.alternate_mode;
}

static bool slow_io_is_safe_gpio(const p0_m2a_slowdrive_t *s)
{
    p0_slow_io_t io;
    return slow_io_select(s->channel, &io) &&
        (GPIOE->MODER & UINT32_C(0x3CCC3C00)) == UINT32_C(0x14441400) &&
        (GPIOB->MODER & UINT32_C(0xF0000000)) == UINT32_C(0x50000000) &&
        !(GPIOE->ODR & UINT32_C(0x6A60)) &&
        !(GPIOB->ODR & UINT32_C(0xC000));
}

static void slow_io_wake(const p0_m2a_slowdrive_t *s)
{
    p0_slow_io_t io;
    if (!slow_io_select(s->channel, &io)) return;
    P0_SLOW_WRITE(io.gpio->BSRR, io.pin_mask);
    P0_SLOW_WRITE(io.gpio->MODER,
        (io.gpio->MODER & ~io.mode_mask) | io.alternate_mode);
}

static void slow_io_run(const p0_m2a_slowdrive_t *s)
{
    p0_slow_io_t io;
    uint32_t drive_counts;

    if (!slow_io_select(s->channel, &io)) return;
    drive_counts = (P0_SLOW_PWM_PERIOD_COUNTS * s->duty_permille) /
        UINT32_C(1000);
    if (s->direction > 0) {
        P0_SLOW_WRITE(*io.ccr_1, P0_SLOW_PWM_PERIOD_COUNTS);
        P0_SLOW_WRITE(*io.ccr_2, P0_SLOW_PWM_PERIOD_COUNTS - drive_counts);
    } else {
        P0_SLOW_WRITE(*io.ccr_1, P0_SLOW_PWM_PERIOD_COUNTS - drive_counts);
        P0_SLOW_WRITE(*io.ccr_2, P0_SLOW_PWM_PERIOD_COUNTS);
    }
}

#endif

static void slow_io_off(void)
{
    const uint32_t port_e_pins = UINT32_C(0x6A60);
    const uint32_t port_b_pins = UINT32_C(0xC000);

    P0_SLOW_WRITE(GPIOE->BSRR, port_e_pins << 16);
    P0_SLOW_WRITE(GPIOB->BSRR, port_b_pins << 16);
    P0_SLOW_WRITE(GPIOE->MODER,
        (GPIOE->MODER & ~UINT32_C(0x3CCC3C00)) | UINT32_C(0x14441400));
    P0_SLOW_WRITE(GPIOB->MODER,
        (GPIOB->MODER & ~UINT32_C(0xF0000000)) | UINT32_C(0x50000000));
    P0_SLOW_WRITE(TIM1->BDTR, 0);
    P0_SLOW_WRITE(TIM1->CR1, 0);
    P0_SLOW_WRITE(TIM9->CR1, 0);
    P0_SLOW_WRITE(TIM12->CR1, 0);
    P0_SLOW_WRITE(TIM1->CCER, 0);
    P0_SLOW_WRITE(TIM9->CCER, 0);
    P0_SLOW_WRITE(TIM12->CCER, 0);
    P0_SLOW_WRITE(TIM1->DIER, 0);
    P0_SLOW_WRITE(TIM9->DIER, 0);
    P0_SLOW_WRITE(TIM12->DIER, 0);
    P0_SLOW_WRITE(TIM1->CCR1, 0);
    P0_SLOW_WRITE(TIM1->CCR2, 0);
    P0_SLOW_WRITE(TIM1->CCR3, 0);
    P0_SLOW_WRITE(TIM1->CCR4, 0);
    P0_SLOW_WRITE(TIM9->CCR1, 0);
    P0_SLOW_WRITE(TIM9->CCR2, 0);
    P0_SLOW_WRITE(TIM12->CCR1, 0);
    P0_SLOW_WRITE(TIM12->CCR2, 0);
}

#else

#define P0_SLOW_MB_PINS UINT32_C(0x6000)
#define P0_SLOW_MB_MODES UINT32_C(0x3C000000)
#define P0_SLOW_MB_OUTPUT UINT32_C(0x14000000)
#define P0_SLOW_MB_AF UINT32_C(0x28000000)

static void slow_io_prepare(void)
{
    /* 两脚仍GPIO00，复位TIM1后先装入配对11；更新事件不可见于引脚。 */
    P0_SLOW_WRITE(RCC_APB2ENR, RCC_APB2ENR | RCC_APB2_TIM1EN);
    (void)RCC_APB2ENR;
    P0_SLOW_WRITE(RCC_APB2RSTR, RCC_APB2RSTR | UINT32_C(1));
    P0_SLOW_WRITE(RCC_APB2RSTR, RCC_APB2RSTR & ~UINT32_C(1));
    P0_SLOW_WRITE(TIM1->CR1, UINT32_C(0x80));
    P0_SLOW_WRITE(TIM1->CR2, 0);
    P0_SLOW_WRITE(TIM1->SMCR, 0);
    P0_SLOW_WRITE(TIM1->DIER, 0);
    P0_SLOW_WRITE(TIM1->BDTR, 0);
    P0_SLOW_WRITE(TIM1->CCER, 0);
    P0_SLOW_WRITE(TIM1->PSC, 0);
    P0_SLOW_WRITE(TIM1->ARR, UINT32_C(3199));
    P0_SLOW_WRITE(TIM1->RCR, 0);
    P0_SLOW_WRITE(TIM1->CNT, 0);
    P0_SLOW_WRITE(TIM1->CCMR1, 0);
    P0_SLOW_WRITE(TIM1->CCMR2, UINT32_C(0x6868));
    P0_SLOW_WRITE(TIM1->CCR1, 0);
    P0_SLOW_WRITE(TIM1->CCR2, 0);
    P0_SLOW_WRITE(TIM1->CCR3, UINT32_C(3200));
    P0_SLOW_WRITE(TIM1->CCR4, UINT32_C(3200));
    P0_SLOW_WRITE(TIM1->EGR, UINT32_C(1));
    P0_SLOW_WRITE(TIM1->SR, 0);
    P0_SLOW_WRITE(GPIOE->AFR[1],
        (GPIOE->AFR[1] & ~UINT32_C(0x0FF00000)) | UINT32_C(0x01100000));
    P0_SLOW_WRITE(GPIOE->OSPEEDR,
        (GPIOE->OSPEEDR & ~P0_SLOW_MB_MODES) | P0_SLOW_MB_AF);
    P0_SLOW_WRITE(TIM1->CCER, UINT32_C(0x1100));
    P0_SLOW_WRITE(TIM1->BDTR, UINT32_C(0x8000));
    P0_SLOW_WRITE(TIM1->CR1, UINT32_C(0x81));
}

static bool slow_io_ready(void)
{
    /* 读回只证明软件可见配置，不能替代引脚波形。 */
    return TIM1->CCR3 == 3200 && TIM1->CCR4 == 3200 &&
        TIM1->ARR == 3199 && TIM1->PSC == 0 && TIM1->RCR == 0 &&
        TIM1->CCMR2 == UINT32_C(0x6868) && TIM1->CCER == UINT32_C(0x1100) &&
        TIM1->CR1 == UINT32_C(0x81) && TIM1->BDTR == UINT32_C(0x8000) &&
        TIM1->DIER == 0 &&
        (GPIOE->MODER & P0_SLOW_MB_MODES) == P0_SLOW_MB_OUTPUT;
}

static void slow_io_wake(void)
{
    P0_SLOW_WRITE(GPIOE->BSRR, P0_SLOW_MB_PINS);
    P0_SLOW_WRITE(GPIOE->MODER,
        (GPIOE->MODER & ~P0_SLOW_MB_MODES) | P0_SLOW_MB_AF);
}

static void slow_io_run(void)
{
    /* CCR3永不改为0；只更新CCR4预装载，等待自然UEV，不发UG。 */
    P0_SLOW_WRITE(TIM1->CCR4, UINT32_C(3040));
}

static void slow_io_off(void)
{
    /* 先配对接回GPIO00，后清比较寄存器，避免预装载清零次序影响焊盘。 */
    P0_SLOW_WRITE(GPIOE->BSRR, P0_SLOW_MB_PINS << 16);
    P0_SLOW_WRITE(GPIOE->MODER,
        (GPIOE->MODER & ~P0_SLOW_MB_MODES) | P0_SLOW_MB_OUTPUT);
    P0_SLOW_WRITE(TIM1->BDTR, 0);
    P0_SLOW_WRITE(TIM1->CR1, 0);
    P0_SLOW_WRITE(TIM1->CCER, 0);
    P0_SLOW_WRITE(TIM1->DIER, 0);
    P0_SLOW_WRITE(TIM1->CCR3, 0);
    P0_SLOW_WRITE(TIM1->CCR4, 0);
}

#endif

#endif
