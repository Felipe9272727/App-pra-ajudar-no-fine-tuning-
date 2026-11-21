# Speed041 — exact faster prefill, Android 0.6.5 and identity

- Rust prefill shares BF16 weight reads over four tokens, preserves scalar accumulation order and advances all 56 cache slots causally inside each block. Rotary reuse, recurrent passes and attention value-order changes preserve bits in the tested states. Exact old Base asset and Loop029 epoch02 patch hashes. Same reasoning/context budgets, signer and package. Trained checkpoint stays separately selectable offline.
- ARM64 Neoverse-N2 run 44949897584 medians first token Base 1.613 to 1.030 s, epoch02 1.702 to 1.120 s for the same 20-token prompt and four measured repetitions per path. Decode of 8 tokens was within 2% on ARM. Full state/logit comparison passed in ARM64 and x86-64. ARM run 44951555200 verified the same output and 37 reused prefix tokens through Normal then thinking. Snapdragon timing remains to be measured.
- GPU direct identity comes from app and web metadata, with Qwen3.5 lineage and independent developer credit. Space revision 010c41866c12ead6f640d0d8b44f0f4544593298 verified anonymously. Ordinary inference files were hash verified. Temporary deployment token removed.
- Signed compact updater 0.5 for installed 0.6.4, 6320677 bytes SHA256 d01364aa1ad50940c2c9c177a4d1f9e0aa1a512be2b959427d6a09cdb4f181e3. Android 15 run 44951406641 passed real install, history, GPU identity and bounded JNI generation of 13 tokens. First full UI sample timed out in the emulator and is preserved. Anonymous public download verified. https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/releases/download/liquid-sense-0.6.5-speed041/LiquidSense-Atualizador-0.5.apk
- Source and reports https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/tree/713a11045fc8aafd885f46e1a48581554e305de4/speed041

# Online040 — Android 0.6.4 with direct Hugging Face GPU

- User asked to match the app's token budgets and connect the Android app directly to the Hugging Face Space. Space revision 8d881d4c1dfb8a377ff6f814f23a5b85059f11ec runs in ZeroGPU. Context is 16384; Normal 0+2048, Profundo 1024+2048, Extenso 2048+4096. Live two-stage test produced 600 reasoning tokens; exact 6144 ceiling checked in a fixture. Final browser and API calls returned a real authenticated CUDA response. Anonymous service quotas can stop the turn.
- Android versionCode 8, same package/certificate, same local weights/libraries, direct HTTPS GPU Base selector with separate history. Optional personal read credential is encrypted on device. No credential in artifacts. Temporary deployment credential removed. GPU mode generates text; web and Python stay in the compatible local modes.
- Compact updater 0.4 reuses exact installed 0.6.3 assets; 6300204 bytes SHA256 ab626884c1e7c49bdd44001f78c37317167afedc45a259602672af72fd49e24b. Normal Android confirmation. Android 15 CI 44920642172 verified STATUS_SUCCESS, history preservation, model selection and provider quota feedback. Physical Xiaomi installation still pending. Anonymous download verified twice. https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/releases/download/liquid-sense-0.6.4-gpu040/LiquidSense-Atualizador-GPU-0.4.apk
- Implementation and all results https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/tree/39ff93e9289d971246fc9402949830eea1827fea/online040. First CI history fixture path issue and second CI zero-quota rejection preserved. Keep prior release/checkpoint history. No training or checkpoint promotion.

# Online039 — public Liquid Sense ZeroGPU Space tested in CUDA

- Space https://huggingface.co/spaces/Felipe0282829273/liquid-sense-gpu, revision
  e3bcf6c23a400a5ce4940eb85b938cc483fd0514. Tested public HTTP 200 and CUDA /generate.
- Shipped BF16 pack SHA6c774a43…7288, 546 tensors, 32 layers and 56 visits. Only
  zero-weight mHC routers use precomputed gates (48). CPU and GPU test tokens
  matched. Same 64-token code prompt, two calls per GPU revision: 22.6s→5.3s
  mean request time. Short requests vary with queue. At budget160 the function
  finished at88 tokens and passed3/3. Quality and latency versus Android Rust
  still need testing before Android integration. No model training occurred.
- 33 source/report files verified at c3aca8e1b253217fd4b7172c7a4b380f8d02d371 under online039. The temporary
  credential was removed after checking the public Space. Never persist it.

# Hosting038 — installation confirmed by user; free GPU research before training

