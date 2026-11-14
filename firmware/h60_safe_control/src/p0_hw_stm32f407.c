#include "p0_hw.h"
#include "p0_build_config.h"
#include "p0_m2a_calibration.h"
#include "p0_motion.h"
#include "p0_pwm_timing.h"
#include "p0_uart_rx.h"
#include "p0_usb_diag.h"
#include "p0_uart_pinmap.h"

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
#define RCC_APB1RSTR REG32(UINT32_C(0x40023820))
#define RCC_APB2RSTR REG32(UINT32_C(0x40023824))
#define RCC_AHB1ENR REG32(UINT32_C(0x40023830))
#define RCC_APB1ENR REG32(UINT32_C(0x40023840))
#define RCC_APB2ENR REG32(UINT32_C(0x40023844))
#define RCC_CSR REG32(UINT32_C(0x40023874))

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

#define RCC_CSR_RMVF (UINT32_C(1) << 24)
#define RCC_CSR_IWDGRSTF (UINT32_C(1) << 29)
#define P0_RESET_OBSERVER_MAGIC UINT32_C(0x50305253)

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
#define USART_SR_TC (UINT32_C(1) << 6)
#define USART_SR_TXE (UINT32_C(1) << 7)
#define USART_CR1_RE (UINT32_C(1) << 2)
#define USART_CR1_TE (UINT32_C(1) << 3)
#define USART_CR1_RXNEIE (UINT32_C(1) << 5)
#define USART_CR1_PEIE (UINT32_C(1) << 8)
#define USART_CR1_UE (UINT32_C(1) << 13)
#define USART_CR3_EIE UINT32_C(1)
#define USART_TX_COMPLETE_TIMEOUT_CYCLES UINT32_C(1000000)

#define ADC_SR_EOC (UINT32_C(1) << 1)
#define ADC_CR2_ADON (UINT32_C(1) << 0)
#define ADC_CR2_SWSTART (UINT32_C(1) << 30)

#if P0_USB_GUARDED_BUILD != 0
static volatile bool g_usb_tx_latched;
static volatile uint32_t g_usb_heartbeat_ms;
#endif
static volatile uint32_t g_millis;
static volatile uint32_t g_main_epoch;
static volatile uint32_t g_supervisor_trip;
static p0_uart_rx_t g_uart_rx;
static bool g_motor_pwm_initialized;
static int8_t g_motor_direction[4];
#if P0_M2A_SLOWDRIVE_BUILD != 0 || P0_USB_MOTION_BUILD != 0
static volatile uint32_t g_motor_stop_generation;

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

#if P0_M2A_SLOWDRIVE_BUILD != 0
#include "p0_m2a_slowdrive_sequence.h"
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
#if P0_H6_CHARACTERIZATION_BUILD != 0
    if (ok && action == P0_SLOW_WAKE && s->phase == P0_SLOW_WAKING &&
        slow_io_is_safe_gpio(s)) {
        slow_io_prepare(s);
        ok = slow_io_ready(s) && slow_permitted(s, last_heartbeat_ms);
        if (ok) {
            slow_io_wake(s);
            s->wake_at_ms = g_millis;
        }
    } else if (ok && action == P0_SLOW_RUN && s->phase == P0_SLOW_ACTIVE &&
               (uint32_t)(g_millis - s->wake_at_ms) >= P0_SLOW_WAKE_MS &&
               slow_io_is_alternate(s)) {
        slow_io_run(s);
#else
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
#endif
    } else {
        ok = false;
    }
    if (!ok) p0_hw_motor_force_safe(0);
    slow_irq_unlock(primask);
    return ok;
}
#endif
#endif
#if P0_USB_MOTION_BUILD != 0
#include "p0_usb_motion_io.h"
static p0_usb_motion_guard_t * volatile g_um_guard;
static volatile bool g_um_waking;
static volatile uint32_t g_um_wake_ms;
static volatile int8_t g_um_direction[4];
#endif
static p0_hw_retained_fault_t g_retained_fault
    __attribute__((section(".noinit")));
