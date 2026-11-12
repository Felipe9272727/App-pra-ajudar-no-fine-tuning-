# Reproduce in a separate output directory

Source baseline is android_chat/native at Android commit5a7d0a2. Prototype is
runtime/. Do not overwrite completed reports, original APK or model checkpoints.

Install Rust1.90 with user-owned caches. Build using
`cargo build --locked --release --manifest-path speed017/runtime/Cargo.toml --bin bench`
and `cargo test --locked --release --manifest-path speed017/runtime/Cargo.toml --lib`.
The study retained a host binary at reports/host_binary.json's path; its sha is
recorded. Reinstallable build caches were removed for memory during training.

Use the retained signed0.1.0 APK, also delivered via https://gofile.io/d/A79W3fzk.
Run `python speed017/locate_pack.py /path/to/LiquidSense-0.1.0-preview.apk /new/locator.json`.
It verifies all embedded pack bytes and locates the ZIP_STORED asset without
extracting1.6GB again. bench accepts that locator as its first argument.
The source APK checksum is in android_chat/reports, and the exact pack SHA is
6c774a434438add704b1993b8e013493fb95bc9802c4d9b30227832115c07288.

For exact traces use `bench locator.json trace speed017/trace_ids_extended.json`.
For warmup/ABBA backbone measurements use `bench locator.json time speed017/timing_ids_extended.json`.
Use a new redirected filename. For chat modes copy exact public tokenizer.json
and identity fixtures from the original Android artifact; the host harness
currently loads tokenizer from /dev/shm/liquid-android/model/tokenizer.json.
Its known SHA is5f9e4d4901a92b997e463c1f46055088b6cca5ca61a6522d1b9f64c4bb81cb42.

`run_speed.sh` requires LS_SPEED_REPORTS pointing to new output; it refuses to
overwrite existing results. Set LS_SPEED_BENCH if compiled elsewhere. The
256K-vocabulary weights and56cache slots remain part of each measured run.
No updated Android APK is produced by this source experiment. ARM build and
actual device measurements remain necessary before a release-speed claim.
