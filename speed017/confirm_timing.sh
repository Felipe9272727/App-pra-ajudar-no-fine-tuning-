#!/usr/bin/env bash
set -euo pipefail
cd /workspace/liquid-sense
for trial in 1 2 3; do
    test ! -e "speed017/reports/confirm_timing_${trial}.json"
    /dev/shm/liquid-android/prebuilt/speed017/bench speed017/model_locator.json time speed017/timing_ids_extended.json > "speed017/reports/confirm_timing_${trial}.json"
done
