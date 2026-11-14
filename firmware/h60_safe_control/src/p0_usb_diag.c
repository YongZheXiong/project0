#include "p0_usb_diag.h"
#include <stdatomic.h>
#include <stddef.h>

#if P0_USB_RX_DIAG_BUILD != 1
#error "Receiver journal is only part of the explicit diagnostic candidate"
#endif
_Static_assert(sizeof(p0_diag_bank_t) == P0_DIAG_BANK_BYTES, "bank layout");
_Static_assert(sizeof(p0_diag_store_t) == P0_DIAG_BYTES, "store layout");
volatile p0_diag_store_t g_p0_diag_store
    __attribute__((used, section(".p0_usb_diag")));
static unsigned active;
static bool ready;
static uint32_t sequence[P0_DIAG_LANES];
static unsigned cursor[P0_DIAG_LANES];

static void word(volatile p0_diag_word_t *p, uint32_t v)
{ p->value = v; p->inverse = ~v; }
static bool header_valid(const volatile p0_diag_bank_t *b, const uint32_t uid[3])
{
    for (unsigned i = 0; i < 8; ++i)
        if (b->header[i].inverse != ~b->header[i].value) return false;
    if (b->header[0].value != P0_DIAG_MAGIC ||
        b->header[1].value != P0_DIAG_SCHEMA ||
        b->header[2].value != P0_DIAG_BANK_BYTES || !b->header[3].value) return false;
    for (unsigned i = 0; i < 3; ++i)
        if (b->header[5+i].value != uid[i]) return false;
    return true;
}
void p0_diag_boot(uint32_t reset_flags, const uint32_t uid[3])
{
    bool v0, v1;
    uint32_t epoch = 1;
    ready = false;
    v0 = header_valid(&g_p0_diag_store.bank[0], uid);
    v1 = header_valid(&g_p0_diag_store.bank[1], uid);
    active = 0;
    if (v0 || v1) {
        unsigned last = v1 ? 1 : 0;
        if (v0 && v1 && (uint32_t)(g_p0_diag_store.bank[0].header[3].value -
             g_p0_diag_store.bank[1].header[3].value) < UINT32_C(0x80000000)) last = 0;
        epoch = g_p0_diag_store.bank[last].header[3].value + 1;
        if (!epoch) epoch = 1;
        active = 1 - last;
    }
    volatile p0_diag_bank_t *bank = &g_p0_diag_store.bank[active];
    /* UART/SysTick启用前初始化；保留另一bank原字节，不作Flash写。 */
    word(&bank->header[0], 0);
    volatile unsigned char *bytes = (volatile unsigned char *)bank;
    for (size_t i = 8; i < sizeof(*bank); ++i) bytes[i] = 0;
    word(&bank->header[1], P0_DIAG_SCHEMA);
    word(&bank->header[2], P0_DIAG_BANK_BYTES);
    word(&bank->header[3], epoch);
    word(&bank->header[4], reset_flags);
    for (unsigned i = 0; i < 3; ++i) word(&bank->header[5+i], uid[i]);
    for (unsigned i = 0; i < P0_DIAG_LANES; ++i) sequence[i] = cursor[i] = 0;
    atomic_thread_fence(memory_order_release);
    word(&bank->header[0], P0_DIAG_MAGIC);
    ready = true;
    p0_diag_emit(P0_DIAG_MAIN, 0, P0_DIAG_BOOT, epoch, reset_flags);
}
void p0_diag_emit(unsigned lane, uint32_t tick, uint32_t event, uint32_t a, uint32_t b)
{
    volatile p0_diag_event_t *entries;
    unsigned capacity;
    if (!ready || lane >= P0_DIAG_LANES || sequence[lane] == UINT32_MAX) return;
    volatile p0_diag_bank_t *bank = &g_p0_diag_store.bank[active];
    switch (lane) {
    case P0_DIAG_MAIN: entries = bank->main; capacity = 64; break;
    case P0_DIAG_UART: entries = bank->uart; capacity = 96; break;
    case P0_DIAG_TICK: entries = bank->tick; capacity = 16; break;
    default: entries = bank->fault; capacity = 8; break;
    }
    uint32_t seq = ++sequence[lane];
    volatile p0_diag_event_t *e = &entries[cursor[lane]];
    if (++cursor[lane] == capacity) cursor[lane] = 0;
    e->word[0].value = 0;
    atomic_thread_fence(memory_order_release);
    word(&e->word[1], tick); word(&e->word[2], event);
    word(&e->word[3], a); word(&e->word[4], b);
    e->word[0].inverse = ~seq;
    atomic_thread_fence(memory_order_release);
    e->word[0].value = seq; /* 每条记录最后提交；半写/翻位不当作完整证据。 */
    if (lane == P0_DIAG_MAIN &&
        (((event & 255) == P0_DIAG_PACKET && ((event >> 8) & 255) == 8) ||
         ((event & 255) == P0_DIAG_TX_COMPLETE && ((event >> 8) & 255) == 129))) {
        volatile p0_diag_event_t *saved = (event & 255) == P0_DIAG_PACKET ?
            &bank->last_hello : &bank->last_ack_complete;
        saved->word[0].value = 0;
        for (unsigned i = 1; i < 5; ++i) saved->word[i] = e->word[i];
        saved->word[0].inverse = ~seq;
        atomic_thread_fence(memory_order_release);
        saved->word[0].value = seq;
    }
}
