#!/usr/bin/env bash
set -euo pipefail
cd /workspace/liquid-sense
export RUSTUP_HOME=/dev/shm/liquid-android/tooling/rustup
export CARGO_HOME=/dev/shm/liquid-android/tooling/cargo
export PATH="$CARGO_HOME/bin:$PATH"
export CARGO_BUILD_JOBS=2
export CARGO_TARGET_DIR=/dev/shm/liquid-android/models021-host-target
cargo +1.90.0 test --locked --release --manifest-path android_models021/native/Cargo.toml --lib > android_models021/reports/unit_tests.log 2>&1
cargo +1.90.0 build --locked --release --manifest-path android_models021/native/Cargo.toml --bin specialist > android_models021/reports/host_build.log 2>&1
mkdir -p /dev/shm/liquid-android/prebuilt/models021
cp "$CARGO_TARGET_DIR/release/specialist" /dev/shm/liquid-android/prebuilt/models021/specialist
rm -rf "$CARGO_TARGET_DIR"
export CARGO_TARGET_DIR=/dev/shm/liquid-android/models021-arm-target
model_sysroot=/dev/shm/liquid-android/tooling/android/sysroot
rust_toolroot=$(rustc +1.90.0 --print sysroot)
export RUSTFLAGS="-C linker-flavor=ld.lld -C linker=$rust_toolroot/lib/rustlib/x86_64-unknown-linux-gnu/bin/rust-lld -C link-arg=-L$model_sysroot/28 -C link-arg=-L$model_sysroot -C link-arg=-z -C link-arg=max-page-size=16384"
cargo +1.90.0 build --locked --release --target aarch64-linux-android --manifest-path android_models021/native/Cargo.toml > android_models021/reports/arm_build.log 2>&1
cp "$CARGO_TARGET_DIR/aarch64-linux-android/release/libliquid_sense.so" /dev/shm/liquid-android/prebuilt/models021/libliquid_sense.so
readelf -h -l /dev/shm/liquid-android/prebuilt/models021/libliquid_sense.so > android_models021/reports/arm64_elf.txt
rm -rf "$CARGO_TARGET_DIR" "$CARGO_HOME" "$RUSTUP_HOME"
