#include <cuda_runtime.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

__global__ void stress_kernel(float *a, float *b, float *c, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) {
        float x = a[i];
        float y = b[i];
        for (int k = 0; k < 20000; k++) {
            x = x * 1.000001f + y * 0.999999f;
            y = y * 0.999999f + x * 0.000001f;
        }
        c[i] = x + y;
    }
}

int main(int argc, char **argv) {
    int seconds = 1200;
    if (argc > 1) {
        seconds = atoi(argv[1]);
        if (seconds <= 0) {
            seconds = 1200;
        }
    }

    int n = 1 << 22;
    size_t bytes = (size_t)n * sizeof(float);
    float *a = NULL;
    float *b = NULL;
    float *c = NULL;

    cudaError_t err = cudaMallocManaged(&a, bytes);
    if (err != cudaSuccess) {
        fprintf(stderr, "cudaMallocManaged a failed: %s\n", cudaGetErrorString(err));
        return 1;
    }

    err = cudaMallocManaged(&b, bytes);
    if (err != cudaSuccess) {
        fprintf(stderr, "cudaMallocManaged b failed: %s\n", cudaGetErrorString(err));
        return 1;
    }

    err = cudaMallocManaged(&c, bytes);
    if (err != cudaSuccess) {
        fprintf(stderr, "cudaMallocManaged c failed: %s\n", cudaGetErrorString(err));
        return 1;
    }

    for (int i = 0; i < n; i++) {
        a[i] = 1.0f;
        b[i] = 2.0f;
        c[i] = 0.0f;
    }

    int threads = 256;
    int blocks = (n + threads - 1) / threads;
    printf("GPU stress test started for %d seconds\n", seconds);
    fflush(stdout);

    time_t start = time(NULL);
    while (time(NULL) - start < seconds) {
        stress_kernel<<<blocks, threads>>>(a, b, c, n);
        err = cudaDeviceSynchronize();
        if (err != cudaSuccess) {
            fprintf(stderr, "CUDA kernel failed: %s\n", cudaGetErrorString(err));
            return 1;
        }
    }

    printf("GPU stress test finished\n");
    cudaFree(a);
    cudaFree(b);
    cudaFree(c);
    return 0;
}
