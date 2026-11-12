#!/usr/bin/env bash
set -euo pipefail
cd /workspace/liquid-sense
bench=${LS_SPEED_BENCH:-/dev/shm/liquid-android/prebuilt/speed017/bench}
reports=${LS_SPEED_REPORTS:?Choose a new output directory; archived results cannot be overwritten}
mkdir -p "$reports"
for name in exact_trace timing chat_reference chat_fast; do test ! -e "$reports/$name.json"; done
"$bench" speed017/model_locator.json trace speed017/trace_ids_extended.json > "$reports/exact_trace.json"
"$bench" speed017/model_locator.json time speed017/timing_ids.json > "$reports/timing.json"
"$bench" speed017/model_locator.json chat_reference speed017/chat_cases.json > "$reports/chat_reference.json"
"$bench" speed017/model_locator.json chat_fast speed017/chat_cases.json > "$reports/chat_fast.json"