static p0_hw_retained_fault_t g_reset_observer
    __attribute__((section(".noinit")));
#if P0_USB_LINK_RECOVERY_BUILD != 0
static uint32_t g_boot_reset_flags;
void p0_hw_usb_boot_identity(uint32_t uid[3], uint32_t *reset_flags)
{
    /* STM32F407 CMSIS UID_BASE；只读96位UID，不作安全认证。 */
    for (uint32_t i = 0; i < 3; ++i)
        uid[i] = REG32(UINT32_C(0x1FFF7A10) + i * UINT32_C(4));
    *reset_flags = g_boot_reset_flags;
}
#endif

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
#if P0_M2A_SLOWDRIVE_BUILD != 0 || P0_USB_MOTION_BUILD != 0
    uint32_t primask = slow_irq_lock();
    ++g_motor_stop_generation;
#endif
    RCC_AHB1ENR |= RCC_AHB1_GPIOBEN | RCC_AHB1_GPIOEEN;
    (void)RCC_AHB1ENR;

#if P0_M2A_SLOWDRIVE_BUILD != 0
    slow_io_off();
#elif P0_USB_MOTION_BUILD != 0
    um_io_off();
    g_um_waking = false;
    for (i = 0; i < 4; ++i) g_um_direction[i] = 0;
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
#if P0_M2A_SLOWDRIVE_BUILD != 0 || P0_USB_MOTION_BUILD != 0
    slow_irq_unlock(primask);
#endif
}

#if P0_MOTION_OUTPUT_COMPILED != 0 && P0_M2A_SLOWDRIVE_BUILD == 0 && P0_USB_MOTION_BUILD == 0

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

