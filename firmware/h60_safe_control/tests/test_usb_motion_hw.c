/* Execute actual HAL transactions with MMIO/PRIMASK substitutions only. */
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
static uint32_t peripheral[0x24000/4], core[0x1000/4];
static void *mock_addr(uint32_t a)
{
    if (a >= 0x40000000 && a < 0x40024000) return peripheral+(a-0x40000000)/4;
    assert(a >= 0xe000e000 && a < 0xe000f000); return core+(a-0xe000e000)/4;
}
static uint32_t mock_irq_lock(void);
static void mock_irq_unlock(uint32_t saved);
static void model_write(volatile uint32_t *reg, uint32_t value);
#define P0_UM_WRITE(reg, value) model_write(&(reg), (value))
#include "p0_hw_stm32f407_mock.c"
static uint32_t masked;
static unsigned write_count;
static int interrupt_at;
static bool pending, injecting;
static p0_usb_motion_guard_t guard;
static bool safe(void)
{
    return (GPIOE->MODER & 0x3ccc3c00) == 0x14441400 &&
        (GPIOB->MODER & 0xf0000000) == 0x50000000 &&
        !(GPIOE->ODR & 0x6a60) && !(GPIOB->ODR & 0xc000) &&
        !TIM1->CCR1 && !TIM1->CCR2 && !TIM1->CCR3 && !TIM1->CCR4 &&
        !TIM9->CCR1 && !TIM9->CCR2 && !TIM12->CCR1 && !TIM12->CCR2;
}
static uint32_t mock_irq_lock(void) {uint32_t old=masked; masked=1; return old;}
static void mock_irq_unlock(uint32_t old)
{
    masked=old;
    if (!masked && pending && !injecting) {
        pending=false; injecting=true; p0_hw_motor_force_safe(0); injecting=false;
    }
}
static void model_write(volatile uint32_t *reg, uint32_t value)
{
    tim_regs_t *two[] = {TIM9,TIM12};
    for (unsigned i=0;i<2;++i) {
        assert(reg!=&two[i]->CR2 && reg!=&two[i]->SMCR && reg!=&two[i]->RCR && reg!=&two[i]->BDTR);
        assert(reg!=&two[i]->CCR3 && reg!=&two[i]->CCR4 && reg!=&two[i]->CCMR2);
    }
    *reg=value;
    if (reg==&GPIOE->BSRR) GPIOE->ODR=(GPIOE->ODR | (value&65535)) & ~(value>>16);
    if (reg==&GPIOB->BSRR) GPIOB->ODR=(GPIOB->ODR | (value&65535)) & ~(value>>16);
    if (!injecting && ++write_count==(unsigned)interrupt_at) pending=true;
}
static void start(void)
{
    interrupt_at=0; pending=injecting=false; masked=0;
    memset(peripheral,0,sizeof(peripheral)); memset(core,0,sizeof(core));
    g_millis=g_main_epoch=g_supervisor_trip=0; g_um_guard=0;
    p0_hw_early_safe_init(); uart3_init();
    USART3->SR=USART_SR_TXE|USART_SR_TC;
    assert(safe() && p0_hw_usb_tx_start(0));
    p0_usb_motion_init(&guard);
    assert(p0_usb_motion_arm(&guard,0,p0_hw_motor_stop_generation()));
    assert(p0_hw_usb_motion_begin(&guard));
    write_count=0;
}
static void drive(void)
{
    int16_t output[4]={80,80,80,80};
    g_millis=10; assert(p0_hw_usb_motion_commit(output));
    assert(TIM1->CCR1==3200 && TIM1->CCR2==3200);
    g_millis=12; assert(p0_hw_usb_motion_commit(output)); assert(TIM1->CCR1==3200);
    g_millis=13; assert(p0_hw_usb_motion_commit(output));
    assert(TIM1->CCR1==2944 && TIM1->CCR2==3200);
    assert(TIM1->CCR3==3200 && TIM1->CCR4==2944);
    assert(TIM9->CCR1==2944 && TIM9->CCR2==3200);
    assert(TIM12->CCR1==3200 && TIM12->CCR2==2944);
}
int main(void)
{
    int16_t output[4]={80,80,80,80}, zero[4]={0}, reverse[4]={-80,-80,-80,-80};
    start(); drive(); assert(p0_hw_usb_motion_commit(zero));
    assert(TIM1->CCR1==3200 && TIM1->CCR2==3200);
    assert(p0_hw_usb_motion_commit(reverse));
    assert(TIM1->CCR1==3200 && TIM1->CCR2==2944);
    assert(!p0_hw_usb_motion_commit(output) && safe()); /* no direct reversal */
    start(); output[0]=81; assert(!p0_hw_usb_motion_commit(output) && safe()); output[0]=80;
    start(); drive(); g_millis=74; SysTick_Handler(); assert(safe());
    assert(!p0_hw_usb_motion_commit(output)); /* ISR stop cannot be undone */
    start(); drive(); guard.target_ms=249; g_millis=249; SysTick_Handler();
    assert(safe() && g_usb_tx_latched && !p0_hw_usb_tx_start(250));
    start(); drive(); guard.target_ms=999; g_usb_heartbeat_ms=999; g_millis=999;
    SysTick_Handler(); assert(safe());
    start(); drive(); p0_hw_usb_tx_quiet(); assert(safe() && !p0_hw_usb_motion_commit(output));
    start(); drive(); g_uart_rx.fault=true; assert(!p0_hw_usb_motion_commit(output) && safe());
    start(); drive(); USART3->SR|=1; assert(!p0_hw_usb_motion_commit(output) && safe());
    start(); drive(); g_supervisor_trip=1; assert(!p0_hw_usb_motion_commit(output) && safe());
    start(); drive(); USART3->SR=0;
    {uint8_t byte=1; p0_hw_uart_write(&byte,1);}
    assert(safe() && g_usb_tx_latched); /* stalled TX clears motion before return */
    /* Inject stop at every write in wake+prepare and in a live PWM update. */
    start(); g_millis=10; assert(p0_hw_usb_motion_commit(output)); unsigned wake_writes=write_count;
    for (unsigned at=1;at<=wake_writes;++at) {
        start(); g_millis=10; interrupt_at=(int)at;
        (void)p0_hw_usb_motion_commit(output); assert(safe());
        interrupt_at=0; assert(!p0_hw_usb_motion_commit(output) && safe());
    }
    start(); drive(); write_count=0; assert(p0_hw_usb_motion_commit(output)); unsigned run_writes=write_count;
    for (unsigned at=1;at<=run_writes;++at) {
        start(); drive(); write_count=0; interrupt_at=(int)at;
        (void)p0_hw_usb_motion_commit(output); assert(safe());
        interrupt_at=0; assert(!p0_hw_usb_motion_commit(output) && safe());
    }
    printf("Actual HAL: 5kHz/wake/sign/leases/STOP, %u wake + %u live interrupt positions PASS\n",wake_writes,run_writes);
    return 0;
}
