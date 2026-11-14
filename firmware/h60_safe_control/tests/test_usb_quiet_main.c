/* Actual main loop with injected UART/clock, no device access. */
#define main firmware_main
#include "../src/main.c"
#undef main
#include "p0_uart_rx.h"
#include <assert.h>
#include <setjmp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef struct { uint32_t us; uint8_t byte; } event_t;
static event_t events[2048];
static size_t count, next;
static uint32_t now_us, quiet_at;
static p0_uart_rx_t rx;
static jmp_buf done;
static int scenario;
static bool enabled, latched, ever_enabled, tx_busy;
static unsigned writes, acks, telems, applies;
static void advance(uint32_t us) {
 uint32_t end=now_us+us;
 while(next<count && events[next].us<=end) p0_uart_rx_push_isr(&rx,events[next++].byte,false);
 now_us=end;
}
static void schedule(uint32_t ms,uint8_t type,uint32_t seq,uint32_t session,bool bad) {
 p0_packet_t p={0}; uint8_t b[P0_PROTOCOL_MAX_FRAME]; size_t i,n;
 p.type=type; p.sequence=seq; p.session_id=session;
 if(type==P0_USB_HELLO) {p.payload_length=5;memcpy(p.payload,"P0UQ1",5);}
 if(scenario==8 && seq==2) {p.payload_length=1;p.payload[0]=0;}
 n=p0_packet_encode(&p,b,sizeof(b)); if(bad)b[n-1]^=1;
 for(i=0;i<n;++i) {assert(count<2048);events[count++]=(event_t){ms*1000+(uint32_t)i*87,b[i]};}
}
void p0_hw_early_safe_init(void) {}
void p0_hw_init(void) {p0_uart_rx_init(&rx);enabled=latched=false;}
void p0_hw_motor_force_safe(void *c) {(void)c;}
void p0_hw_motor_apply_pwm(void *c,const int16_t p[4]) {(void)c;(void)p;++applies;}
uint32_t p0_hw_millis(void) {return now_us/1000;}
void p0_hw_main_alive(void) {advance(100);}
bool p0_hw_supervisor_tripped(void) {return scenario==11 && now_us>=60000;}
bool p0_hw_uart_read_byte(uint8_t *b) {return p0_uart_rx_pop(&rx,b);}
bool p0_hw_uart_take_rx_fault(void) {if(scenario==10 && now_us>=60000)return true;return p0_uart_rx_take_fault(&rx);}
void p0_hw_encoder_read(int32_t c[4]) {memset(c,0,4*sizeof(*c));}
bool p0_hw_vin_read(uint16_t *r,uint16_t *v) {*r=1000;*v=12000;return scenario!=12;}
void p0_hw_watchdog_start(void) {}
void p0_hw_watchdog_feed(void) {if(now_us>=600000)longjmp(done,1);}
uint32_t p0_hw_take_retained_fault(void) {return scenario==15?P0_HW_FAULT_IWDG_RESET:0;}
void p0_hw_fault_trap(uint32_t c) {(void)c;abort();}
void p0_hw_usb_tx_lease(uint32_t ms) {(void)ms;}
bool p0_hw_usb_tx_start(uint32_t ms) {(void)ms;if(latched || scenario==16)return false;enabled=ever_enabled=true;return true;}
void p0_hw_usb_tx_quiet(void) {assert(!tx_busy);if(!latched)quiet_at=now_us;enabled=false;latched=true;}
bool p0_hw_usb_tx_active(void) {return enabled && !latched;}
void p0_hw_uart_write(const uint8_t *data,size_t n) {
 p0_parser_t parser;p0_packet_t p={0};size_t i;
 assert(enabled && !latched);p0_parser_init(&parser);
 for(i=0;i<n;++i)(void)p0_parser_feed(&parser,data[i],&p);
 ++writes;if(p.type==P0_MSG_ACK)++acks;
 if(p.type==P0_MSG_TELEMETRY) {
  ++telems;assert(p.session_id==77 && p.payload[0]==P0_STATE_DISARMED);
  assert(p.payload[1]==0 && p.payload[2]==0 && p.payload[3]==1);
  assert(p.payload[32]==0 && p.payload[33]==2 &&
         p.payload[34]==P0_FIRMWARE_VERSION_PATCH && p.payload[35]==16);
 }
 tx_busy=true;advance((uint32_t)n*87);tx_busy=false;
 if(scenario==13)p0_hw_usb_tx_quiet();
}
static void run(int which) {
 scenario=which;count=next=0;now_us=quiet_at=0;writes=acks=telems=applies=0;ever_enabled=tx_busy=false;
 memset(&g_control,0,sizeof(g_control));memset(&g_parser,0,sizeof(g_parser));g_telemetry_sequence=0;g_motion_fault=false;
 if(which!=0)schedule(5,P0_USB_HELLO,1,77,false);
 if(which==1) {
  schedule(30,P0_MSG_HEARTBEAT,2,77,false);schedule(70,P0_MSG_STOP,3,77,false);
  schedule(100,P0_MSG_HEARTBEAT,4,77,false);schedule(130,P0_MSG_DISARM,5,77,false);
  schedule(160,P0_MSG_HEARTBEAT,6,77,false);schedule(190,P0_USB_QUIET,7,77,false);
 } else if(which>=3 && which<=9) {
  uint8_t type=which==3?P0_MSG_ARM:which==4?P0_MSG_WHEEL_TARGET:which==5?P0_MSG_M2A_CALIBRATION_HOLD:P0_MSG_HEARTBEAT;
  schedule(50,type,which==6?1:2,which==7?88:77,which==9);
 } else if(which==14)schedule(256,P0_MSG_HEARTBEAT,2,77,false);
 schedule(350,P0_USB_HELLO,1,99,false);
 if(which==0)count=0;
 if(setjmp(done)==0)firmware_main();
 assert(applies==0 && g_control.state!=P0_STATE_ARMED);
 if(which==0) {assert(!ever_enabled && writes==0 && g_usb.phase==P0_USB_WAIT);return;}
 assert(latched && !enabled && g_usb.phase==P0_USB_CLOSED);
 if(which==12 || which==15 || which==16)assert(!ever_enabled && writes==0);else assert(ever_enabled);
 if(which==1) {assert(acks==7 && telems>=1);assert(quiet_at>=190000 && quiet_at<205000);}
 if(which==2 || which==14) {assert(acks==1);assert(quiet_at>=257000 && quiet_at<258000);}
 if(which>=3 && which<=9) {assert(acks==1);assert(quiet_at<65000);}
}
static void boundaries(void) {
 p0_usb_quiet_t s;p0_packet_t p={0};p.type=P0_USB_HELLO;p.session_id=1;p.sequence=1;p.payload_length=5;memcpy(p.payload,"P0UQ1",5);
 p0_usb_quiet_init(&s);assert(p0_usb_quiet_accept(&s,&p,UINT32_MAX-100)==P0_USB_OPEN);
 p0_usb_quiet_tick(&s,148);assert(s.phase==P0_USB_ACTIVE);p0_usb_quiet_tick(&s,149);assert(s.phase==P0_USB_CLOSED);
 p0_usb_quiet_init(&s);p.session_id=0;assert(p0_usb_quiet_accept(&s,&p,0)==P0_USB_IGNORE && s.phase==P0_USB_CLOSED);
 p0_usb_quiet_init(&s);p.session_id=1;p.payload[0]='X';assert(p0_usb_quiet_accept(&s,&p,0)==P0_USB_IGNORE && s.phase==P0_USB_CLOSED);
 p0_usb_quiet_init(&s);p.payload[0]='P';assert(p0_usb_quiet_accept(&s,&p,0)==P0_USB_OPEN);s.sequence=UINT32_MAX;
 p.type=P0_MSG_HEARTBEAT;p.payload_length=0;p.sequence=0;assert(p0_usb_quiet_accept(&s,&p,1)==P0_USB_IGNORE && s.phase==P0_USB_CLOSED);
}
int main(void) {int i;for(i=0;i<17;++i)run(i);boundaries();puts(P0_FIRMWARE_BUILD_LABEL ": 17 actual-main scenarios + boundaries PASS");return 0;}