#if P0_USB_GUARDED_BUILD != 0
static void usb_tx_off(void)
{
    USART3->CR1 &= ~USART_CR1_TE;
    gpio_set_mode(P0_UART_GPIO, P0_UART_TX_PIN, 0); /* 输入，无推挽空闲高 */
    P0_UART_GPIO->PUPDR &= ~((UINT32_C(3) << (P0_UART_TX_PIN * 2)) |
                             (UINT32_C(3) << (P0_UART_RX_PIN * 2)));
#if P0_UART_J5_BUILD != 0
    /* 早期/静默/故障路径均撤销旧USB映射与上下拉。 */
    gpio_set_mode(GPIOD, 8, 0);
    gpio_set_mode(GPIOD, 9, 0);
    GPIOD->PUPDR &= ~((UINT32_C(3) << 16) | (UINT32_C(3) << 18));
    gpio_set_af(GPIOD, 8, 0);
    gpio_set_af(GPIOD, 9, 0);
#endif
}
void p0_hw_usb_tx_quiet(void)
{
#if P0_USB_RX_DIAG_BUILD != 0
    bool first = !g_usb_tx_latched;
#endif
    g_usb_tx_latched = true;
    usb_tx_off();
#if P0_USB_MOTION_BUILD != 0
    p0_hw_motor_force_safe(0);
#endif
#if P0_USB_RX_DIAG_BUILD != 0
    if (first) P0_DIAG(P0_DIAG_TX_QUIET, g_supervisor_trip, g_uart_rx.fault);
#endif
}
bool p0_hw_usb_tx_active(void)
{
    return !g_usb_tx_latched && (USART3->CR1 & USART_CR1_TE) != 0 &&
        (uint32_t)(g_millis - g_usb_heartbeat_ms) < UINT32_C(250);
}
void p0_hw_usb_tx_lease(uint32_t heartbeat_ms)
{
    if (p0_hw_usb_tx_active()) g_usb_heartbeat_ms = heartbeat_ms;
}
bool p0_hw_usb_tx_start(uint32_t heartbeat_ms)
{
    uint32_t primask;
    bool ok;
    __asm volatile("mrs %0, primask\ncpsid i" : "=r"(primask) :: "memory");
    ok = !g_usb_tx_latched && !g_supervisor_trip && !g_uart_rx.fault;
    if (ok) {
        g_usb_heartbeat_ms = heartbeat_ms;
        USART3->CR1 |= USART_CR1_TE;
        gpio_config_af(P0_UART_GPIO, P0_UART_TX_PIN, 7, false);
    }
    __asm volatile("dsb\nmsr primask, %0" :: "r"(primask) : "memory");
    return ok && p0_hw_usb_tx_active();
}
#if P0_USB_MOTION_BUILD != 0
bool p0_hw_usb_motion_begin(p0_usb_motion_guard_t *guard)
{
    uint32_t saved = slow_irq_lock();
    bool ok = p0_hw_usb_tx_active() &&
        p0_usb_motion_fresh(guard, g_millis, g_motor_stop_generation);
    if (ok) g_um_guard = guard;
    slow_irq_unlock(saved);
    return ok;
}
bool p0_hw_usb_motion_commit(const int16_t output[4])
{
    uint32_t saved = slow_irq_lock();
    bool nonzero = false;
    bool ok = p0_hw_usb_tx_active() && !g_supervisor_trip &&
        !g_uart_rx.fault && !(USART3->SR & USART_SR_RX_ERROR_MASK) &&
        p0_usb_motion_fresh(g_um_guard, g_millis, g_motor_stop_generation);
    for (uint8_t i = 0; i < 4; ++i) {
        int32_t magnitude = output[i] < 0 ? -(int32_t)output[i] : output[i];
        int8_t direction = output[i] > 0 ? 1 : (output[i] < 0 ? -1 : 0);
        if (magnitude > P0_UM_OUTPUT_LIMIT ||
            (direction && g_um_direction[i] && direction != g_um_direction[i]))
            ok = false;
        if (magnitude) nonzero = true;
    }
    if (ok && nonzero && !g_um_waking) {
        ok = um_io_is_safe_gpio(0);
        if (ok) {
            um_io_prepare(0);
            ok = um_io_ready(0);
        }
        if (ok) {
            um_io_wake(0);
            g_um_waking = true;
            g_um_wake_ms = g_millis;
        }
    } else if (ok && g_um_waking &&
               (uint32_t)(g_millis - g_um_wake_ms) >= P0_UM_WAKE_MS) {
        ok = um_io_is_alternate(0);
        if (ok) {
            um_io_run(output);
            for (uint8_t i = 0; i < 4; ++i)
                g_um_direction[i] = output[i] > 0 ? 1 : (output[i] < 0 ? -1 : 0);
        }
    }
    if (!ok) p0_hw_motor_force_safe(0);
    slow_irq_unlock(saved);
    return ok;
}
#endif
static bool usb_tx_wait(uint32_t mask)
{
    uint32_t budget = USART_TX_COMPLETE_TIMEOUT_CYCLES;
    while (p0_hw_usb_tx_active() && budget != 0) {
        if ((USART3->SR & mask) != 0) return true;
        --budget;
    }
    p0_hw_usb_tx_quiet();
    return false;
}
#endif

