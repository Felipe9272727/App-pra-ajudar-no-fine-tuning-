# Android020 — separate fast preview delivery

After completed017/018/019research, build ARM64 preview0.1.1 with019runtime
optimizations ENABLED in nativeLoad. Same general BF16 pack, tokenizer, identity,
generation mode/budget,32physical/56visits, no quantization or new model weights.
018failed candidate is not packaged;015E remains a later explicit model option.

Original preview signing key was not retained. Preserve the installed app and
history by using a separate application ID dev.liquidsense.chat.fast, activity
class dev.liquidsense.chat.MainActivity (JNI names stay correct), label Liquid
Sense Rápido. Keep a new private signing key locally, never in public GitHub.
No INTERNET permission. Show measured native preparation/decode counters after
a response, with model-general/version label. No model selector yet.

Stream the exact old APK's STORED model asset into the new APK; no repeated
weight export. Space is limited; delete only rebuildable intermediate unsigned
files AFTER aligned/signed outputs are verified. Preserve both signed APKs.
Build with Rust1.90, AndroidAPI28+ official SDK/sysroot,16KB alignment. Verify
signature, permissions, ABI/ELF alignment, class/manifest and full model pack
SHA256. Publish source/build evidence and deliver via user's authorized Gofile.
No physical Android execution or Snapdragon speed claim without user/device
measurement. CPU019gain is host evidence only; weights remain unchanged.
