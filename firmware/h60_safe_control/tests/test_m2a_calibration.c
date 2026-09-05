#include "p0_m2a_calibration.h"

#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>

#define CHECK(condition)                                                       \
    do {                                                                       \
        if (!(condition)) {                                                    \
            fprintf(stderr, "FAIL %s:%d: %s\n", __FILE__, __LINE__,          \
                    #condition);                                               \
            exit(EXIT_FAILURE);                                                \
        }                                                                      \
    } while (0)

static void check_all_zero(const int16_t output[4])
{
    size_t i;

    for (i = 0; i < 4U; ++i) {
        CHECK(output[i] == 0);
    }
}

static void test_requires_arm_and_enforces_single_channel_limit(void)
{
    p0_m2a_calibration_t calibration;
    int16_t output[4] = {1, 1, 1, 1};

    p0_m2a_calibration_reset(&calibration);
    CHECK(!p0_m2a_calibration_hold(
        &calibration, 0, 1, 50, 10, output));
    check_all_zero(output);

    CHECK(p0_m2a_calibration_arm(&calibration, 20));
    CHECK(p0_m2a_calibration_hold(
        &calibration, 2, -1, P0_M2A_MAX_DUTY_PERMILLE, 21, output));
    CHECK(output[0] == 0);
    CHECK(output[1] == 0);
    CHECK(output[2] == -(int16_t)P0_M2A_MAX_DUTY_PERMILLE);
    CHECK(output[3] == 0);
}

static void test_invalid_requests_fail_closed(void)
{
    p0_m2a_calibration_t calibration;
    int16_t output[4];

    CHECK(p0_m2a_calibration_arm(&calibration, 0));
    CHECK(!p0_m2a_calibration_hold(
        &calibration, 4, 1, 50, 1, output));
    CHECK(!calibration.armed);
    check_all_zero(output);

    CHECK(p0_m2a_calibration_arm(&calibration, 0));
    CHECK(!p0_m2a_calibration_hold(
        &calibration, 0, 1, P0_M2A_MAX_DUTY_PERMILLE + 1U, 1, output));
    CHECK(!calibration.armed);
    check_all_zero(output);

    CHECK(p0_m2a_calibration_arm(&calibration, 0));
    CHECK(!p0_m2a_calibration_hold(
        &calibration, 0, 0, 1, 1, output));
    CHECK(!calibration.armed);
    check_all_zero(output);
}

static void test_release_and_hold_lease(void)
{
    p0_m2a_calibration_t calibration;
    int16_t output[4];

    CHECK(p0_m2a_calibration_arm(&calibration, 100));
    CHECK(p0_m2a_calibration_hold(
        &calibration, 1, 1, 50, 101, output));
    CHECK(p0_m2a_calibration_service(
        &calibration,
        101 + P0_M2A_HOLD_LEASE_MS,
        output) == P0_M2A_SERVICE_OK);
    CHECK(p0_m2a_calibration_service(
        &calibration,
        102 + P0_M2A_HOLD_LEASE_MS,
        output) == P0_M2A_SERVICE_HOLD_EXPIRED);
    CHECK(!calibration.armed);
    check_all_zero(output);

    CHECK(p0_m2a_calibration_arm(&calibration, 200));
    CHECK(p0_m2a_calibration_hold(
        &calibration, 1, 1, 50, 201, output));
    CHECK(p0_m2a_calibration_hold(
        &calibration, 1, 0, 0, 202, output));
    CHECK(calibration.armed);
    CHECK(!calibration.output_active);
    check_all_zero(output);
}

static void test_session_hard_limit_and_clock_wrap(void)
{
    p0_m2a_calibration_t calibration;
    int16_t output[4];
    uint32_t start = UINT32_MAX - UINT32_C(20);

    CHECK(p0_m2a_calibration_arm(&calibration, start));
    CHECK(p0_m2a_calibration_hold(
        &calibration, 3, -1, 60, start + UINT32_C(1), output));
    CHECK(p0_m2a_calibration_service(
        &calibration, UINT32_C(10), output) == P0_M2A_SERVICE_OK);

    CHECK(p0_m2a_calibration_arm(&calibration, 1000));
    CHECK(p0_m2a_calibration_service(
        &calibration,
        1000 + P0_M2A_MAX_ARMED_MS,
        output) == P0_M2A_SERVICE_OK);
    CHECK(p0_m2a_calibration_service(
        &calibration,
        1001 + P0_M2A_MAX_ARMED_MS,
        output) == P0_M2A_SERVICE_SESSION_EXPIRED);
    CHECK(!calibration.armed);
    check_all_zero(output);
}

int main(void)
{
    test_requires_arm_and_enforces_single_channel_limit();
    test_invalid_requests_fail_closed();
    test_release_and_hold_lease();
    test_session_hard_limit_and_clock_wrap();
    puts("PASS: H60 M2-A calibration host tests");
    return EXIT_SUCCESS;
}
