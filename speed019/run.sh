#!/usr/bin/env bash
set -euo pipefail
cd /workspace/liquid-sense
# Call only after all018model workers and registered017timings finish.
export RUSTUP_HOME=/dev/shm/liquid-android/tooling/rustup
export CARGO_HOME=/dev/shm/liquid-android/tooling/cargo
export CARGO_TARGET_DIR=/dev/shm/liquid-android/speed019-target
export CARGO_BUILD_JOBS=2
cargo_bin=/dev/shm/liquid-android/tooling/cargo/bin/cargo
test ! -e speed019/reports/unit_tests.log
"$cargo_bin" test --locked --release --manifest-path speed019/runtime/Cargo.toml --lib > speed019/reports/unit_tests.log 2>&1
"$cargo_bin" build --locked --release --manifest-path speed019/runtime/Cargo.toml --bin bench > speed019/reports/build.log 2>&1
mkdir -p /dev/shm/liquid-android/prebuilt/speed019
cp "$CARGO_TARGET_DIR/release/bench" /dev/shm/liquid-android/prebuilt/speed019/bench
bench=/dev/shm/liquid-android/prebuilt/speed019/bench
for name in exact_trace chat_reference chat_fast; do test ! -e "speed019/reports/$name.json"; done
"$bench" speed017/model_locator.json trace speed017/trace_ids_extended.json > speed019/reports/exact_trace.json
"$bench" speed017/model_locator.json chat_reference speed017/chat_cases.json > speed019/reports/chat_reference.json
"$bench" speed017/model_locator.json chat_fast speed017/chat_cases.json > speed019/reports/chat_fast.json
for trial in 1 2 3; do
 test ! -e "speed019/reports/timing_${trial}.json"
 "$bench" speed017/model_locator.json time speed017/timing_ids_extended.json > "speed019/reports/timing_${trial}.json" 2> "speed019/reports/timing_${trial}.log"
done
