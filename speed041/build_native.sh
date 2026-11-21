#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export RUSTUP_HOME=/dev/shm/speed041/tooling/rustup
export CARGO_HOME=/dev/shm/speed041/tooling/cargo
export CARGO_TARGET_DIR=/dev/shm/speed041/arm-target
export TMPDIR=/dev/shm/speed041/tmp
export PATH="$CARGO_HOME/bin:$PATH"
android_sysroot=/dev/shm/liquid-android/tooling/android/sysroot
rust_sysroot=$(rustc +1.90.0 --print sysroot)
export RUSTFLAGS="-C linker-flavor=ld.lld -C linker=$rust_sysroot/lib/rustlib/x86_64-unknown-linux-gnu/bin/rust-lld -C link-arg=-L$android_sysroot/28 -C link-arg=-L$android_sysroot -C link-arg=-z -C link-arg=max-page-size=16384"
cargo +1.90.0 build --locked --release --jobs 2 --target aarch64-linux-android --manifest-path speed041/native/Cargo.toml --lib
cp "$CARGO_TARGET_DIR/aarch64-linux-android/release/libliquid_sense.so" /dev/shm/speed041/libliquid_sense.so
readelf -h -l -d /dev/shm/speed041/libliquid_sense.so
