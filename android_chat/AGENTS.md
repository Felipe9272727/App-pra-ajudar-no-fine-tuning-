# Android chat delivery

- This is a Rust offline inference/app port, not another weight-training study.
- Default is exact general principal best.pt (46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8).
  Never substitute vanilla Qwen or silently promote specialist015E/rejected016.
- Preserve physical32/plan56, per-visit independent caches, positive saved Loop
  gains, mHC2/Sinkhorn and Liquid-inspired conv7/window256. No official LFM claim.
- Quantization is a new approximate deployment format: report fidelity and
  limitations honestly; never treat packaging or app branding as a weight gain.
- No old source/checkpoint/report modification. Do not query sealed validation.
- Model bundled inside signed APK; no network permission, API keys or remote API.
- Use four CPU threads. Tools/builds go under /dev/shm/liquid-android because disk
  is almost full; preserve existing model files/Git objects. No background worker
  promise. End with checked APK/build evidence, or a precise remaining blocker.
