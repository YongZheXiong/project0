#ifndef P0_BUILD_CONFIG_H
#define P0_BUILD_CONFIG_H

#ifndef P0_MOTION_OUTPUT_COMPILED
#define P0_MOTION_OUTPUT_COMPILED 0
#endif

#if P0_MOTION_OUTPUT_COMPILED != 0
#error "H60 safe-bringup v0.1 must be built with motion output disabled"
#endif

#define P0_FIRMWARE_VERSION_MAJOR 0
#define P0_FIRMWARE_VERSION_MINOR 1
#define P0_FIRMWARE_VERSION_PATCH 1

#endif
