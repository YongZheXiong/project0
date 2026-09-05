/* MMIO与ARM汇编由测试构建替身提供；候选提交、停止、SysTick均取实际源码。 */
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
static uint32_t peripheral[0x24000/4], core[0x1000/4];
static void *mock_addr(uint32_t addr)
{
    if (addr>=0x40000000 && addr<0x40024000) return &peripheral[(addr-0x40000000)/4];
    assert(addr>=0xE000E000 && addr<0xE000F000);
    return &core[(addr-0xE000E000)/4];
}
static uint32_t mock_irq_lock(void);
static void mock_irq_unlock(uint32_t mask);
static void model_write(volatile uint32_t *reg, uint32_t value);
#define P0_SLOW_WRITE(reg, value) model_write(&(reg), (value))
#include "p0_hw_stm32f407_mock.c"

static uint32_t mask, ccr3_active, ccr4_active;
static int updates_at, interrupt_at, writes;
static bool pending, before_lock, injecting, track;
static unsigned observed_drive, observed_brake;

static void update(void)
{
    ccr3_active=TIM1->CCR3; ccr4_active=TIM1->CCR4;
}
static void observe(void)
{
    uint32_t mode=GPIOE->MODER & P0_SLOW_MB_MODES;
    assert(mode==P0_SLOW_MB_OUTPUT || mode==P0_SLOW_MB_AF);
    /* 每个软件可见状态枚举完整理想周期，检查反向/超档以及其他脚隔离。 */
    unsigned drive=0, brake=0;
    for (uint32_t c=0;c<3200;++c) {
        bool a, b;
        if (mode==P0_SLOW_MB_AF) {
            assert(TIM1->CR1 & 1); assert(TIM1->BDTR & 0x8000);
            a=c<ccr3_active; b=c<ccr4_active;
        } else {
            a=(GPIOE->ODR & 0x2000)!=0; b=(GPIOE->ODR & 0x4000)!=0;
        }
        assert(a || !b); /* 不出现反向01 */
        drive+=a&&!b; brake+=a&&b;
    }
    assert(drive==0 || drive==160);
    observed_drive |= drive; observed_brake |= brake;
    assert((GPIOE->MODER & UINT32_C(0x00CC3C00)) == UINT32_C(0x00441400));
    assert((GPIOB->MODER & UINT32_C(0xF0000000)) == UINT32_C(0x50000000));
    assert(!(RCC_APB2ENR & RCC_APB2_TIM9EN));
    assert(!(RCC_APB1ENR & RCC_APB1_TIM12EN));
}
static void trip_now(void)
{
    injecting=true;
    /* 使用真实监督ISR达到其100ms主循环停滞条件。 */
    for (unsigned i=0;i<101;++i) SysTick_Handler();
    injecting=false;
    assert(g_supervisor_trip);
}
static uint32_t mock_irq_lock(void)
{
    if (before_lock && !injecting && mask==0) {
        before_lock=false; trip_now();
    }
    uint32_t old=mask; mask=1; return old;
}
static void mock_irq_unlock(uint32_t saved)
{
    mask=saved;
    if (!mask && pending && !injecting) {
        pending=false; trip_now();
    }
}
static void model_write(volatile uint32_t *reg, uint32_t value)
{
    bool selected=track && !injecting;
    if (selected && (updates_at==-2 || writes==updates_at)) update();
    *reg=value;
    if (reg==&GPIOE->BSRR) {
        GPIOE->ODR=(GPIOE->ODR | (value & 0xFFFF)) & ~(value>>16);
    }
    if (reg==&TIM1->EGR && (value&1)) update();
    if (selected) {
        observe();
        if (writes==interrupt_at) { assert(mask==1); pending=true; }
        ++writes;
    }
}
static void setup(void)
{
    track=false; pending=before_lock=injecting=false; mask=0;
    memset(peripheral,0,sizeof(peripheral)); memset(core,0,sizeof(core));
    p0_hw_motor_force_safe(0);
    g_millis=0; g_supervisor_trip=0;
    p0_uart_rx_init(&g_uart_rx);
    ccr3_active=ccr4_active=0; writes=0;
    observed_drive=observed_brake=0;
}
static void wake(p0_m2a_slowdrive_t *s)
{
    p0_slow_arm(s,g_millis,p0_hw_motor_stop_generation());
    assert(p0_slow_hold(s,1,1,50,g_millis,p0_hw_motor_stop_generation())==P0_SLOW_WAKE);
    track=true;
}
static unsigned check_repeated_start(void)
{
    const uint32_t gaps[] = {0, 1, 470000, UINT32_MAX - 4};
    unsigned cases = 0;
    /* 同一次上电内保留外设及停止代次；覆盖两次实测间隔和毫秒回绕。 */
    for (unsigned i = 0; i < sizeof(gaps)/sizeof(gaps[0]); ++i) {
        p0_m2a_slowdrive_t s;
        setup(); updates_at=-2; interrupt_at=-1; wake(&s);
        assert(p0_hw_slow_commit(&s,P0_SLOW_WAKE,g_millis));
        tim_regs_t first_timer = *TIM1;
        uint32_t first_mode = GPIOE->MODER, first_odr = GPIOE->ODR;
        for (unsigned run = 0; run < 3; ++run) {
            uint32_t start = g_millis;
            assert(memcmp(&first_timer,TIM1,sizeof(first_timer))==0);
            assert(GPIOE->MODER==first_mode && GPIOE->ODR==first_odr);
            g_millis=start+2;
            assert(p0_slow_service(&s,g_millis,p0_hw_motor_stop_generation())==P0_SLOW_NONE);
            g_millis=start+3;
            assert(p0_slow_service(&s,g_millis,p0_hw_motor_stop_generation())==P0_SLOW_RUN);
            assert(p0_hw_slow_commit(&s,P0_SLOW_RUN,start)); update();
            observed_drive=observed_brake=0; observe();
            assert(observed_drive==160 && observed_brake==3040);
            p0_m2a_slowdrive_t stale = s;
            p0_hw_motor_force_safe(0);
            assert(!p0_hw_slow_commit(&stale,P0_SLOW_RUN,g_millis));
            assert(!(GPIOE->ODR & P0_SLOW_MB_PINS));
            p0_slow_reset(&s);
            g_millis+=gaps[i];
            wake(&s);
            assert(p0_hw_slow_commit(&s,P0_SLOW_WAKE,g_millis));
            ++cases;
        }
        p0_hw_motor_force_safe(0);
    }
    return cases;
}
int main(void)
{
    p0_m2a_slowdrive_t s;
    unsigned scenarios=0;
    /* 任一候选寄存器写前更新；-2为每次写前更新，-1为无自然更新。 */
    for (int event=-2;event<40;++event) {
        setup(); updates_at=event; interrupt_at=-1; wake(&s);
        assert(p0_hw_slow_commit(&s,P0_SLOW_WAKE,0)); observe();
        assert(observed_drive==0 && observed_brake==3200);
        g_millis=3;
        assert(p0_slow_service(&s,3,p0_hw_motor_stop_generation())==P0_SLOW_RUN);
        assert(p0_hw_slow_commit(&s,P0_SLOW_RUN,0)); update(); observe();
        assert(observed_drive==160);
        p0_hw_motor_force_safe(0); observe();
        assert(!(GPIOE->ODR & P0_SLOW_MB_PINS));
        assert(p0_slow_service(&s,4,p0_hw_motor_stop_generation())==P0_SLOW_REJECT);
        ++scenarios;
    }
    for (int point=-1;point<30;++point) {
        setup(); updates_at=-2; interrupt_at=point; wake(&s);
        before_lock=point==-1;
        (void)p0_hw_slow_commit(&s,P0_SLOW_WAKE,0);
        if (point>=writes) continue;
        assert(g_supervisor_trip && !(GPIOE->ODR & P0_SLOW_MB_PINS));
        assert(!p0_hw_slow_commit(&s,P0_SLOW_RUN,0)); observe();
        ++scenarios;
    }
    /* 到RUN写前/写中、零请求/STOP后的旧令牌以及已知UART错误。 */
    setup(); updates_at=-2; interrupt_at=-1; wake(&s);
    assert(p0_hw_slow_commit(&s,P0_SLOW_WAKE,0));
    g_millis=3; assert(p0_slow_service(&s,3,p0_hw_motor_stop_generation())==P0_SLOW_RUN);
    interrupt_at=writes; assert(p0_hw_slow_commit(&s,P0_SLOW_RUN,0));
    assert(g_supervisor_trip); observe();
    assert(!p0_hw_slow_commit(&s,P0_SLOW_RUN,0));
    for (unsigned error=0;error<4;++error) {
        setup(); interrupt_at=-1; wake(&s);
        if (error==0) p0_uart_rx_push_isr(&g_uart_rx,0,true);
        if (error==1) USART3->SR=USART_SR_RX_ERROR_MASK;
        if (error==2) g_millis=1001;
        if (error==3) p0_hw_motor_force_safe(0);
        assert(!p0_hw_slow_commit(&s,P0_SLOW_WAKE,0)); observe();
    }
    setup(); wake(&s); mask=1; interrupt_at=-1;
    assert(p0_hw_slow_commit(&s,P0_SLOW_WAKE,0)); assert(mask==1);
    /* 同一WAKING重复底层启动不得在AF接管后复位/分批重装计数。 */
    unsigned previous=writes;
    assert(!p0_hw_slow_commit(&s,P0_SLOW_WAKE,0));
    assert(writes-previous==8); /* 只执行配对撤输出事务 */
    assert(!(GPIOE->ODR & P0_SLOW_MB_PINS));
    p0_hw_motor_force_safe(0); assert(mask==1);
    printf("PASS: actual hardware transactions %u update/ISR scenarios plus guard/PRIMASK cases\n",scenarios);
    printf("PASS: %u repeated-start hardware cycles without clearing the test fixture between sessions\n",
           check_repeated_start());
}
