# Liquid Sense Android 0.5 — optional Native029 epoch02

[Download the signed APK on Gofile](https://gofile.io/d/7OFCC99z) ·
1,969,325,396 bytes (1.97GB), Android9+/ARM64.

Install over the existing Liquid Sense Tools app. Same package
`dev.liquidsense.chat.tools`, versionCode3 and same signing certificate preserve
Android application data. No physical-device installation was performed here.
In **Trocar modelo**, choose **Experimental029 · época2 (Web e Python)**.
The General/WebPython model remains the default for new installations; previous
selections and per-model conversations remain. Base/offline and optional external
Specialist015E are preserved. The specialist still needs its separate installed
app, as before; the new epoch02 weights are fully bundled in this download.

This is the checkpoint from the second epoch of the four-epoch Native029 study,
not epoch04 and not a newly promoted general model. In the original Python
validation it scored1/4code tasks,10/20cases,6/8general, versus the selected
parent's0/4,2/20,4/8. It also lost3previous code cases and2general controls.
Those observed tests are not a fresh benchmark for this release.

**Port limitation:** all546 active text tensors match the evaluated native
checkpoint exactly, but generation is not guaranteed equivalent between the
Rust and Python runtimes. On the already observed chunks question, Rust emitted
a different program, passing1/5cases versus Python5/5. On19×7 it matched the
candidate's133; the parent retained123. This is a small host portability check,
not Android quality validation or a new superiority result. Both the selector
notice and About disclose the experimental status and runtime difference.

The native loop remains32physical layers/56executions, mHC2, temporal kernel7
and local windows256. No new training, quantization, extra loop passes or speed
improvement is claimed. The1.0GB decoded edit increases runtime RAM use, and the
353MB patch increases download size/startup work. These are exact compressed
weight differences, not on-device low-rank approximations.

Web search, isolated local MicroPython and Normal/Profundo/Extenso remain:
0/2048,1024/2048,2048/4096 reasoning/answer tokens, with context16384.
Agent limits remain6rounds/4actualtools. Tool histories for the new experimental
choice use their own conversation key, preserving the stable conversation.

Validation:18Rust tests,27Java agent checks, actual Android resource/Java/DEX
compilation, ARM64 JNI/ELF build, native hash/load/generation checks, full ZIP
CRC/alignment, APKv3 signature/certificate and embedded base/patch digests.
Gofile's returned name/size/MD5 match local bytes; public page returnedHTTP200.
The entire remote file was not downloaded again. No phone testing is claimed.

APK SHA256:
`9a1a487230f7979f441002cc885501f5eb79d1f859e12474cb6b14c93b239cac`.
Exact patch SHA256:
`0f19e758cbad61f86ca144c685994d1d6710b85b36d64e2a8be98731fe497310`.
Source archive is Native029 epoch02:
`73b452641035c272aef3ecb76e7fd8b2fd75b1e261007bb32107ad04c4fe4b06`.

`patch_archive/` preserves all85binary fragments. `apk_archive/` preserves the
remaining signed APK bytes and references the existing exact general pack;
stream reconstruction was checked against the full signed APK SHA256.
Restore with `python android_epochs030/restore.py --ref IMMUTABLE_COMMIT_SHA
--out NEW_OUTPUT.apk`. Original protected safetensors/general-pack source files
are required for full reconstruction. `--patch-only` restores just the new edit.
No prior checkpoint, APK archive or experiment was removed.

Rebuild: restore the documented Android tools/Rust1.90+ARM target, run
`restore_shared_assets.py`, `export_patch.py` (or restore the exact saved patch),
`compile.sh`, `compile_ui.py`, then `build_apk.py prepare`/`seal`.
Signing keys are private and are deliberately absent; signing a replacement
update requires the existing developer certificate. Public upload receipts are
sanitized; Gofile guest-account credentials remain outside the repository.
