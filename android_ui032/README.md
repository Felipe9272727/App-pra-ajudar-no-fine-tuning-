# Liquid Sense Android0.6.2 — keyboard, navigation and motion fixes

[Download on Gofile — 1.97GB](https://gofile.io/d/fNGVCZpE), Android9+/ARM64.
Install over the existing Liquid Sense Tools app: same package/certificate,
versionCode6. Existing conversations/models and local commands are preserved.

The user reported a phone keyboard covering the composer, new-chat taps doing
nothing, blue website-like touch feedback and insufficient animation in031.
This release directly addresses those paths:

- Android30+ uses explicit system-bar/IME insets on a native root. The WebView
  is remeasured above the keyboard, and an inset-animation callback follows its
  movement. Android28/29 retains resize plus visible-window measurement.
  The old WebView padding listener is removed. Native measured height and the
  browser visual viewport both constrain the chat; flex panels can shrink.
- New chat, context clear and model/history navigation accept requests while
  generating/loading. The current work is cancelled or awaited explicitly;
  the UI shows a visible pending transition. Only one engine job runs at once.
  Old output is archived under the old chat and never displayed in the new one.
  An in-flight HTTPS tool call may still need to return before cancellation
  completes; this is shown as pending, not an instant second inference.
- Empty new chats are now persistent/visible in history. Changing thread clears
  an old history search filter so the new active chat is not hidden. Migration
  no longer refreshes all old chat timestamps at every startup.
- Blue WebView tap highlights and edge overscroll are disabled. Keyboard focus
  outlines and text selection remain accessible. Navigation buttons use normal
  Android haptic feedback, respecting the system setting.
- Message/welcome entrances, dialog entrance/exit, drawer movement, panel opens,
  selected-chat feedback, composer focus, button presses and actual busy/loading
  states have restrained motion. Reduced-motion preferences disable it.

No additional runtime language was required: Java owns Android integration,
HTML/CSS/JavaScript owns presentation, and the Rust/MicroPython C libraries stay
byte-identical. Model weights and the real loop architecture are unchanged;
this is not new training or a quality/speed claim. Base, experimental029epoch02,
external Code015E and all four legacy profile IDs remain.031's known model
limitations still apply.

Commands: /clear (also / clear), /new, /models, /think (normal/profundo/extenso),
/stop and /help. Commands are handled by the app and consume no model tokens.
Clear creates empty active context while preserving archived conversations.

Validation:

- 51Chromium UI checks, including composer bounds at a reduced native viewport,
 visualViewport overlay fallback, viewport restoration, pending new-chat clicks,
 stale output suppression, empty-chat visibility and reduced motion.
- 8real Chromium touch-input checks using a simulated Java bridge.
- 11checks of the actual production Java ConversationBook/NavigationQueue on a
 host JVM: persistence roundtrip, no old messages in a new context, old late
 results retained, request copying, last navigation intent and one-time draining.
- 27Java tool-agent checks; real Android resources/Java/DEX compilation.
- APKv3 certificate/signature, alignment, full ZIP CRC and exact model/native/UI
 payload digests. Full signed- APK archive reconstruction hash also verified.

These checks are not physical Android/emulator execution. Keyboard screenshots
show a simulated reduced viewport without a real Android IME. The new native
WindowInsets path is compiled/reviewed; device-specific behavior is unverified.
No physical device is available in this environment.

APK SHA256:
614cdc6cfbce027947e4294ab9f0578b581d47b3615eefc72f1d88940be58590

Old0310.6.1 remains exactly recoverable at commit
c37e62b9a3f8d40bdffad33a2e5bd0edd7052878 and its existing Gofile link. Only the
redundant RAM build cache was reused after full archive verification. All prior
experiments, checkpoints and exact APK archives remain.032adds only its new
signed suffix and references unchanged older pack/patch/archive segments.
`python android_ui032/restore.py NEW_OUTPUT.apk` recreates this signed APK from
those preserved project files. Signing and guest-upload credentials are private.
