# Delivery035 — hash mismatch confirmed on selected physical APK
- Actual phone file has correct byte count but wrong SHA256. It is not the preserved signed0.6.3. Parser returned null. No session installation attempted; no legacy install error captured. Do not assert storage/network/host/malware cause without evidence.
- "App not found" only refers to expected queried Tools package; not proof user conversations/app were removed.
- Gofile original receipt matched size+MD5, but never full-redownloaded. Current API denies content metadata/premium and then rate limits. Stop attempts to that endpoint; no bypass. Exact served APK not available to compare, so delivery fault location unknown.
- Recover exact immutable0.6.3 APK from preserved public sources. No training, new large app rebuild or version bump. Publish ZIP+checksums via GitHub Release; require full remote ZIP redownload/SHA and contained APK hash before link delivery. Keep physical installation pending user action. No uninstall/data wipe.
- Old releases/checkpoints remain untouched. No signing credentials required for recovery. One standard public runner, maximum4threads, no model inference needed.