- User explicitly confirms helper0.3fixed final installation on Xiaomi. Record
  phone installation as USER-REPORTED success, not pending. No automatic phone
  speed/quality/keyboard claim.037status updated in038branch; past CI preserved.
- User wants more improvements but asks FIRST about free/faster hosting. Research
  completed, no new training, checkpoint promotion, app update or deployment.
  Read hosting038/REPORT.md,status.json on
  codex/liquid-sense-hosting-038-20261116 atf15b503eb3bb9b3b47ef2cf27c7dfa6e9d7cbe77.
- Official docs checked2026-11-16: HFZeroGPU permits2free personalGradioSpaces
  for accounts in good standing, verifiedemail, age>30days; free5minGPU/day,
  shared queues. Do not reuse obsolete PRO-only claim or assume CPUBasicnew
  computeSpaces require no paid plan. ModalStarter$30monthlycompute credits,
  payment method required; spending/usage limit needed to stay within credits.
  Colabfree is for interactive notebooks, not continuous appweb backend.
- Current custom Rust runtimeCPU does not automatically use a hostedGPU. Need
  compatible GPU execution and same checkpoint+loop/controllers. Existing030
  Python/Rust generation divergence means parity/quality must be tested. Measure
  TTFT,tokens/s,total(coldstart,queue,network) before speed claims. Suggested
  next step: isolatedZeroGPU demo if accounteligible, optionalLocal/Online later.
  No account credentials provided/requested; no paid resources or endpoint used.

# AndroidSession037 COMPLETE — fix our double close; final phone install pending

- Phone036repair succeeded:32/235blocks,256MiB; full ZIP and APK CRC/SHA+reread
  passed. Preserve verified.apk in helper cache and valid036; no new repair.
- Our036Session code closed FileBridge output explicitly AND automatically,
  then catch abandoned after commit. AOSP close is not idempotent; reproduced
  actual EBADF in Android15 with full exact APK.037nests stream scope so it
  closes ONCE before commit, reads staged base.apk size+SHA, never abandons
  after a commit attempt and correlates callbacks with its own session ID.
- Delivered helper0.3/code3,37340bytes,SHA256
  084e6b13a28df286c8f9b2cd68c3a541d4dfc31e70a132ad949c5a21d5a430ac:
  https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/releases/download/liquid-sense-session037/LiquidSense-Reparador-0.3.apk
- Read android_install037 on codex/liquid-sense-session-037-20261116.
  48files verified at9a324b008124768c0dcd758fc2d35948103a6cef. CI43798804632/job133073727510:
  old036EBADF reproduced;037update kept cached APK+helper marker; staged
  1967560403bytes and SHA4735be85...ade0e10verified; NORMAL installer UI clicked;
  final STATUS_SUCCESS0, Tools version7installed, actual chat UI opened.
  Public tiny APK download verified. Two initial test-precondition failures
  (prewarmed Activity, instrumented unknown-source permission) preserved.
- User updates helper IN PLACE, no uninstall/clear data. Open and go DIRECTLY
  to button3; do not reselect ZIP or repeat button2. Confirm Android installer.
  Button4copies new037result if failure. Existing report may include old errors;
  inspect newest037session. Main app/weights unchanged. Cached APK already good.
- Pending actual final Xiaomi installation. Physical block repair IS confirmed;
  do not call it pending. No model-quality/speed, keyboard or live neural tests
  claimed from installation/launch. All CI runs closed. Older releases retained.

# AndroidIntegrity036 — repeated phone ZIP mismatch; block repair helper ready

- User DID download our link. ZIP035phone bytes1967561424match; SHA
  b7b6e7c797b9a48741ec98bc2784ec833caebf6a12d068ffc39d58909de7ef79
  differs from published52966dccfc9ec1dd6f4eaeabadaa3615c31e286034d84c04a74690042724f307.
  ZArchiver: CRCinvalid. New independent download+nativeunzip+Java CRC passed.
  Origin of alteration unknown: no blame of user/extractor/network/storage.
- Compared UI031→032→033: same~1.97GB, weights, Rust/Python, package/cert.
  Old UI opened on phone; exact0.6.0vs0.6.1unknown. First explicit failed0.6.2,
  0.6.3fresh packaging,035outerZIP. No inference/model regression established.
- New SAMEPACKAGE helper update0.2/version2,33244bytes, SHA256
  4f2a774b6b1a4b3a13cbcbdc84014dcc1a49ce9be165e1c9a34c69cef13f85b7:
  https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/releases/download/liquid-sense-integrity036/LiquidSense-Reparador-0.2.apk
