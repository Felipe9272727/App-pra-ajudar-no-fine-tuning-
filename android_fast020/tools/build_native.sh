#!/usr/bin/env bash
set -euo pipefail
cd /workspace/liquid-sense
export RUSTUP_HOME=/dev/shm/liquid-android/tooling/rustup
export CARGO_HOME=/dev/shm/liquid-android/tooling/cargo
export PATH="$CARGO_HOME/bin:$PATH"
export CARGO_TARGET_DIR=/dev/shm/liquid-android/fast020-target
export CARGO_BUILD_JOBS=2
native_sysroot=/dev/shm/liquid-android/tooling/android/sysroot
rust_toolroot=$(rustc +1.90.0 --print sysroot)
export RUSTFLAGS="-C linker-flavor=ld.lld -C linker=$rust_toolroot/lib/rustlib/x86_64-unknown-linux-gnu/bin/rust-lld -C link-arg=-L$native_sysroot/28 -C link-arg=-L$native_sysroot -C link-arg=-z -C link-arg=max-page-size=16384"
cargo +1.90.0 build --locked --release --target aarch64-linux-android --manifest-path android_fast020/native/Cargo.toml
mkdir -p /dev/shm/liquid-android/prebuilt/fast020
cp "$CARGO_TARGET_DIR/aarch64-linux-android/release/libliquid_sense.so" /dev/shm/liquid-android/prebuilt/fast020/libliquid_sense.so
readelf -h -l /dev/shm/liquid-android/prebuilt/fast020/libliquid_sense.so > android_fast020/reports/arm64_elf.txt
