#include "p0_hw.h"
#include "p0_build_config.h"
#include "p0_m2a_calibration.h"
#include "p0_motion.h"
#include "p0_pwm_timing.h"
#include "p0_uart_rx.h"

#include <stdint.h>

typedef struct {
    volatile uint32_t MODER;
    volatile uint32_t OTYPER;
    volatile uint32_t OSPEEDR;
    volatile uint32_t PUPDR;
    volatile uint32_t IDR;
    volatile uint32_t ODR;
    volatile uint32_t BSRR;
    volatile uint32_t LCKR;
    volatile uint32_t AFR[2];
} gpio_regs_t;

typedef struct {
    volatile uint32_t CR1;
    volatile uint32_t CR2;
    volatile uint32_t SMCR;
    volatile uint32_t DIER;
    volatile uint32_t SR;
    volatile uint32_t EGR;
    volatile uint32_t CCMR1;
    volatile uint32_t CCMR2;
    volatile uint32_t CCER;
    volatile uint32_t CNT;
    volatile uint32_t PSC;
    volatile uint32_t ARR;
    volatile uint32_t RCR;
    volatile uint32_t CCR1;
    volatile uint32_t CCR2;
    volatile uint32_t CCR3;
    volatile uint32_t CCR4;
    volatile uint32_t BDTR;
    volatile uint32_t DCR;
    volatile uint32_t DMAR;
} tim_regs_t;

typedef struct {
    volatile uint32_t SR;
    volatile uint32_t DR;
    volatile uint32_t BRR;
    volatile uint32_t CR1;
    volatile uint32_t CR2;
    volatile uint32_t CR3;
} usart_regs_t;

typedef struct {
    volatile uint32_t SR;
    volatile uint32_t CR1;
    volatile uint32_t CR2;
    volatile uint32_t SMPR1;
    volatile uint32_t SMPR2;
    volatile uint32_t JOFR1;
    volatile uint32_t JOFR2;
    volatile uint32_t JOFR3;
    volatile uint32_t JOFR4;
    volatile uint32_t HTR;
    volatile uint32_t LTR;
    volatile uint32_t SQR1;
    volatile uint32_t SQR2;
    volatile uint32_t SQR3;
    volatile uint32_t JSQR;
    volatile uint32_t JDR1;
    volatile uint32_t JDR2;
    volatile uint32_t JDR3;
    volatile uint32_t JDR4;
    volatile uint32_t DR;
} adc_regs_t;

typedef struct {
    volatile uint32_t CTRL;
    volatile uint32_t LOAD;
    volatile uint32_t VAL;
    volatile uint32_t CALIB;
} systick_regs_t;

#define REG32(address) (*(volatile uint32_t *)(uintptr_t)(address))

#define RCC_CR REG32(UINT32_C(0x40023800))
#define RCC_CFGR REG32(UINT32_C(0x40023808))
#define RCC_APB2RSTR REG32(UINT32_C(0x40023824))
#define RCC_AHB1ENR REG32(UINT32_C(0x40023830))
#define RCC_APB1ENR REG32(UINT32_C(0x40023840))
#define RCC_APB2ENR REG32(UINT32_C(0x40023844))

#define GPIOA ((gpio_regs_t *)(uintptr_t)UINT32_C(0x40020000))
#define GPIOB ((gpio_regs_t *)(uintptr_t)UINT32_C(0x40020400))
#define GPIOC ((gpio_regs_t *)(uintptr_t)UINT32_C(0x40020800))
#define GPIOD ((gpio_regs_t *)(uintptr_t)UINT32_C(0x40020C00))
#define GPIOE ((gpio_regs_t *)(uintptr_t)UINT32_C(0x40021000))

#define TIM2 ((tim_regs_t *)(uintptr_t)UINT32_C(0x40000000))
#define TIM3 ((tim_regs_t *)(uintptr_t)UINT32_C(0x40000400))
#define TIM4 ((tim_regs_t *)(uintptr_t)UINT32_C(0x40000800))
#define TIM5 ((tim_regs_t *)(uintptr_t)UINT32_C(0x40000C00))
#define TIM12 ((tim_regs_t *)(uintptr_t)UINT32_C(0x40001800))
#define TIM1 ((tim_regs_t *)(uintptr_t)UINT32_C(0x40010000))
#define TIM9 ((tim_regs_t *)(uintptr_t)UINT32_C(0x40014000))

