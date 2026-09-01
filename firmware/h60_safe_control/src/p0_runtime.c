#include <stddef.h>

void *memset(void *destination, int value, size_t length)
{
    unsigned char *output = (unsigned char *)destination;
    size_t i;

    for (i = 0; i < length; ++i) {
        output[i] = (unsigned char)value;
    }
    return destination;
}

void *memcpy(void *destination, const void *source, size_t length)
{
    unsigned char *output = (unsigned char *)destination;
    const unsigned char *input = (const unsigned char *)source;
    size_t i;

    for (i = 0; i < length; ++i) {
        output[i] = input[i];
    }
    return destination;
}