void p0_hw_early_safe_init(void)
{
#if P0_USB_GUARDED_BUILD != 0
    RCC_AHB1ENR |= P0_UART_GPIO_CLOCKS;
    RCC_APB1ENR |= RCC_APB1_USART3EN;
    (void)RCC_APB1ENR;
#if P0_UART_J5_BUILD != 0
    gpio_set_mode(P0_UART_GPIO, P0_UART_RX_PIN, 0);
#endif
    usb_tx_off();
#endif
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
    RCC_AHB1ENR |= P0_UART_GPIO_CLOCKS;
    RCC_APB1ENR |= RCC_APB1_USART3EN;
    (void)RCC_APB1ENR;

#if P0_USB_GUARDED_BUILD != 0
    usb_tx_off();
    gpio_config_af(P0_UART_GPIO, P0_UART_RX_PIN, 7, false);
    g_usb_tx_latched = false;
#else
    gpio_config_af(GPIOD, 8, 7, true);
    gpio_config_af(GPIOD, 9, 7, true);
#endif

    USART3->CR1 = 0;
    p0_uart_rx_init(&g_uart_rx);
    USART3->BRR = UINT32_C(139);
    USART3->CR2 = 0;
    USART3->CR3 = USART_CR3_EIE;
    /* STM32F407 USART3为IRQ39；优先级低于默认优先级的SysTick。 */
    NVIC_USART3_PRIORITY = UINT8_C(0x40);
    NVIC_ICPR1 = UINT32_C(1) << 7;
    NVIC_ISER1 = UINT32_C(1) << 7;
#if P0_USB_GUARDED_BUILD != 0
    USART3->CR1 = USART_CR1_RE | USART_CR1_UE |
                  USART_CR1_RXNEIE | USART_CR1_PEIE;
#else
    USART3->CR1 = USART_CR1_RE | USART_CR1_TE | USART_CR1_UE |
                  USART_CR1_RXNEIE | USART_CR1_PEIE;
#endif
}

static void encoder_timer_init(tim_regs_t *timer, uint32_t period)
{
#if P0_USB_ENCODER_FILTER_BUILD != 0
    /* 只核滤波时基，不改总线时钟；异常走原故障撤输出路径。
       SW/SWS=HSI、HPRE=/1、PPRE1=/1；CKD在下方明确保持0。 */
    P0_HW_ASSERT((RCC_CFGR & UINT32_C(0x1CFF)) == 0);
#endif
    timer->CR1 = 0;
    timer->PSC = 0;
    timer->ARR = period;
#if P0_USB_ENCODER_FILTER_BUILD != 0
    /* RM0090: ICxF=0110，fSAMPLING=fDTS/4，连续6样本。
       A/B对称；CCxS=01、ICxPSC=0，原双沿x4/极性保持。 */
    timer->CCMR1 = UINT32_C(0x6161);
#else
    timer->CCMR1 = UINT32_C(0x0101);
#endif
    timer->CCER = 0;
    timer->SMCR = UINT32_C(3);
    timer->CNT = 0;
    timer->EGR = UINT32_C(1);
    timer->CR1 = UINT32_C(1);
#if P0_USB_ENCODER_FILTER_BUILD != 0
    P0_HW_ASSERT(timer->CCMR1 == UINT32_C(0x6161) &&
                 timer->CCER == 0 && timer->SMCR == UINT32_C(3) &&
                 timer->PSC == 0 && timer->ARR == period &&
                 (timer->CR1 & UINT32_C(0x301)) == UINT32_C(1));
#endif
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

#if P0_USB_RX_DIAG_BUILD != 0
void p0_hw_diag_event(uint32_t event, uint32_t a, uint32_t b)
{
    uint32_t ipsr;
    __asm volatile("mrs %0, ipsr" : "=r"(ipsr));
    unsigned lane = ipsr == 0 ? P0_DIAG_MAIN :
        (ipsr == 55 ? P0_DIAG_UART : (ipsr == 15 ? P0_DIAG_TICK : P0_DIAG_FAULT));
    p0_diag_emit(lane, g_millis, event, a, b);
}
#endif
void p0_hw_init(void)
{
    p0_hw_early_safe_init();
#if P0_USB_RX_DIAG_BUILD != 0
    uint32_t uid[3];
    for (unsigned i = 0; i < 3; ++i) uid[i] = REG32(UINT32_C(0x1FFF7A10) + i*4);
    p0_diag_boot(RCC_CSR, uid);
#endif
    clock_use_hsi_16mhz();
    uart3_init();
    encoders_init();
    vin_adc_init();
    systick_init();
    P0_DIAG(P0_DIAG_HW_READY, USART3->BRR, USART3->CR1);
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
        P0_DIAG(P0_DIAG_RX_BYTE, status, (uint32_t)byte |
            ((uint32_t)g_uart_rx.fault << 8));
    }
}

