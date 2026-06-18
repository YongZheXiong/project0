#!/usr/bin/env bash
set -euo pipefail

DURATION="${1:-1200}"
TEMP_LIMIT_C="${2:-85}"
LOG_DIR="$HOME/orionx_thermal_test"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_ID="$(date +%Y%m%d_%H%M%S)"
RUN_DIR="$LOG_DIR/mixed_$RUN_ID"
mkdir -p "$RUN_DIR"

TEGRA_LOG="$RUN_DIR/tegrastats.log"
SUMMARY="$RUN_DIR/summary.txt"
GPU_LOG="$RUN_DIR/gpu_stress.log"
CPU_LOG="$RUN_DIR/stress_ng.log"
GPU_BIN="$RUN_DIR/gpu_stress"

cleanup() {
  set +e
  pkill -f "$GPU_BIN" >/dev/null 2>&1
  pkill stress-ng >/dev/null 2>&1
  if [[ -n "${TEGRA_PID:-}" ]]; then
    kill "$TEGRA_PID" >/dev/null 2>&1
    wait "$TEGRA_PID" >/dev/null 2>&1
  fi
}
trap cleanup EXIT

{
  echo "run_dir=$RUN_DIR"
  echo "duration_seconds=$DURATION"
  echo "temp_limit_c=$TEMP_LIMIT_C"
  echo "started_at=$(date)"
  echo
  echo "nvpmodel:"
  nvpmodel -q || true
  echo
  echo "tools:"
  command -v stress-ng || true
  command -v nvcc || command -v /usr/local/cuda/bin/nvcc || true
  command -v tegrastats || true
} | tee "$SUMMARY"

if ! command -v stress-ng >/dev/null 2>&1; then
  echo "stress-ng is missing; install it first." | tee -a "$SUMMARY"
  exit 2
fi

NVCC_BIN="$(command -v nvcc || true)"
if [[ -z "$NVCC_BIN" && -x /usr/local/cuda/bin/nvcc ]]; then
  NVCC_BIN=/usr/local/cuda/bin/nvcc
fi
if [[ -z "$NVCC_BIN" ]]; then
  echo "nvcc is missing; cannot run CUDA GPU stress." | tee -a "$SUMMARY"
  exit 3
fi

"$NVCC_BIN" "$SCRIPT_DIR/orin_nx_gpu_stress.cu" -O3 -o "$GPU_BIN"

tegrastats --interval 1000 --logfile "$TEGRA_LOG" >/dev/null 2>&1 &
TEGRA_PID="$!"
sleep 2

"$GPU_BIN" "$DURATION" >"$GPU_LOG" 2>&1 &
GPU_PID="$!"

stress-ng --cpu 4 --cpu-method matrixprod --vm 2 --vm-bytes 2G --matrix 2 --timeout "${DURATION}s" --metrics-brief >"$CPU_LOG" 2>&1 &
CPU_PID="$!"

(
  while kill -0 "$CPU_PID" >/dev/null 2>&1 || kill -0 "$GPU_PID" >/dev/null 2>&1; do
    latest_tj="$(tail -n 1 "$TEGRA_LOG" 2>/dev/null | grep -o 'tj@[0-9.]*C' | sed 's/tj@//;s/C//' || true)"
    if [[ -n "$latest_tj" ]] && awk "BEGIN { exit !($latest_tj >= $TEMP_LIMIT_C) }"; then
      echo "Safety stop: tj reached ${latest_tj}C, limit is ${TEMP_LIMIT_C}C" | tee -a "$SUMMARY"
      pkill -f "$GPU_BIN" >/dev/null 2>&1
      pkill stress-ng >/dev/null 2>&1
      break
    fi
    sleep 5
  done
) &
MONITOR_PID="$!"

set +e
wait "$CPU_PID"
CPU_STATUS="$?"
wait "$GPU_PID"
GPU_STATUS="$?"
set -e
kill "$MONITOR_PID" >/dev/null 2>&1 || true
sleep 2
cleanup
trap - EXIT

{
  echo
  echo "finished_at=$(date)"
  echo "cpu_status=$CPU_STATUS"
  echo "gpu_status=$GPU_STATUS"
  echo
  echo "last_20_tegrastats:"
  tail -n 20 "$TEGRA_LOG" || true
  echo
  echo "highest_tj:"
  grep -o 'tj@[0-9.]*C' "$TEGRA_LOG" | sed 's/tj@//;s/C//' | sort -n | tail -n 1 || true
  echo
  echo "highest_cpu:"
  grep -o 'cpu@[0-9.]*C' "$TEGRA_LOG" | sed 's/cpu@//;s/C//' | sort -n | tail -n 1 || true
  echo
  echo "highest_gpu:"
  grep -o 'gpu@[0-9.]*C' "$TEGRA_LOG" | sed 's/gpu@//;s/C//' | sort -n | tail -n 1 || true
  echo
  echo "highest_vdd_in_mw:"
  grep -o 'VDD_IN [0-9]*mW' "$TEGRA_LOG" | awk '{print $2}' | sed 's/mW//' | sort -n | tail -n 1 || true
  echo
  echo "gpu_log_tail:"
  tail -n 20 "$GPU_LOG" || true
  echo
  echo "stress_ng_tail:"
  tail -n 20 "$CPU_LOG" || true
} | tee -a "$SUMMARY"

echo "$RUN_DIR"