#define USART3 ((usart_regs_t *)(uintptr_t)UINT32_C(0x40004800))
#define ADC2 ((adc_regs_t *)(uintptr_t)UINT32_C(0x40012100))
#define SYSTICK ((systick_regs_t *)(uintptr_t)UINT32_C(0xE000E010))

#define SCB_AIRCR REG32(UINT32_C(0xE000ED0C))
#define NVIC_ISER1 REG32(UINT32_C(0xE000E104))
#define NVIC_ICPR1 REG32(UINT32_C(0xE000E284))
#define NVIC_USART3_PRIORITY \
    (*(volatile uint8_t *)(uintptr_t)UINT32_C(0xE000E427))

#define IWDG_KR REG32(UINT32_C(0x40003000))
#define IWDG_PR REG32(UINT32_C(0x40003004))
#define IWDG_RLR REG32(UINT32_C(0x40003008))
#define IWDG_SR REG32(UINT32_C(0x4000300C))

#define IWDG_SR_UPDATE_MASK UINT32_C(0x3)
#define IWDG_UPDATE_TIMEOUT_CYCLES UINT32_C(1000000)

#define RCC_AHB1_GPIOAEN (UINT32_C(1) << 0)
#define RCC_AHB1_GPIOBEN (UINT32_C(1) << 1)
#define RCC_AHB1_GPIOCEN (UINT32_C(1) << 2)
#define RCC_AHB1_GPIODEN (UINT32_C(1) << 3)
#define RCC_AHB1_GPIOEEN (UINT32_C(1) << 4)

#define RCC_APB1_TIM2EN (UINT32_C(1) << 0)
#define RCC_APB1_TIM3EN (UINT32_C(1) << 1)
#define RCC_APB1_TIM4EN (UINT32_C(1) << 2)
#define RCC_APB1_TIM5EN (UINT32_C(1) << 3)
#define RCC_APB1_TIM12EN (UINT32_C(1) << 6)
#define RCC_APB1_USART3EN (UINT32_C(1) << 18)
#define RCC_APB2_TIM1EN (UINT32_C(1) << 0)
#define RCC_APB2_ADC2EN (UINT32_C(1) << 9)
#define RCC_APB2_TIM9EN (UINT32_C(1) << 16)

#define USART_SR_RXNE (UINT32_C(1) << 5)
#define USART_SR_RX_ERROR_MASK UINT32_C(0xF) /* PE/FE/NE/ORE */
#define USART_SR_TXE (UINT32_C(1) << 7)
#define USART_CR1_RE (UINT32_C(1) << 2)
#define USART_CR1_TE (UINT32_C(1) << 3)
#define USART_CR1_RXNEIE (UINT32_C(1) << 5)
#define USART_CR1_PEIE (UINT32_C(1) << 8)
#define USART_CR1_UE (UINT32_C(1) << 13)
#define USART_CR3_EIE UINT32_C(1)

#define ADC_SR_EOC (UINT32_C(1) << 1)
#define ADC_CR2_ADON (UINT32_C(1) << 0)
#define ADC_CR2_SWSTART (UINT32_C(1) << 30)

static volatile uint32_t g_millis;
static volatile uint32_t g_main_epoch;
static volatile uint32_t g_supervisor_trip;
static p0_uart_rx_t g_uart_rx;
static bool g_motor_pwm_initialized;
static int8_t g_motor_direction[4];
#if P0_M2A_SLOWDRIVE_BUILD != 0
static volatile uint32_t g_motor_stop_generation;
#include "p0_m2a_slowdrive_sequence.h"

static uint32_t slow_irq_lock(void)
{
    uint32_t primask;
    __asm volatile("mrs %0, primask\ncpsid i" : "=r"(primask) :: "memory");
    return primask;
}

static void slow_irq_unlock(uint32_t primask)
{
    __asm volatile("dsb\nmsr primask, %0" :: "r"(primask) : "memory");
}

uint32_t p0_hw_motor_stop_generation(void)
{
    return g_motor_stop_generation;
}

