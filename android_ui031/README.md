# Liquid Sense Android0.6 — chat UI refresh

[Download on Gofile — 1.97GB](https://gofile.io/d/fl8LUcK7) · Android9+/ARM64.

A new local chat interface inspired by public ChatGPT/Claude interaction patterns.
This release changes presentation and local conversation management. It does not
train the model, improve neural quality or change inference kernels.

- Compact top model menu; grouped Base/general, Loop029 experimental and Code015E.
  Base/WebPython and Base/offline explicitly use the same weights.
- Navigation drawer, new chats, searchable local conversation archive; four legacy
  model/profile IDs and their previous conversations are migrated and preserved.
- Neutral user bubbles and flowing assistant answers; readable Markdown/code
  blocks with exact-source copy buttons. No raw answer HTML is interpreted.
- Collapsible real activity, actual thought output, returned web sources and
  Python output. Search/Python indicators only follow actual validated execution.
- Stop, continue, local diagnostics and Normal/Profundo/Extenso presets remain.
  Forced thinking closure is labelled as a limit, not completed reasoning.
- Responsive dark charcoal/lavender UI with a serif welcome heading. No copied
  OpenAI/Anthropic branding, online UI services, account login or CDN resources.

The app uses Rust for inference, Java for Android/JNI/tools, MicroPython C for
local execution, and bundled HTML/CSS/JavaScript for presentation. The WebView
loads only three whitelisted APK assets through an intercepted HTTPS app-assets
origin. Other WebView requests/navigation are blocked; source links open in the
external browser. CSP, narrow bridge commands, safe DOM rendering and URL scheme
checks keep model/web/user content from becoming UI scripts.

Goose was researched at https://aardappel.github.io/goose/ . It is a new systems
language that emits C; its own benchmarks do not establish a gain for this model
or Android app.031 adds no Goose dependency. See RESEARCH.md for sources, the
comparison with the old interface and the rationale.

The Rust and MicroPython shared libraries, original base pack and exact epoch02
edit are byte-identical to0.5. General default remains unchanged; the epoch02
retention failures and Rust/Python discrepancy remain disclosed in the selector.
Specialist015E still requires its existing separate installed app.

Validation:29Chromium UI checks with a mocked Java bridge, four actual-thought
parser checks,27Java agent checks, secure local-asset origin test, real Android
resource/Java/DEX compilation, APKv3 signature/certificate, ZIP alignment/CRC and
full embedded asset/native-library hashes. Screenshots use mock UI fixtures and
are not evidence of model quality. No physical Android device/emulator execution
is claimed. The Chromium environment blocks direct file URLs; production uses an
intercepted HTTPS origin, tested separately.

Same package dev.liquidsense.chat.tools,versionCode4,Android9+/ARM64 and previous
signing certificate. Install over0.5 to preserve Android application data.
Check reports/gofile_delivery.json for the current verified public download.

Exact signed APK SHA256:
4c4d247fb0c63c3db8fef6779e27b0623f2172efe20a8efb44e1ab16a11c11a5

The old0.5 signed APK remains fully recoverable from its immutable030archive;
only its redundant RAM build cache was reused.031's exact archive reuses all
unchanged030segments and preserves a new suffix. A full reconstruction stream
was verified against the signed031SHA256. Restore with
`python android_ui031/restore.py NEW_OUTPUT.apk` in a restored project containing
its prior protected model/patch sources. No checkpoint or experiment was deleted.

Rebuild with the documented Android build tools: compile_ui.py followed by
build_apk.py (requires a verified030build cache and the private signing key).
Archive restoration does not need a signing key. Existing older public downloads
and all prior sources remain. Gofile guest credentials and signing material are
kept outside the project.
