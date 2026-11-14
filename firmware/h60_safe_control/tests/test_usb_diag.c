#include "p0_usb_diag.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

int main(int argc, char **argv)
{
    const uint32_t uid[3] = {0x123, 0x456, 0x789};
    memset((void *)&g_p0_diag_store, 0, sizeof(g_p0_diag_store));
    p0_diag_emit(P0_DIAG_MAIN, 0, P0_DIAG_STATE, 0, 0); /* boot前不写 */
    assert(g_p0_diag_store.bank[0].header[0].value == 0);
    p0_diag_boot(1U << 27, uid);
    assert(g_p0_diag_store.bank[0].header[3].value == 1);
    for (unsigned i = 0; i < 300; ++i)
        p0_diag_emit(P0_DIAG_UART, i, P0_DIAG_RX_BYTE, 0x20, i & 255);
    p0_diag_emit(P0_DIAG_MAIN, 300, P0_DIAG_PACKET | (8U << 8), 77, 1);
    p0_diag_emit(P0_DIAG_MAIN, 302, P0_DIAG_TX_COMPLETE | (129U << 8), 77, 1);
    p0_diag_bank_t previous;
    memcpy(&previous, (const void *)&g_p0_diag_store.bank[0], sizeof(previous));
    p0_diag_boot(1U << 26, uid);
    assert(g_p0_diag_store.bank[1].header[3].value == 2);
    assert(memcmp(&previous, (const void *)&g_p0_diag_store.bank[0], sizeof(previous)) == 0);
    for (unsigned i = 0; i < P0_DIAG_LANES; ++i)
        p0_diag_emit(i, 5, P0_DIAG_HW_READY, i, 0);
    p0_diag_emit(P0_DIAG_MAIN, 6, P0_DIAG_PACKET | (8U << 8) | (2U << 16), 88, 1);
    for (unsigned i = 0; i < 200; ++i)
        p0_diag_emit(P0_DIAG_MAIN, 10+i, P0_DIAG_STATE, i, 0);
    assert(g_p0_diag_store.bank[1].last_hello.word[3].value == 88);
    p0_diag_emit(P0_DIAG_LANES, 0, P0_DIAG_STATE, 1, 2); /* 非法lane无副作用 */
    if (argc == 2) {
        FILE *f = fopen(argv[1], "wb"); assert(f);
        assert(fwrite((const void *)&g_p0_diag_store, sizeof(g_p0_diag_store), 1, f) == 1);
        assert(fclose(f) == 0);
    }
    /* 头损坏不沿用其epoch；另一有效bank不被覆盖。 */
    g_p0_diag_store.bank[1].header[3].inverse ^= 1;
    p0_diag_boot(0, uid);
    assert(g_p0_diag_store.bank[1].header[3].value == 2);
    assert(memcmp(&previous, (const void *)&g_p0_diag_store.bank[0], sizeof(previous)) == 0);
    /* 翻位/半写以及UID不匹配的前史不能建立连续性。 */
    g_p0_diag_store.bank[0].header[0].value = 0;
    g_p0_diag_store.bank[1].header[0].value = 0;
    p0_diag_boot(0, uid);
    assert(g_p0_diag_store.bank[0].header[3].value == 1);
    g_p0_diag_store.bank[0].header[3].value = UINT32_MAX;
    g_p0_diag_store.bank[0].header[3].inverse = 0;
    p0_diag_boot(0, uid);
    assert(g_p0_diag_store.bank[1].header[3].value == 1); /* 跳0，解析器不称连续 */
    const uint32_t other[3] = {0x999, 0x456, 0x789};
    p0_diag_boot(0, other);
    assert(g_p0_diag_store.bank[0].header[3].value == 1);
    puts("dual-bank retention, lane wrap, milestones and torn-header recovery PASS (NO_DEVICE)");
    return 0;
}