static bool slow_permitted(const p0_m2a_slowdrive_t *s, uint32_t heartbeat)
{
    uint32_t now = g_millis;
    return !g_supervisor_trip && !g_uart_rx.fault &&
        !(USART3->SR & USART_SR_RX_ERROR_MASK) &&
        (uint32_t)(now - heartbeat) <= UINT32_C(250) &&
        p0_slow_fresh(s, now, g_motor_stop_generation);
}

bool p0_hw_slow_commit(p0_m2a_slowdrive_t *s, p0_slow_action_t action,
    uint32_t last_heartbeat_ms)
{
    uint32_t primask = slow_irq_lock();
    bool ok = slow_permitted(s, last_heartbeat_ms);
    if (ok && action == P0_SLOW_WAKE && s->phase == P0_SLOW_WAKING &&
        (GPIOE->MODER & P0_SLOW_MB_MODES) == P0_SLOW_MB_OUTPUT &&
        !(GPIOE->ODR & P0_SLOW_MB_PINS)) {
        slow_io_prepare();
        ok = slow_io_ready() && slow_permitted(s, last_heartbeat_ms);
        if (ok) {
            slow_io_wake();
            s->wake_at_ms = g_millis;
        }
    } else if (ok && action == P0_SLOW_RUN && s->phase == P0_SLOW_ACTIVE &&
               (uint32_t)(g_millis - s->wake_at_ms) >= P0_SLOW_WAKE_MS &&
               (GPIOE->MODER & P0_SLOW_MB_MODES) == P0_SLOW_MB_AF) {
        slow_io_run();
    } else {
        ok = false;
    }
    if (!ok) p0_hw_motor_force_safe(0);
    slow_irq_unlock(primask);
    return ok;
}
#endif
static p0_hw_retained_fault_t g_retained_fault
    __attribute__((section(".noinit")));

static void gpio_set_mode(gpio_regs_t *gpio, uint8_t pin, uint32_t mode)
{
    uint32_t shift = (uint32_t)pin * UINT32_C(2);
    uint32_t value = gpio->MODER;

    value &= ~(UINT32_C(3) << shift);
    value |= (mode & UINT32_C(3)) << shift;
    gpio->MODER = value;
}

static void gpio_set_af(gpio_regs_t *gpio, uint8_t pin, uint8_t af)
{
    uint32_t index = (uint32_t)pin >> 3;
    uint32_t shift = ((uint32_t)pin & UINT32_C(7)) * UINT32_C(4);
    uint32_t value = gpio->AFR[index];

    value &= ~(UINT32_C(0xF) << shift);
    value |= ((uint32_t)af & UINT32_C(0xF)) << shift;
    gpio->AFR[index] = value;
}

static void gpio_config_output_low(gpio_regs_t *gpio, uint8_t pin)
{
    uint32_t pin_mask = UINT32_C(1) << pin;
    uint32_t shift = (uint32_t)pin * UINT32_C(2);

    gpio->BSRR = pin_mask << 16;
    gpio->OTYPER &= ~pin_mask;
    gpio->PUPDR &= ~(UINT32_C(3) << shift);
    gpio_set_mode(gpio, pin, UINT32_C(1));
}

static void gpio_config_af(
    gpio_regs_t *gpio,
    uint8_t pin,
    uint8_t af,
    bool pull_up)
{
    uint32_t pin_mask = UINT32_C(1) << pin;
    uint32_t shift = (uint32_t)pin * UINT32_C(2);
    uint32_t pull = pull_up ? UINT32_C(1) : UINT32_C(0);

    gpio->OTYPER &= ~pin_mask;
    gpio->PUPDR = (gpio->PUPDR & ~(UINT32_C(3) << shift)) |
                  (pull << shift);
    gpio->OSPEEDR = (gpio->OSPEEDR & ~(UINT32_C(3) << shift)) |
                    (UINT32_C(2) << shift);
    gpio_set_af(gpio, pin, af);
    gpio_set_mode(gpio, pin, UINT32_C(2));
}

