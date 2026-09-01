#ifndef P0_CRC32_H
#define P0_CRC32_H

#include <stddef.h>
#include <stdint.h>

uint32_t p0_crc32_ieee(const uint8_t *data, size_t length);

#endif
