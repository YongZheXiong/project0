#include "p0_crc32.h"

uint32_t p0_crc32_ieee(const uint8_t *data, size_t length)
{
    uint32_t crc = UINT32_C(0xFFFFFFFF);
    size_t i;

    for (i = 0; i < length; ++i) {
        uint32_t current = (uint32_t)data[i];
        uint8_t bit;

        crc ^= current;
        for (bit = 0; bit < UINT8_C(8); ++bit) {
            uint32_t mask = (uint32_t)(-(int32_t)(crc & UINT32_C(1)));
            crc = (crc >> 1) ^ (UINT32_C(0xEDB88320) & mask);
        }
    }
    return ~crc;
}