void p0_hw_motor_force_safe(void *unused)
{
    static const uint8_t port_e_pins[] = {5, 6, 9, 11, 13, 14};
    uint32_t i;

    (void)unused;
#if P0_M2A_SLOWDRIVE_BUILD != 0
    uint32_t primask = slow_irq_lock();
    ++g_motor_stop_generation;
#endif
    RCC_AHB1ENR |= RCC_AHB1_GPIOBEN | RCC_AHB1_GPIOEEN;
    (void)RCC_AHB1ENR;

#if P0_M2A_SLOWDRIVE_BUILD != 0
    slow_io_off();
#endif

    TIM9->CCR1 = 0;
    TIM9->CCR2 = 0;
    TIM1->CCR1 = 0;
    TIM1->CCR2 = 0;
    TIM1->CCR3 = 0;
    TIM1->CCR4 = 0;
    TIM12->CCR1 = 0;
    TIM12->CCR2 = 0;

    for (i = 0; i < (sizeof(port_e_pins) / sizeof(port_e_pins[0])); ++i) {
        gpio_config_output_low(GPIOE, port_e_pins[i]);
    }
    gpio_config_output_low(GPIOB, 14);
    gpio_config_output_low(GPIOB, 15);

    RCC_APB1ENR &= ~RCC_APB1_TIM12EN;
    RCC_APB2ENR &= ~(RCC_APB2_TIM1EN | RCC_APB2_TIM9EN);
    g_motor_direction[0] = 0;
    g_motor_direction[1] = 0;
    g_motor_direction[2] = 0;
    g_motor_direction[3] = 0;
    g_motor_pwm_initialized = false;
#if P0_M2A_SLOWDRIVE_BUILD != 0
    slow_irq_unlock(primask);
#endif
}

#if P0_MOTION_OUTPUT_COMPILED != 0 && P0_M2A_SLOWDRIVE_BUILD == 0

#define P0_TIM_CCMR_PWM_PRELOAD UINT32_C(0x6868)
#define P0_TIM_CR1_ARPE_CEN UINT32_C(0x81)
#define P0_TIM_BDTR_MOE (UINT32_C(1) << 15)

static void motor_pwm_timer_init(void)
{
    RCC_AHB1ENR |= RCC_AHB1_GPIOBEN | RCC_AHB1_GPIOEEN;
    RCC_APB1ENR |= RCC_APB1_TIM12EN;
    RCC_APB2ENR |= RCC_APB2_TIM1EN | RCC_APB2_TIM9EN;
    (void)RCC_APB2ENR;

    gpio_config_af(GPIOE, 5, 3, false);
    gpio_config_af(GPIOE, 6, 3, false);
    gpio_config_af(GPIOE, 9, 1, false);
    gpio_config_af(GPIOE, 11, 1, false);
    gpio_config_af(GPIOE, 13, 1, false);
    gpio_config_af(GPIOE, 14, 1, false);
    gpio_config_af(GPIOB, 14, 9, false);
    gpio_config_af(GPIOB, 15, 9, false);

    TIM9->CR1 = 0;
    TIM1->CR1 = 0;
    TIM12->CR1 = 0;
    TIM9->PSC = 0;
    TIM1->PSC = 0;
    TIM12->PSC = 0;
    TIM9->ARR = P0_MOTOR_PWM_PERIOD_COUNTS - UINT32_C(1);
    TIM1->ARR = P0_MOTOR_PWM_PERIOD_COUNTS - UINT32_C(1);
    TIM12->ARR = P0_MOTOR_PWM_PERIOD_COUNTS - UINT32_C(1);
    TIM9->CCR1 = 0;
    TIM9->CCR2 = 0;
    TIM1->CCR1 = 0;
    TIM1->CCR2 = 0;
    TIM1->CCR3 = 0;
    TIM1->CCR4 = 0;
    TIM12->CCR1 = 0;
    TIM12->CCR2 = 0;
    TIM9->CCMR1 = P0_TIM_CCMR_PWM_PRELOAD;
    TIM1->CCMR1 = P0_TIM_CCMR_PWM_PRELOAD;
    TIM1->CCMR2 = P0_TIM_CCMR_PWM_PRELOAD;
    TIM12->CCMR1 = P0_TIM_CCMR_PWM_PRELOAD;
    TIM9->CCER = UINT32_C(0x11);
    TIM1->CCER = UINT32_C(0x1111);
    TIM12->CCER = UINT32_C(0x11);
    TIM1->BDTR = P0_TIM_BDTR_MOE;
    TIM9->EGR = UINT32_C(1);
    TIM1->EGR = UINT32_C(1);
    TIM12->EGR = UINT32_C(1);
    TIM9->CR1 = P0_TIM_CR1_ARPE_CEN;
    TIM1->CR1 = P0_TIM_CR1_ARPE_CEN;
    TIM12->CR1 = P0_TIM_CR1_ARPE_CEN;
    g_motor_pwm_initialized = true;
}