void p0_hw_uart_write(const uint8_t *data, size_t length)
{
    size_t i;
#if P0_USB_RX_DIAG_BUILD != 0
    uint32_t kind = length >= 14 ? (uint32_t)data[3] << 8 : 0;
    uint32_t session = length >= 14 ? p0_read_u32_le(data+6) : 0;
    uint32_t seq = length >= 14 ? p0_read_u32_le(data+10) : 0;
    P0_DIAG(P0_DIAG_TX_BEGIN | kind, session, seq);
#endif

    for (i = 0; i < length; ++i) {
#if P0_USB_GUARDED_BUILD != 0
        if (!usb_tx_wait(USART_SR_TXE)) {
            P0_DIAG(P0_DIAG_TX_ABORT, (uint32_t)i, (uint32_t)length);
            return;
        }
#else
        while ((USART3->SR & USART_SR_TXE) == 0) {
        }
#endif
        USART3->DR = data[i];
    }
#if P0_USB_RX_DIAG_BUILD == 0
#if P0_USB_GUARDED_BUILD != 0
    (void)usb_tx_wait(USART_SR_TC);
#endif
#else
    if (usb_tx_wait(USART_SR_TC))
        P0_DIAG(P0_DIAG_TX_COMPLETE | kind, session, seq);
    else P0_DIAG(P0_DIAG_TX_ABORT, (uint32_t)length, (uint32_t)length);
#endif
}

void p0_hw_encoder_read(int32_t count[4])
{
    count[0] = (int32_t)TIM2->CNT;
    count[1] = (int32_t)(uint16_t)TIM3->CNT;
    count[2] = (int32_t)TIM5->CNT;
    count[3] = (int32_t)(uint16_t)TIM4->CNT;
}

#if P0_USB_MOTION_TRACE_BUILD != 0
void p0_hw_usb_motion_trace_snapshot(uint8_t channel, p0_trace_io_t *sample)
{
    static const uint8_t pin1[4] = {9, 13, 5, 14};
    static const uint8_t pin2[4] = {11, 14, 6, 15};
    uint32_t before = g_motor_stop_generation;
    uint32_t first, second, mode, enable, clock;
    tim_regs_t *timer;
    gpio_regs_t *gpio;
    sample->flags = 0;
    sample->ccr1 = sample->ccr2 = 0;
    sample->generation = before;
    if (channel >= 4) return;
    timer = channel < 2 ? TIM1 : (channel == 2 ? TIM9 : TIM12);
    gpio = channel == 3 ? GPIOB : GPIOE;
    first = channel == 1 ? timer->CCR3 : timer->CCR1;
    second = channel == 1 ? timer->CCR4 : timer->CCR2;
    mode = gpio->MODER;
    enable = (timer->CCER >> (channel == 1 ? 8 : 0)) & UINT32_C(0x11);
    clock = channel < 2 ? (RCC_APB2ENR & RCC_APB2_TIM1EN) :
        (channel == 2 ? (RCC_APB2ENR & RCC_APB2_TIM9EN) :
                        (RCC_APB1ENR & RCC_APB1_TIM12EN));
    sample->ccr1 = (uint16_t)first;
    sample->ccr2 = (uint16_t)second;
    if (((mode >> (2 * pin1[channel])) & 3) == 2 &&
        ((mode >> (2 * pin2[channel])) & 3) == 2) sample->flags |= P0_TRACE_IO_AF;
    if (clock) sample->flags |= P0_TRACE_IO_CLOCK;
    if (enable == UINT32_C(0x11)) sample->flags |= P0_TRACE_IO_CCER;
    if (channel >= 2 || (timer->BDTR & UINT32_C(0x8000)))
        sample->flags |= P0_TRACE_IO_MOE_OR_NA;
    if (first > 3200 || second > 3200) sample->flags |= P0_TRACE_IO_RANGE;
    sample->generation = g_motor_stop_generation;
    if (before == sample->generation) sample->flags |= P0_TRACE_IO_COHERENT;
}
#endif

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

