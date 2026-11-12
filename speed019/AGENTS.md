# Speed019 — exact matrix-zero shortcut only

- Read PROTOCOL.md and current status/reports before any run; no weights change.
- This follows017runtime with proof of16numerically zero BF16 output matrices.
  Detect actual bytes at load. Only AVX2/NEON+finite-input shortcut is eligible;
  scalar/nonfinite paths retain reference. Signed-zero behavior is tested.
- Every32physical/56virtual layer, all mHC merges and independent temporal/KV
  states execute. Skip only proven-zero matrix multiplication, never a layer.
- Baseline source hashes point to preserved017source. Prototype in runtime/.
- One model process/four threads. Wait for018models and017fixed confirmation
  before compilation/019measurements. No CPU speed inference from phone specs.
- Fixed12timing pairs and exact16trace/3chat probes; no repetitions to select
  a better number. 019ratio is all optimizations versus reference, not a factor
  to multiply by017's ratio. Keep every raw result, including null/negative.
- This is source/host runtime only; installed signed0.1.0APK remains preserved.
  No Android/ARM binary build or physical device validation is claimed here.