static void apply_pair(
    uint8_t channel,
    int16_t signed_output,
    volatile uint32_t *ccr_1,
    volatile uint32_t *ccr_2)
{
    uint16_t input_1;
    uint16_t input_2;
    int8_t direction = (signed_output > 0) ? INT8_C(1) :
                       ((signed_output < 0) ? INT8_C(-1) : INT8_C(0));

    if ((direction != 0) && (g_motor_direction[channel] != 0) &&
        (direction != g_motor_direction[channel])) {
        signed_output = 0;
        direction = 0;
    }
    p0_motion_output_pair(signed_output, &input_1, &input_2);
    *ccr_1 = p0_pwm_compare_counts(input_1);
    *ccr_2 = p0_pwm_compare_counts(input_2);
    g_motor_direction[channel] = direction;
}

void p0_hw_motor_apply_pwm(void *unused, const int16_t output_permille[4])
{
    uint8_t i;
    uint8_t nonzero = 0;

    (void)unused;
#if P0_M2A_CALIBRATION_BUILD != 0
    for (i = 0; i < UINT8_C(4); ++i) {
        int32_t value = output_permille[i];
        uint32_t magnitude = (value < 0) ?
                                 (uint32_t)(-value) : (uint32_t)value;
        if (value != 0) {
            ++nonzero;
        }
        if ((magnitude > P0_M2A_MAX_DUTY_PERMILLE) ||
            ((magnitude != 0) &&
             (magnitude < P0_M2A_MIN_DUTY_PERMILLE))) {
            p0_hw_motor_force_safe(0);
            return;
        }
    }
    if (nonzero > UINT8_C(1)) {
        p0_hw_motor_force_safe(0);
        return;
    }
#else
    (void)i;
    (void)nonzero;
#endif
    if (!g_motor_pwm_initialized) {
        motor_pwm_timer_init();
    }
    /* Protocol/encoder order is the schematic connector order MA, MB, MC, MD. */
    apply_pair(0, output_permille[0], &TIM1->CCR1, &TIM1->CCR2);
    apply_pair(1, output_permille[1], &TIM1->CCR3, &TIM1->CCR4);
    apply_pair(2, output_permille[2], &TIM9->CCR1, &TIM9->CCR2);
    apply_pair(3, output_permille[3], &TIM12->CCR1, &TIM12->CCR2);
}

#else

void p0_hw_motor_apply_pwm(void *unused, const int16_t output_permille[4])
{
    (void)unused;
    (void)output_permille;
    p0_hw_motor_force_safe(0);
}

#endif

void p0_hw_early_safe_init(void)
{
    p0_hw_motor_force_safe(0);
}

static void clock_use_hsi_16mhz(void)
{
    RCC_CR |= UINT32_C(1);
    while ((RCC_CR & (UINT32_C(1) << 1)) == 0) {
    }
    RCC_CFGR &= ~UINT32_C(3);
    while ((RCC_CFGR & (UINT32_C(3) << 2)) != 0) {
    }
}

static void uart3_init(void)
{
    RCC_AHB1ENR |= RCC_AHB1_GPIODEN;
    RCC_APB1ENR |= RCC_APB1_USART3EN;
    (void)RCC_APB1ENR;

    gpio_config_af(GPIOD, 8, 7, true);
    gpio_config_af(GPIOD, 9, 7, true);

    USART3->CR1 = 0;
    p0_uart_rx_init(&g_uart_rx);
    USART3->BRR = UINT32_C(139);
    USART3->CR2 = 0;
    USART3->CR3 = USART_CR3_EIE;
    /* STM32F407 USART3为IRQ39；优先级低于默认优先级的SysTick。 */
    NVIC_USART3_PRIORITY = UINT8_C(0x40);
    NVIC_ICPR1 = UINT32_C(1) << 7;
    NVIC_ISER1 = UINT32_C(1) << 7;
    USART3->CR1 = USART_CR1_RE | USART_CR1_TE | USART_CR1_UE |
                  USART_CR1_RXNEIE | USART_CR1_PEIE;
}

