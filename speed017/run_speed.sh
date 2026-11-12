#!/usr/bin/env bash
set -euo pipefail
cd /workspace/liquid-sense
bench=/dev/shm/liquid-android/speed-target/release/bench
"$bench" speed017/model_locator.json trace /dev/shm/liquid-android/model/python_reference.json > speed017/reports/exact_trace.json
"$bench" speed017/model_locator.json time speed017/timing_ids.json > speed017/reports/timing.json
"$bench" speed017/model_locator.json chat_reference speed017/chat_cases.json > speed017/reports/chat_reference.json
"$bench" speed017/model_locator.json chat_fast speed017/chat_cases.json > speed017/reports/chat_fast.json
