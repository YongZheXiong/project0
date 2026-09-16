"""编译并执行真实C逻辑；只替换MMIO地址和不可在Mac执行的ARM指令。"""
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
DEFINES = ['-DP0_MOTION_OUTPUT_COMPILED=1', '-DP0_M2A_CALIBRATION_BUILD=1',
           '-DP0_M2A_SLOWDRIVE_BUILD=1']


class SlowdriveOfflineTests(unittest.TestCase):
    def compile_run(self, test, sources, mock_hw=False, extra_defines=()):
        with tempfile.TemporaryDirectory() as tmp:
            if mock_hw:
                source = (ROOT/'src/p0_hw_stm32f407.c').read_text()
                old = '#define REG32(address) (*(volatile uint32_t *)(uintptr_t)(address))'
                self.assertEqual(source.count(old), 1)
                source = source.replace(old, '#define REG32(address) (*(volatile uint32_t *)mock_addr(address))')
                source, n = re.subn(
                    r'\(\((\w+_regs_t) \*\)\(uintptr_t\)(UINT32_C\(0x[0-9A-F]+\))\)',
                    r'((\1 *)mock_addr(\2))', source)
                self.assertEqual(n, 15)
                lock = '__asm volatile("mrs %0, primask\\ncpsid i" : "=r"(primask) :: "memory");'
                self.assertEqual(source.count(lock), 2)
                source = source.replace(lock, 'primask = mock_irq_lock();')
                for instruction in ['dsb\\nmsr primask, %0', 'msr primask, %0']:
                    old = '__asm volatile("'+instruction+'" :: "r"(primask) : "memory");'
                    self.assertEqual(source.count(old), 1)
                    source = source.replace(old, 'mock_irq_unlock(primask);')
                source, n = re.subn(r'__asm volatile\("(?:cpsid i|dsb|dsb\\nisb)" ::: "memory"\);',
                                    '(void)0;', source)
                self.assertEqual(n, 4)
                source = source.replace('__asm volatile("nop");', '(void)0;')
                source = source.replace(
                    '__asm volatile("dsb\\nudf #0" ::: "memory");', '(void)0;')
                self.assertNotIn('__asm', source)
                self.assertEqual(source.count('__attribute__((section(".noinit")))'), 2)
                source = source.replace('__attribute__((section(".noinit")))', '')
                (Path(tmp)/'p0_hw_stm32f407_mock.c').write_text(source)
            command = ['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-pedantic',
                       '-fsanitize=address,undefined','-Iinclude','-I'+tmp,*DEFINES,
                       *extra_defines,
                       'tests/'+test,*sources,'-o',str(Path(tmp)/'test')]
            build = subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(build.returncode, 0, build.stderr)
            result = subprocess.run([str(Path(tmp)/'test')],capture_output=True,text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            print(result.stdout.strip())

    def test_state_machine(self):
        self.compile_run('test_m2a_slowdrive.c',['src/p0_m2a_slowdrive.c'])

    def test_actual_main_and_protocol(self):
        self.compile_run('test_slowdrive_main.c', [f'src/{s}.c' for s in
             ['p0_m2a_slowdrive','p0_m2a_calibration','p0_motion',
             'p0_motion_scheduler','p0_control','p0_protocol','p0_crc32']])

    def test_h6_actual_main_and_protocol(self):
        self.compile_run('test_slowdrive_main.c', [f'src/{source}.c' for source in
            ['p0_m2a_slowdrive', 'p0_m2a_calibration', 'p0_motion',
             'p0_motion_scheduler', 'p0_control', 'p0_protocol', 'p0_crc32']],
            extra_defines=['-DP0_H6_CHARACTERIZATION_BUILD=1'])

    def test_actual_hardware_and_timer_interleavings(self):
        self.compile_run('test_slowdrive_hw.c',
                         ['src/p0_m2a_slowdrive.c','src/p0_uart_rx.c'],mock_hw=True)

    def test_h6_state_machine(self):
        self.compile_run('test_h6_slowdrive.c', ['src/p0_m2a_slowdrive.c'],
                         extra_defines=['-DP0_H6_CHARACTERIZATION_BUILD=1'])

    def test_h6_hardware_all_channels(self):
        self.compile_run('test_h6_slowdrive_hw.c',
                         ['src/p0_m2a_slowdrive.c', 'src/p0_uart_rx.c'],
                         mock_hw=True,
                         extra_defines=['-DP0_H6_CHARACTERIZATION_BUILD=1'])

    def test_h6_r2_extended_window_state_machine(self):
        self.compile_run('test_h6_extended_window.c',
                         ['src/p0_m2a_slowdrive.c'],
                         extra_defines=['-DP0_H6_CHARACTERIZATION_BUILD=1',
                                        '-DP0_H6_EXTENDED_WINDOW_BUILD=1'])

    def test_h6_r2_actual_main_and_protocol(self):
        self.compile_run('test_slowdrive_main.c', [f'src/{source}.c' for source in
            ['p0_m2a_slowdrive', 'p0_m2a_calibration', 'p0_motion',
             'p0_motion_scheduler', 'p0_control', 'p0_protocol', 'p0_crc32']],
            extra_defines=['-DP0_H6_CHARACTERIZATION_BUILD=1',
                           '-DP0_H6_EXTENDED_WINDOW_BUILD=1'])

    def test_h6_r2_hardware_mc_plus_envelope(self):
        self.compile_run('test_h6_slowdrive_hw.c',
                         ['src/p0_m2a_slowdrive.c', 'src/p0_uart_rx.c'],
                         mock_hw=True,
                         extra_defines=['-DP0_H6_CHARACTERIZATION_BUILD=1',
                                        '-DP0_H6_EXTENDED_WINDOW_BUILD=1'])

    def test_w2_four_wheel_profile_state_machine(self):
        self.compile_run('test_w2_four_wheel_profile.c',
                         ['src/p0_m2a_slowdrive.c'],
                         extra_defines=['-DP0_H6_CHARACTERIZATION_BUILD=1',
                                        '-DP0_W2_FOUR_WHEEL_PROFILE_BUILD=1'])

    def test_w2_four_wheel_profile_hardware(self):
        self.compile_run('test_h6_slowdrive_hw.c',
                         ['src/p0_m2a_slowdrive.c', 'src/p0_uart_rx.c'],
                         mock_hw=True,
                         extra_defines=['-DP0_H6_CHARACTERIZATION_BUILD=1',
                                        '-DP0_W2_FOUR_WHEEL_PROFILE_BUILD=1'])

    def test_w2_link5_requires_explicit_isolated_profile_build(self):
        for defines in (
            ['-DP0_W2_FIVE_SECOND_LINK_LOSS_BUILD=1'],
            ['-DP0_W2_FIVE_SECOND_LINK_LOSS_BUILD=2',
             '-DP0_W2_FOUR_WHEEL_PROFILE_BUILD=1'],
            ['-DP0_W2_FIVE_SECOND_LINK_LOSS_BUILD=1',
             '-DP0_W2_FOUR_WHEEL_PROFILE_BUILD=1',
             '-DP0_H6_EXTENDED_WINDOW_BUILD=1'],
        ):
            with self.subTest(defines=defines):
                result = subprocess.run(
                    ['cc', '-std=c11', '-Iinclude', '-fsyntax-only', *defines,
                     'src/p0_manifest.c'],
                    cwd=ROOT, capture_output=True, text=True,
                )
                self.assertNotEqual(result.returncode, 0)

    def test_w2_link5_actual_main_and_protocol(self):
        self.compile_run('test_slowdrive_main.c', [f'src/{source}.c' for source in
            ['p0_m2a_slowdrive', 'p0_m2a_calibration', 'p0_motion',
             'p0_motion_scheduler', 'p0_control', 'p0_protocol', 'p0_crc32']],
            extra_defines=['-DP0_H6_CHARACTERIZATION_BUILD=1',
                           '-DP0_W2_FOUR_WHEEL_PROFILE_BUILD=1',
                           '-DP0_W2_FIVE_SECOND_LINK_LOSS_BUILD=1'])

    def test_w2_link5_hardware_commit_and_interrupt_cancellation(self):
        self.compile_run('test_h6_slowdrive_hw.c',
                         ['src/p0_m2a_slowdrive.c', 'src/p0_uart_rx.c'],
                         mock_hw=True,
                         extra_defines=['-DP0_H6_CHARACTERIZATION_BUILD=1',
                                        '-DP0_W2_FOUR_WHEEL_PROFILE_BUILD=1',
                                        '-DP0_W2_FIVE_SECOND_LINK_LOSS_BUILD=1'])

    def test_invalid_build_combinations(self):
        for pwm,m2a,audit,slow,h6,r2,w2,cal in [
                (0,0,0,1,0,0,0,0),(0,1,0,1,0,0,0,0),
                (1,0,0,1,0,0,0,0),(1,1,1,1,0,0,0,0),
                (1,1,0,2,0,0,0,0),(1,1,0,1,0,0,0,1),
                (1,1,0,0,1,0,0,0),(1,1,1,1,1,0,0,0),
                (1,1,0,1,2,0,0,0),(1,1,0,1,1,0,0,1),
                (1,1,0,1,0,1,0,0),(1,1,0,1,1,2,0,0),
                (1,1,0,1,0,0,1,0),(1,1,0,1,1,1,1,0),
                (1,1,0,1,1,0,2,0)]:
            with self.subTest(pwm=pwm,m2a=m2a,audit=audit,slow=slow,h6=h6,
                              r2=r2,w2=w2,cal=cal):
                result = subprocess.run(['cc','-std=c11','-Iinclude','-fsyntax-only',
                    f'-DP0_MOTION_OUTPUT_COMPILED={pwm}', f'-DP0_M2A_CALIBRATION_BUILD={m2a}',
                    f'-DP0_OFFLINE_MOTION_AUDIT_BUILD={audit}',f'-DP0_M2A_SLOWDRIVE_BUILD={slow}',
                    f'-DP0_H6_CHARACTERIZATION_BUILD={h6}',
                    f'-DP0_H6_EXTENDED_WINDOW_BUILD={r2}',
                    f'-DP0_W2_FOUR_WHEEL_PROFILE_BUILD={w2}',
                    f'-DP0_MOTION_CALIBRATION_VALID={cal}','src/p0_manifest.c'],
                    cwd=ROOT,capture_output=True,text=True)
                self.assertNotEqual(result.returncode,0)


if __name__ == '__main__':
    unittest.main()