static void encoder_timer_init(tim_regs_t *timer, uint32_t period)
{
    timer->CR1 = 0;
    timer->PSC = 0;
    timer->ARR = period;
    timer->CCMR1 = UINT32_C(0x0101);
    timer->CCER = 0;
    timer->SMCR = UINT32_C(3);
    timer->CNT = 0;
    timer->EGR = UINT32_C(1);
    timer->CR1 = UINT32_C(1);
}

static void encoders_init(void)
{
    RCC_AHB1ENR |= RCC_AHB1_GPIOAEN | RCC_AHB1_GPIOBEN |
                   RCC_AHB1_GPIODEN;
    RCC_APB1ENR |= RCC_APB1_TIM2EN | RCC_APB1_TIM3EN |
                   RCC_APB1_TIM4EN | RCC_APB1_TIM5EN;
    (void)RCC_APB1ENR;

    gpio_config_af(GPIOA, 15, 1, true);
    gpio_config_af(GPIOB, 3, 1, true);
    gpio_config_af(GPIOB, 4, 2, true);
    gpio_config_af(GPIOB, 5, 2, true);
    gpio_config_af(GPIOA, 0, 2, true);
    gpio_config_af(GPIOA, 1, 2, true);
    gpio_config_af(GPIOD, 12, 2, true);
    gpio_config_af(GPIOD, 13, 2, true);

    encoder_timer_init(TIM2, UINT32_C(0xFFFFFFFF));
    encoder_timer_init(TIM3, UINT32_C(0xFFFF));
    encoder_timer_init(TIM5, UINT32_C(0xFFFFFFFF));
    encoder_timer_init(TIM4, UINT32_C(0xFFFF));
}

static void vin_adc_init(void)
{
    RCC_AHB1ENR |= RCC_AHB1_GPIOCEN;
    RCC_APB2ENR |= RCC_APB2_ADC2EN;
    (void)RCC_APB2ENR;

    GPIOC->PUPDR &= ~UINT32_C(3);
    gpio_set_mode(GPIOC, 0, UINT32_C(3));

    ADC2->CR1 = 0;
    ADC2->CR2 = 0;
    ADC2->SMPR1 = (ADC2->SMPR1 & ~UINT32_C(7)) | UINT32_C(7);
    ADC2->SQR1 = 0;
    ADC2->SQR2 = 0;
    ADC2->SQR3 = UINT32_C(10);
    ADC2->CR2 = ADC_CR2_ADON;
}

static void systick_init(void)
{
    SYSTICK->LOAD = UINT32_C(16000) - UINT32_C(1);
    SYSTICK->VAL = 0;
    SYSTICK->CTRL = UINT32_C(7);
}

void p0_hw_init(void)
{
    p0_hw_early_safe_init();
    clock_use_hsi_16mhz();
    uart3_init();
    encoders_init();
    vin_adc_init();
    systick_init();
}

uint32_t p0_hw_millis(void)
{
    return g_millis;
}

void p0_hw_main_alive(void)
{
    ++g_main_epoch;
}

bool p0_hw_supervisor_tripped(void)
{
    return g_supervisor_trip != 0;
}

bool p0_hw_uart_read_byte(uint8_t *byte)
{
    return p0_uart_rx_pop(&g_uart_rx, byte);
}

bool p0_hw_uart_take_rx_fault(void)
{
    uint32_t primask;
    bool fault;

    __asm volatile("mrs %0, primask\ncpsid i" : "=r"(primask) :: "memory");
    fault = p0_uart_rx_take_fault(&g_uart_rx);
    __asm volatile("msr primask, %0" :: "r"(primask) : "memory");
    return fault;
}

void USART3_IRQHandler(void)
{
    uint32_t status = USART3->SR;

    if ((status & (USART_SR_RXNE | USART_SR_RX_ERROR_MASK)) != 0) {
        /* 必须先读SR再读DR以清RXNE和接收错误；ISR不解析命令/等待TX。 */
        uint8_t byte = (uint8_t)USART3->DR;
        p0_uart_rx_push_isr(&g_uart_rx, byte,
            (status & USART_SR_RX_ERROR_MASK) != 0);
    }
}

void p0_hw_uart_write(const uint8_t *data, size_t length)
{
    size_t i;

    for (i = 0; i < length; ++i) {
        while ((USART3->SR & USART_SR_TXE) == 0) {
        }
        USART3->DR = data[i];
    }
}