- Read android_delivery036 on codex/liquid-sense-integrity-036-20261116,
  44files verified at24eae908bb61c0cedeeefe7ec2a1c0ae9b7c5a46. Android15run43796079215/job133065078317
  PASSED helper update, production scan, actual HTTPS8MiBblock repair,
  full ZIP SHA, extraction CRC/APK SHA, reread and Android parser.
  Public tiny APK download verified.13local core/JavaZIPtests andunzip passed.
  First CI-only testresource alignment failure preserved. LocalJava HTTPS
  probe refused direct connection; actual Android HTTPS test passed instead.
- User updates helper, selects EXISTINGZIP, waits. Shows original-read and
  cache-reread hashes and requiredMiB. Button2repairs only differing blocks in
  private copy; if all differ, may need nearly2GB, amount shown before download.
  Button3normal Android install; button4report. No uninstall/chats access/upload.
  INTERNET added for pinned public HTTPS ranges only. OriginalZIP preserved.
- Pending user's physical block/repair/install result and origin of alteredbytes.
  File-picker taps, final main-app Session install and Xiaomi repair untested.
  Do not claim these from emulator scan/repair. No model changes/full rebuild.

# AndroidDelivery035 — physical APK hash mismatch; delivery recovery

- Phone report: Xiaomi Android15/SDK35, 1967560403bytes, SHA256
  8303e126b3af7d3f4cc95f218729a7cbb0e7193acb508745754122866f535203.
  Expected signed0.6.3 hash is4735be85...ade0e10. Same size but different bytes;
  parser returned null. Helper blocked session as intended. Actual source of
  alteration remains unknown. Missing queried package is NOT evidence of data
  deletion. No uninstall/data wipe.
- Recover exact immutable0.6.3 from preserved archive, wrap in ZIP with CRC+SHA,
  host separately on GitHub Releases; no version bump, signing or weight changes.
  Source branch codex/liquid-sense-delivery-035-20261115. Read its
  android_delivery035/README.md,status.json,reports and release delivery manifest.
- Original Gofile receipt checked MD5/size, NOT full download. Current content
  API refused premium/rate-limited; stop retries, no bypass. Do not blame host,
  phone or network without direct evidence.
- Both draft and anonymous public FULL redownload passed, including ZIP and
  contained APK SHA256, run43750305576/job132922568159. Evidence at 9e8871b5f4c7bdac9442c8e054001560dd52ce73.
  https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/releases/tag/liquid-sense-0.6.3-verified035
  User must download ZIP anew, extract, then install/select extracted APK in
  helper034. Physical installation still pending. No uninstall/data wipe.

# AndroidInstall034 — physical 0.6.3 also rejected; tiny diagnostic ready

- Phone screenshots confirm 0.6.3 was rejected too. Root cause remains unknown:
  Android15 emulator installed both0.6.2and0.6.3. Do not claim a phone fix or
  rebuild/download another2GB APK without actual device error evidence.
- Delivered separate native helper (20890bytes) https://gofile.io/d/IqxirO9A,
  package dev.liquidsense.installcheck, SHA256
  3181345443e30e0663fdd54ce42109327a8c12f8c5d654a4055f11513f06fa41.
  Exact APK, source, reports and screenshot preserved on branch
  codex/liquid-sense-device-diag-034-20261115 at 9f3566bbae9941094960928b9fbd17bdd61c170a.
- Read android_install034/README.md,status.json and reports from that branch.
  Helper installed/launched on actual Android15 emulator run43749143251,
  job132918977825. File selection/hash/session flow was NOT executed there.
- User must select existing downloaded0.6.3 in helper, wait for full hash,
  use normal Android-confirmed PackageInstaller Session if integrity passes,
  then copy report here. Captures bytes/SHA, installed/archive cert+version,
  actual STATUS/LEGACY_STATUS/message. No INTERNET permission or chat access.
  Never uninstall app/erase conversations; no automatic report upload.
- Pending: receive user's physical report, diagnose actual refusal, then make
  targeted correction. No weights/training/loop/model-quality changes.

# AndroidInstall033 COMPLETE — full APK installed/updated/launched on actual Android emulator

