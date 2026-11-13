# Loop025 — three-epoch supervised loop-block training

Current explicit user authorization permits gradients and direct parameter edits.
Start from GENERAL best.pt SHA25646f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8,
not018or any rejected candidate. This is a new experiment, not a repeated018run.

Hypothesis: the previous small joint scope froze16exact-zero branch exits in
inserted layers8..11and20..23, blocking60upstream selected tensors. Open these
exits and train the repeated block itself. Select the276previously eligible
middle4..27control/mHC/temporal/norm tensors plus those16dense exits:292tensors,
48,340,208values. All407other tensors, including153vision, stay hash-identical.
Both actual shared visits execute in the same forward/backward with explicit
per-visit activation-checkpoint contexts. No random weights or warmstart edits.

Three fixed epochs over8code/general pairs (16examples/epoch),24optimizer steps.
Teaching data are the8observed018code problems and8general examples, with
final-answer-only targets and native nonthinking prefixes. Unlike018, do not
teach explanatory thought traces: goal is correct final programs and completion,
not verbosity. Evaluation uses the same mode and dual endoftext/im_end stopping
for ALL models, aligned to the general app. Targets end with tokenizer im_end.
Teacher forcing includes answers only in target positions, never eval prefixes.

Adafactor, relative scale, no weight decay: controller lr.005, exit lr.03,
seed20261113. Global gradient norm is clipped to1before each update. Shuffle8pairs deterministically per epoch. Per-step displacement
relative to unchanged parent bounded separately: controllers.05L2 with RMS
floor.01; exits.01L2 with RMS floor.01. Exact-zero exits therefore have at most
1e-4RMS displacement. BF16 rounding/projected gain overshoots must be measured,
not hidden. Positive visit gains normalized to sum1. This does not force a
larger second gain or guarantee loop benefit. Check actual gradients per name,
previously blocked branches after exits open, changed counts, finite values,
all699hashes, architecture and cold restoration.

Save rolling optimizer/RNG/selected weights after EVERY step, immutable split
checkpoints after epochs1/2/3. Logs every update. A rolling recovery file is
replaceable working state; all epoch snapshots/prior studies are preserved.
Training checkpoints may reside in shm to respect disk limits, but epoch bytes
must be persisted to GitHub before final. Archive only redundant APK build
copies AFTER full reconstructed hash verification, with exact restoration.

Comparison: original Qwen, unchanged general parent, each epoch under identical
PyTorchCPU/BF16/eager/cache,greedy,seed0,4threads, nonthinking,dualEOS,160code tokens,
64general tokens. All inputs omit gold answers and hidden tests. Report2taught
code fits separately from4new validation tasks with disjoint algorithm families,
and all12observed general/language controls. Do not reuse old control scores
because the dual-EOS protocol differs; rerun matching references. Preserve raw
final output, truncation and case bits per completed row, resume missing only.

An epoch is eligible only if it has a strict complete-task validation gain over
parent, retains EVERY parent-correct validation case and general control, and
loses no taught-case bits. Among eligible epochs maximize validation tasks,
then cases, then earliest epoch. NLL is diagnostic only. No loss-based promotion.
Only the selected eligible epoch can consume4new final problems and4new general
controls, compared ONCE with original/parent. These final task families differ
from training and validation. Report family/small-sample limitations. If no epoch
passes, keep final data unused and preserve general as selected.

Causal loop-use diagnostic after selection is frozen: compare parent and the
selected epoch, or epoch3if none eligible, on2taught tasks. Replace SECOND
middle exit with saved FIRST exit while still executing all56layer calls. This
is a causal contribution ablation, not a valid cheaper single-pass model.
Record state differences and program/case changes. Mechanism activity alone
is not evidence of better programming or intelligence. No4B superiority claim.

No new APK/default promotion unless independent final gain preserves every
parent-correct final case/control and all earlier gates. Even then preserve as
research candidate; no broad intelligence conclusion from four tasks. Close all
workers and verify durable commits before final. Old sealed013/016/RSI100
questions are never opened by this experiment.
