# Speed017
- Read PROTOCOL.md, REPORT.md, reports/summary.json and status before runs.
- Preserve baseline android_chat source and installed0.1.0 APK; no weight edits.
- Prototype lives in runtime/; optimize flag toggles row-major GDN and cached
  constant gates, reuse_prefix toggles exact session reuse. Default Model flag
  remains false; benchmark explicitly enables it. No updated APK is claimed.
- All32physical/56virtual visits and independent caches stay active.
- Four CPU threads, one model process. Hardware is cloud x86, not user Snapdragon.
- Seven tests and16-token bitwise trace plus3chat probes completed. Do not repeat
  completed measurements to make a better number. Four timing pairs show1.122x
  observed backbone ratio, paired p=.125; no significant speed claim or promotion.
- Actual unchanged model pack maps directly from stored asset in retained APK:
  model_locator.json. The redundant raw temporary .lsp was hash-verified then
  removed for space; canonical checkpoints and APK remain intact.
- Host benchmark executable retained under /dev/shm/liquid-android/prebuilt/speed017.
  Reinstallable compiler/build caches were removed before PyTorch training.
- CONFIRMATORY_TIMING.md registers one NEW fixed twelve-pair replication to
  resolve the exploratory interval including zero. No old rows overwritten or
  pooled, no stopping on significance, and no further repetitions regardless
  of result. This is a declared uncertainty check, not selection of faster runs.