- User physical phone rejected0.6.2with generic invalid-package message.0.6.3fresh ZIP/v1v2v3/samecert/versionCode7delivered https://gofile.io/d/ttGQz5Os (1967560403bytes), SHA4735be854079941188e5f918e82d7c21d5468a437efe1bf7f45e72c15ade0e10. All weights/Rust/C and UI032fixes/commands retained, no training.
- Branch codex/liquid-sense-install-033-20261115;73artifacts verified at immutable04990ad71bbc9a03829e6b31759a2297692aab3e. Read android_install033/README.md,REPORT.md,status.json,CI_attempts and reports/Android15. Old signed APKs remain byte-recoverable.
- Real Android15/API35GoogleAPIsx86_64emulator supportsARM64via libndk_translation. Run43676111054success atcommitac6f3d050cbe38c9e436a4adc9dc707570051ae7. EXACT old0.6.2AND new0.6.3both installed. New update preserved test private-file marker; activity start ok,process alive20s,actual rendered chat screenshot captured. Do not conflate marker preservation with directly testing every existing conversation.
- Phone-specific refusal NOT reproduced; precise Xiaomi/HyperOS/download cause unconfirmed. No physical-device test, keyboard interaction, new model quality or speed result. Screenshot/install/launch are real emulator evidence, not mocked bridge.
- Future APK builds must use fresh logical ZIP entries, not append to an already signed APK. Old append builds contained superseded records/signing blocks. Permit only normal zero signer alignment padding. Verifyv1/v2/v3using exercising SDK ranges; default verifier may skip older schemes and show false without proving absence.
- Reconstruct with portable_restore.py using pinned upstream SHA and verified tooluse022/archive_parts hydration. No Torch/model rebuilding/signing key required for restoring signed bytes. CI explicitly creates AVD descriptor and preflights fragments before emulator startup; failed harness attempts/logs retained. All CI/model workers closed, private signing/upload secrets remain outside repo.

# AndroidUI032 COMPLETE — APK0.6.2 fixes delivered

- User reported keyboard covering composer, unresponsive new chats, blue tap highlight and wanted more motion. Same Tools package/cert, versionCode6, public APK https://gofile.io/d/fNGVCZpE (1969473053bytes). SHA256614cdc6cfbce027947e4294ab9f0578b581d47b3615eefc72f1d88940be58590.
- Branch codex/liquid-sense-ui-fixes-032-20261115;55files verified at immutable6f1e404952a1a2bc1011f3df951455306c3f7b93. Read android_ui032/README.md,status.json,reports,archive and remote verification.0310.6.1 remains preserved atc37e62b9a3f8d40bdffad33a2e5bd0edd7052878 and prior GofileQydCwORM; no old experiment/checkpoint/archive deleted.
- KeyboardLayout explicitly measures native system/IME insets on API30+ and legacy resize/visible frame on28/29. JS also handles native/visual viewport and shrinking flex. Physical Android/emulator execution NOT performed; do not turn browser simulation into a claim of confirmed phone behavior.
- New chat/clear/model/history navigation is queued instead of silently ignored during work; cancel current generation, suppress stale UI and archive old results before draining once. An actual in-flight HTTPS tool call may take time to return. Empty chats are now persistent/visible and history filter clears on changing thread.
- Tap flash/overscroll disabled; motion added with reduced-motion support.51UIchecks,8Chromium-touch simulations,11production Java persistence/queue checks,27Java agent checks and actual Android build/signature/CRC/alignment pass. Bridge simulations are labelled. Local /clear,/new,/models,/think,/stop,/help preserved; clear empties active context and keeps old chat archive.
- Same Rust/C libraries, base/epoch02weights and32physical/56executed hybrid architecture. No new training/general quality promotion. Keep stable best.pt46f6697. The known epoch02Rust/Python mismatch and retention regression remain; UI polish is not a neural gain. No model worker active; signing/upload secrets stay outside repo.

# Android030 COMPLETE — optional epoch02 APK0.5 delivered

- Signed Tools package dev.liquidsense.chat.tools, versionCode3, same previous certificate. Public APK: https://gofile.io/d/7OFCC99z (1969325396bytes). Stable/default general unchanged; experimental029epoch02 bundled as a separate Web/Python selector/history. Specialist015E remains optional via its installed app.
- Source/artifacts branch codex/liquid-sense-app-epochs-030-20261114; verified immutable commit3a73e4795bdbdcd9a14479336416aa04d75d6fd5,170files match Git blob SHA1 and sizes. Read android_epochs030/README.md,status.json, reports and exact APK/patch archives there. No training or general promotion.
- Exact546text hashes/381changed tensors; decoded edit1000020000bytes. Native loop32physical/56executed,mHC2,temporal7,local256 retained.18Rust tests/27Java checks, Android compilation/signature/alignment/CRC and native loading passed. No physical device run or speed gain claimed.
- IMPORTANT: native Rust is not generation-equivalent to Python for this candidate. Already observed chunks probe:Rust1/5cases,Python5/5;19x7candidate133matches,parent123retained. UI warns; don't advertise029Python gains as measured Android gains. Research029 retention still FAILED; keep general best.pt46f6697.
- Exact signed APK SHA2569a1a487230f7979f441002cc885501f5eb79d1f859e12474cb6b14c93b239cac.85patch fragments plus APK prefix/bridge/suffix retained; full reconstruction stream hash verified. All prior sources/checkpoints/archives preserved. Gofile guest/signing secrets remain private. No ongoing model worker.

