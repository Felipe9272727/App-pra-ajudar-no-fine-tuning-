# Install033 — clean packaging and actual Android installer regression

The user supplied a real phone screenshot: Android refused0.6.2 with the generic
"package appears invalid" message. That message does not identify the precise
failure code. No physical-device logcat or downloaded-file SHA is available.

Inspection found repeated append-mode updates had left superseded ZIP records
and old signing blocks in the payload. Existing ZIP CRC/aapt/apksigner checks had
not established Android installation. This is a packaging issue under study,
not a neural/model-quality experiment.

0.6.3rebuilds a fresh ZIP from logical current assets, manifest first, compressed
resources handled correctly, stored/4-byte-aligned resources.arsc and large model
assets, one copy of each entry and one current APK signing block. Only normal
zero signing alignment padding is permitted. Old signed APKs remain exactly
recoverable; only redundant RAM build cache was retired after reconstruction SHA
verification. Both native libraries, base pack and epoch02edit are byte-identical.

The same developer certificate signs v1/v2/v3. Each signature is verified with a
range exercising that scheme (21..23,24..27,28..35). Those signature-only ranges
are not a claim the app's Android9minimum was reduced. Default apksigner output
can mark older schemes false when it skips them; it must not alone be interpreted
as their absence. Previous builder configuration explicitly disabledv1/v2.

A standard public GitHub runner starts a Google-APIs Android15x86_64emulator with
ARM64translation. CI restores the exact original0.6.2and clean0.6.3signed APK bytes
using only pinned upstream data and immutable Git fragments, without a signing
key or Gofile credentials. It attempts old installation, falls back to old0.6.0
as an update baseline when needed, tests new installation/update, records a test
private-data marker across update and attempts an activity launch.

CI run43674895719, commit5509a94387639a8d5beb92aee01780f39a63312e.
Installer results will be recorded separately, including negative evidence.
An emulator result is not proof of Xiaomi/HyperOS behavior or every UI function.
No model training, extra loops or quality/speed claim is made.

## Final observed result

Run43676111054succeeded on Android15/API35, x86_64with actualARM64native
translation (libndk_translation). Exact old0.6.2SHA614cdc6 and new0.6.3SHA4735be8
were restored and installed through actual adb PackageManager. BOTH returned
Success. The update kept a fixture file in private application data. The new
activity started successfully, remained alive after20s, and its screen capture
shows the rendered Liquid Sense chat home. These are not mocked-bridge tests.

The old phone refusal was NOT reproduced in this emulator. Therefore a precise
Xiaomi/HyperOS or downloaded-file failure cause is still unconfirmed. Fresh ZIP
and broader signatures are packaging hardening, not a proven isolated root cause
on the physical phone. No physical phone, keyboard interaction, model-answer
quality or speed was tested in this run. See reports/Android15/result.json,
install outputs, launch log, package data and actual screen.png.

Failed harness setup attempts and their evidence are preserved in CI_attempts.
The corrected CI hydrates the existing verified archive tar parts, preflights all
inputs and explicitly creates the AVD descriptor. No new model work occurred.
