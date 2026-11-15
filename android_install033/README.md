# Liquid Sense0.6.3 — rebuilt installer package

[Download the tested signed APK on Gofile — 1.97GB](https://gofile.io/d/ttGQz5Os).
Same package/certificate as previous releases, versionCode7,Android9+/ARM64.
Install over the existing app to retain its Android application data.

The user reported Android rejecting0.6.2 as an invalid package.0.6.3builds a fresh
ZIP rather than appending to prior signed ZIPs. It contains one current copy of
each record and one current signing block, plus normal zero signer alignment.
v1/v2/v3are independently verified, and resources.arsc/model assets stay stored
and aligned. All model weights and both native libraries are byte-identical.
Keyboard/navigation/motion fixes and local slash commands from032are retained.
No training or model-quality improvement is claimed.

**Actual Android result:** full old0.6.2and new0.6.3APKs both installed successfully
in a Google-APIs Android15/API35emulator supporting ARM64translation. Updating
preserved a test private-data marker. The new activity opened, remained alive
20seconds and rendered the chat home screen. This is an actual PackageManager
install and activity launch, not only a browser/mock or signature check.

The physical phone's refusal of0.6.2was not reproduced; a precise Xiaomi/HyperOS
or download-specific cause remains unconfirmed. No physical-device test or
keyboard interaction is claimed. Existing UI/model limitations remain.

Evidence: reports/Android15/result.json, old/new install outputs, update-marker,
launch, package metadata, logcat and actual emulator screen.png. Successful CI:
https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/actions/runs/43676111054
Setup failures, corrections and negative evidence are retained in CI_attempts.json.
The workflow uses one standard public runner and no private signing/upload keys.

Signed APK SHA256:
4735be854079941188e5f918e82d7c21d5468a437efe1bf7f45e72c15ade0e10

Exact canonical signed bytes are archived in apk_archive/ referencing unchanged
base/patch sources. portable_restore.py restores with Python's standard library;
tooluse022/archive_parts must first be hydrated with pack_archive.py restore.
portable_sources.json preserves the only32bytes otherwise requiring the old
port file; the original upstream file is fetched at a pinned revision and hashed.
All earlier signed APKs, weights and experiments remain byte-recoverable.
