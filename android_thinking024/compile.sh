#!/usr/bin/env bash
set -euo pipefail
cd /workspace/liquid-sense
export RUSTUP_HOME=/dev/shm/liquid-android/tooling/rustup
export CARGO_HOME=/dev/shm/liquid-android/tooling/cargo
export PATH="$CARGO_HOME/bin:$PATH"
export CARGO_BUILD_JOBS=2
export CARGO_TARGET_DIR=/dev/shm/liquid-android/thinking024/rust-host-target
cargo +1.90.0 test --locked --release --manifest-path android_thinking024/native/Cargo.toml --lib > android_thinking024/reports/rust_unit_tests.log 2>&1
cargo +1.90.0 build --locked --release --manifest-path android_thinking024/native/Cargo.toml --bin toolcheck > android_thinking024/reports/rust_host_build.log 2>&1
mkdir -p /dev/shm/liquid-android/prebuilt/thinking024
cp "$CARGO_TARGET_DIR/release/toolcheck" /dev/shm/liquid-android/prebuilt/thinking024/toolcheck
/dev/shm/liquid-android/prebuilt/thinking024/toolcheck > android_thinking024/reports/native_template_parity.log
rm -rf "$CARGO_TARGET_DIR"
export CARGO_TARGET_DIR=/dev/shm/liquid-android/thinking024/rust-arm-target
model_sysroot=/dev/shm/liquid-android/tooling/android/sysroot
rust_toolroot=$(rustc +1.90.0 --print sysroot)
export RUSTFLAGS="-C linker-flavor=ld.lld -C linker=$rust_toolroot/lib/rustlib/x86_64-unknown-linux-gnu/bin/rust-lld -C link-arg=-L$model_sysroot/28 -C link-arg=-L$model_sysroot -C link-arg=-z -C link-arg=max-page-size=16384"
cargo +1.90.0 build --locked --release --target aarch64-linux-android --manifest-path android_thinking024/native/Cargo.toml --lib > android_thinking024/reports/rust_arm_build.log 2>&1
cp "$CARGO_TARGET_DIR/aarch64-linux-android/release/libliquid_sense.so" /dev/shm/liquid-android/prebuilt/thinking024/libliquid_sense.so
readelf -h -l /dev/shm/liquid-android/prebuilt/thinking024/libliquid_sense.so > android_thinking024/reports/rust_arm_elf.txt
rm -rf "$CARGO_TARGET_DIR" "$CARGO_HOME" "$RUSTUP_HOME"