void p0_hw_iwdg_diagnostic_stall(void)
{
    p0_hw_motor_force_safe(0);
    __asm volatile("dsb" ::: "memory");
    for (;;) {
        __asm volatile("nop");
    }
}

void p0_hw_exception_diagnostic_trigger(void)
{
    uint32_t timeout = USART_TX_COMPLETE_TIMEOUT_CYCLES;

    p0_hw_motor_force_safe(0);
    while (((USART3->SR & USART_SR_TC) == 0) && (timeout != 0)) {
        --timeout;
    }
    P0_HW_ASSERT(timeout != 0);
    __asm volatile("dsb\nudf #0" ::: "memory");
    p0_hw_fault_trap(P0_HW_FAULT_HARD);
}

uint32_t p0_hw_take_retained_fault(void)
{
    uint32_t code = P0_HW_FAULT_NONE;
    uint32_t reset_flags = RCC_CSR;
#if P0_USB_LINK_RECOVERY_BUILD != 0
    g_boot_reset_flags = reset_flags;
#endif
    bool reset_observer_valid =
        (g_reset_observer.magic == P0_RESET_OBSERVER_MAGIC) &&
        (g_reset_observer.inverted_code == ~g_reset_observer.code) &&
        (g_reset_observer.code == P0_RESET_OBSERVER_MAGIC);

    if ((g_retained_fault.magic == P0_HW_FAULT_MAGIC) &&
        (g_retained_fault.inverted_code == ~g_retained_fault.code)) {
        code = g_retained_fault.code;
    } else if (reset_observer_valid &&
               ((reset_flags & RCC_CSR_IWDGRSTF) != 0)) {
        code = P0_HW_FAULT_IWDG_RESET;
    }
    g_retained_fault.magic = 0;
    g_retained_fault.code = 0;
    g_retained_fault.inverted_code = UINT32_C(0xFFFFFFFF);
    g_reset_observer.magic = P0_RESET_OBSERVER_MAGIC;
    g_reset_observer.code = P0_RESET_OBSERVER_MAGIC;
    g_reset_observer.inverted_code = ~P0_RESET_OBSERVER_MAGIC;
    RCC_CSR |= RCC_CSR_RMVF;
    return code;
}

void p0_hw_fault_trap(uint32_t code)
{
    __asm volatile("cpsid i" ::: "memory");
#if P0_USB_GUARDED_BUILD != 0
    p0_hw_usb_tx_quiet();
#endif
    p0_hw_motor_force_safe(0);
    g_retained_fault.code = code;
    g_retained_fault.inverted_code = ~code;
    g_retained_fault.magic = P0_HW_FAULT_MAGIC;
    __asm volatile("dsb" ::: "memory");
    P0_DIAG(P0_DIAG_TRAP, code, 0);
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
#if P0_USB_MOTION_BUILD != 0
    if (g_um_guard != 0 && g_um_guard->armed &&
        !p0_usb_motion_fresh(g_um_guard, g_millis, g_motor_stop_generation))
        p0_hw_motor_force_safe(0);
#endif
#if P0_USB_GUARDED_BUILD != 0
    if ((USART3->CR1 & USART_CR1_TE) != 0 &&
        (uint32_t)(g_millis - g_usb_heartbeat_ms) >= UINT32_C(250))
    {
        p0_hw_usb_tx_quiet();
        P0_DIAG(P0_DIAG_TX_LEASE_EXPIRED, g_millis, g_usb_heartbeat_ms);
    }
#endif
    if (g_main_epoch == last_epoch) {
        if (stalled_ms < UINT32_C(100)) {
            ++stalled_ms;
        }
        if (stalled_ms >= UINT32_C(100)) {
            p0_hw_motor_force_safe(0);
            g_supervisor_trip = UINT32_C(1);
#if P0_USB_GUARDED_BUILD != 0
            p0_hw_usb_tx_quiet();
#endif
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
