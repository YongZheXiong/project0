#include "p0_usb_motion.h"
#include <assert.h>
#include <limits.h>
#include <stdlib.h>

static void step(p0_motion_controller_t *m, int32_t counts[4], int16_t output[4])
{assert(p0_motion_step(m,counts,output));for(unsigned i=0;i<4;++i)assert(abs(output[i])<=200);}
int main(void)
{
 p0_motion_controller_t m; p0_motion_config_t c=p0_usb_motion_config();
 int32_t n[4]={0};int16_t out[4]={0};int16_t target[4]={20,20,20,20};
 assert(c.maximum_target_mm_s==40 && c.maximum_output_permille==200 && c.ki_q10_per_s==2048);
 assert(p0_motion_init(&m,&c));step(&m,n,out);assert(p0_motion_set_targets(&m,target));
 /* 稀疏编码器输入：100ms窗得到工程1mm/s，避免把0/1样本误作0/9尖峰。 */
 for(unsigned k=1;k<=100;++k){if(k%5==0){++n[0];--n[1];++n[2];--n[3];}step(&m,n,out);}
 for(unsigned i=0;i<4;++i)assert(m.measured_speed_mm_s[i]==1);
 /* 零反馈只测试限幅与抗积分饱和，不宣称真实电机可以堵转。 */
 for(unsigned k=0;k<1000;++k)step(&m,n,out);
 for(unsigned i=0;i<4;++i){assert(out[i]>=199 && out[i]<=200);assert(m.integrator_q10[i]<=200*1024);}
 int16_t reverse[4]={-20,-20,-20,-20};assert(p0_motion_set_targets(&m,reverse));
 for(unsigned k=0;k<20;++k){step(&m,n,out);for(unsigned i=0;i<4;++i)assert(out[i]>=0);}
 for(unsigned k=0;k<60;++k)step(&m,n,out);
 for(unsigned i=0;i<4;++i)assert(out[i]<0);
 /* 故障判定仍看每个10ms原增量，不可被100ms均值掩盖。 */
 n[0]+=13;assert(!p0_motion_step(&m,n,out));for(unsigned i=0;i<4;++i)assert(out[i]==0);
 assert(m.speed_history_count==0 && !m.encoder_ready);
 /* 长窗只改绝对截止，75ms目标租约、stop代际、一次ARM与时钟回绕仍有效。 */
 p0_usb_motion_guard_t g;p0_usb_motion_init(&g);uint32_t start=UINT32_MAX-100;
 assert(p0_usb_motion_arm(&g,start,7));
 g.target_ms=start+19999;assert(p0_usb_motion_fresh(&g,start+19999,7));
 g.target_ms=start+20000;assert(!p0_usb_motion_fresh(&g,start+20000,7));
 p0_usb_motion_stop(&g);assert(!p0_usb_motion_arm(&g,0,7));
 return 0;
}
