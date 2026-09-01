#include "p0_build_config.h"

const char p0_firmware_manifest[]
    __attribute__((used, section(".firmware_manifest"))) =
        "P0_H60_SAFE;FW=0.1.1;MOTION=0;TIMEOUT_MS=250";