# Latest research — Native029 four epochs COMPLETE, no candidate promoted

- User asked “Treine o melhor+4 épocas”. Latest results branch is
  codex/liquid-sense-main-four-epochs-029-20261114, immutable commit
  f07a48295b01a5e2d8517301605f85e36c1c02af. Main contains this index; use explicit ref for
  [native029/report](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/blob/f07a48295b01a5e2d8517301605f85e36c1c02af/native029/REPORT.md),
  [summary](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/blob/f07a48295b01a5e2d8517301605f85e36c1c02af/native029/summary.json),
  [status](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/blob/f07a48295b01a5e2d8517301605f85e36c1c02af/native029/status.json) and
  [integrity](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/blob/f07a48295b01a5e2d8517301605f85e36c1c02af/native029/remote_verification.json).
- Four new epochs/fresh optimizer from the selected GENERAL46f6697, not rejected
  028SFT/PPO:192unique updates,10796label-token presentations, both real visits,
  rank8on150projections+276native controls. Lower LR/stronger parentKLwere fixed
  before learning; results do not isolate epoch count alone.
- Fresh coding withoutthinking: parent0/4,2/20cases; epochs1..4respectively
  0/4,5/20;1/4,10/20;0/4,7/20;0/4,5/20. Epoch02solves chunks, but loses3known
  code cases+2general controls. No epoch passed new+legacy per-item retention.
  Trained thinking closes8/8answers but0/4correct code tasks. Budgets128/192are
  short and originals truncate; no general/4B/deeper-reasoning/speed claim.
- Stable general best.pt remains46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8.
  No APK/default changed. Five archives/178artifacts verified. All workers
  CLOSED. No background training. Final028/029still unqueried. Preserve every
  snapshot and negative result; restore via native029/restore.py at exact ref.
  Do not rerun029or present its observed validation as fresh. Gradients remain
  authorized, and correct answers stay out of evaluation prompts.

# Latest MAIN research — Native028 complete/rejected,2026-11-14

- User focus is the MAIN Liquid Sense, not speculative children. Latest research
  branch `codex/liquid-sense-productive-thinking-028-20261114`; immutable result
  commit `5bf2ef89c7092984267ee9da96f7617b5ea3f5d1`. Files native028/ and research027/ are in that branch,
  not necessarily main. Read the [report](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/blob/5bf2ef89c7092984267ee9da96f7617b5ea3f5d1/native028/REPORT.md),
  [summary](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/blob/5bf2ef89c7092984267ee9da96f7617b5ea3f5d1/native028/summary.json),
  [state](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/blob/5bf2ef89c7092984267ee9da96f7617b5ea3f5d1/native028/status.json) and
  [integrity](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/blob/5bf2ef89c7092984267ee9da96f7617b5ea3f5d1/native028/remote_verification.json) with an explicit ref.
- Gradients/supervised teaching are authorized. Keep solutions out of evaluation
  prompts, preserve the native Loop+mHC+Liquid-inspired temporal architecture,
  and never delete past experiments or promote a regressed checkpoint.
- Exactly96SFT+8PPOupdates, both loop visits and mHC/temporal controls together.
  New4code families: original1/4nonthinking; parent/SFT/PPO0/4in both modes.
  Nonthinking cases original6/20,parent7/20,SFT2/20,PPO6/20. Trained versions
  finish8/8thinking outputs within192tokens but lose prior-correct cases and
  two general controls. No candidate eligible; fresh final remains unqueried.
- Keep general best.pt SHA25646f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8.
  No model/APK/default changed. All5archives/255artifacts verified, all workers
  closed, temporary build tools/cache restored. Do not rerun completed028or
  present its observed validation as fresh. A next hypothesis is documented,
  not running. No deep-reasoning, useful-loop,4B or lossless-speed claim.