void p0_hw_encoder_read(int32_t count[4])
{
    count[0] = (int32_t)TIM2->CNT;
    count[1] = (int32_t)(uint16_t)TIM3->CNT;
    count[2] = (int32_t)TIM5->CNT;
    count[3] = (int32_t)(uint16_t)TIM4->CNT;
}

bool p0_hw_vin_read(uint16_t *raw, uint16_t *nominal_mv)
{
    uint32_t timeout = UINT32_C(100000);
    uint32_t sample;

    ADC2->SR = 0;
    ADC2->CR2 |= ADC_CR2_SWSTART;
    while (((ADC2->SR & ADC_SR_EOC) == 0) && (timeout != 0)) {
        --timeout;
    }
    if (timeout == 0) {
        return false;
    }

    sample = ADC2->DR & UINT32_C(0xFFF);
    *raw = (uint16_t)sample;
    *nominal_mv = (uint16_t)((sample * UINT32_C(36300) +
                              UINT32_C(2047)) /
                             UINT32_C(4095));
    return true;
}

void p0_hw_watchdog_start(void)
{
    uint32_t timeout = IWDG_UPDATE_TIMEOUT_CYCLES;

    /* Start IWDG first so the LSI clock is forced on before waiting for
       prescaler/reload register updates. Waiting before 0xCCCC can stall a
       cold boot forever because the update flags have no running LSI clock. */
    IWDG_KR = UINT32_C(0xCCCC);
    IWDG_KR = UINT32_C(0x5555);
    IWDG_PR = UINT32_C(4);
    IWDG_RLR = UINT32_C(249);
    while (((IWDG_SR & IWDG_SR_UPDATE_MASK) != 0) && (timeout != 0)) {
        --timeout;
    }
    P0_HW_ASSERT(timeout != 0);
    IWDG_KR = UINT32_C(0xAAAA);
}

void p0_hw_watchdog_feed(void)
{
    IWDG_KR = UINT32_C(0xAAAA);
}

uint32_t p0_hw_take_retained_fault(void)
{
    uint32_t code = P0_HW_FAULT_NONE;

    if ((g_retained_fault.magic == P0_HW_FAULT_MAGIC) &&
        (g_retained_fault.inverted_code == ~g_retained_fault.code)) {
        code = g_retained_fault.code;
    }
    g_retained_fault.magic = 0;
    g_retained_fault.code = 0;
    g_retained_fault.inverted_code = UINT32_C(0xFFFFFFFF);
    return code;
}

void p0_hw_fault_trap(uint32_t code)
{
    __asm volatile("cpsid i" ::: "memory");
    p0_hw_motor_force_safe(0);
    g_retained_fault.code = code;
    g_retained_fault.inverted_code = ~code;
    g_retained_fault.magic = P0_HW_FAULT_MAGIC;
    __asm volatile("dsb" ::: "memory");
    SCB_AIRCR = UINT32_C(0x05FA0004);
    __asm volatile("dsb\nisb" ::: "memory");
    for (;;) {
    }
}

void SysTick_Handler(void)
{
    static uint32_t last_epoch;
    static uint32_t stalled_ms;

    ++g_millis;
    if (g_main_epoch == last_epoch) {
        if (stalled_ms < UINT32_C(100)) {
            ++stalled_ms;
        }
        if (stalled_ms >= UINT32_C(100)) {
            p0_hw_motor_force_safe(0);
            g_supervisor_trip = UINT32_C(1);
        }
    } else {
        last_epoch = g_main_epoch;
        stalled_ms = 0;
    }
}

void NMI_Handler(void)
{
    p0_hw_fault_trap(P0_HW_FAULT_NMI);
}

void HardFault_Handler(void)
{
    p0_hw_fault_trap(P0_HW_FAULT_HARD);
}

void MemManage_Handler(void)
{
    p0_hw_fault_trap(P0_HW_FAULT_MEMMANAGE);
}

void BusFault_Handler(void)
{
    p0_hw_fault_trap(P0_HW_FAULT_BUS);
}

void UsageFault_Handler(void)
{
    p0_hw_fault_trap(P0_HW_FAULT_USAGE);
}

void Default_Handler(void)
{
    p0_hw_fault_trap(P0_HW_FAULT_DEFAULT_IRQ);
}
