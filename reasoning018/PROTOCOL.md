# Reasoning018: bounded joint reasoning pilot, from general principal

Authorization: user explicitly approved supervised gradients. Do not repeat or
extend rejected015/016 trials. Parent is the preserved general hybrid best.pt
SHA25646f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8.

Hypothesis: teaching checked solution explanations plus executable final code,
with a thinking-enabled native prefix, can improve completion/correctness.
Restrict adaptation to329tensors/2,675,888values: Loop gains, all48mHC routers,
Liquid-inspired decay/gates/conv7 and norms. Freeze all dense content matrices,
embeddings/readout and vision. Both visits must execute in the same supervised
backward pass with visit-correct checkpoint recomputation. No dedicated
"thought weights" exist; activity/gradient/extra tokens do not prove reasoning.
This differs from016: starts from GENERAL, excludes the last dense readout,
uses explanatory targets and native thinking prefixes, small bounded updates.

Fixed eight optimizer updates, each one code and one general teaching example,
equal per-example loss. Adafactor relative lr0.0002. Per-step relative L2 trust
cap0.002 (RMS floor0.001), positive gains projected onto sum1. Report any final
post-normalization cap excess. No dose search or tuning from evaluated outputs.
Use the first variant of eight existing review013 TRAIN families and the first
eight already-taught016 general examples, each with independently checked
educational solution explanation. These are teaching data, not fresh benchmarks.
Do not read reserved013/016/RSI100 final tasks into the training process.

Training: answers only in causal teacher-forcing TARGETS; prefix contains only
the problem and open think tag. Target explanatory solution + closing think
+ correct final answer + native EOS248044. Do not use turn-end248046 as EOS.
Before changing weights, verify source hashes, all references,329-name selection,
and no-update backward coverage on both visits. Save actual gradient counts,
changed values, all699 hashes, selected raw checkpoint and optimizer state.

Evaluation: first old12 general controls with thinking=False, greedy seed0,
64new tokens, matching unchanged original/general reference conditions. Need
retain EVERY previously correct principal control (10/12), not merely total.
Then two existing code teaching probes (above_0,prefix_offset_0), same greedy
thinking=True256budget parent/candidate; teaching fits are not generalization.
If ANY general regression appears, reject promotion and leave new independent
validation unused. A failed control gate may still get a bounded diagnostic
on the two teaching probes, clearly labeled observed and not independent.
Only an eligible candidate can access new sealed validation; separately freeze
that suite before its first query. No claim of broad improvement or4B superiority
from this pilot. No new APK/default checkpoint promotion from training fit.

Long-thinking budget diagnostics are not quality evidence without a correct,
nonempty final answer. Report closing-tag completion, useful final result,
token/time counts and generation mode. Do not publish private generated
reasoning traces: keep final answer, token counts and raw-output digest.
Preserve all old files; finish with no model worker alive and durable publication.

Eligibility clarification BEFORE first training/evaluation: after control
retention, require a strict task-complete gain on the two observed teaching
probes, zero per-case/code regressions and a finished nonempty final answer.
Teacher-forced loss reduction alone does not open independent validation.
If these conditions fail, archive this pilot and keep all sealed sets unused.
The unchanged parent/original old controls are reused rather than rerun; record
exact source/protocol and per-case bits. New parent thinking-code runs are
needed because earlier nonthinking runs have a different prefix/budget.
