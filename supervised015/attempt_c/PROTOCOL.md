# Study015 C — bounded critical-token supervised refinement

B is COMPLETE training: all546 text tensors changed, exact stream hash
c2f851b064b9656e356fe2c37985df88d598bf2fd358903d1a06fcf53b659ca7.
Its8 taught-task generations scored6/8, versus original/immutable principal1/8.
B fails32(find_zero: while True repetition) and129(minPath: wrong neighbors).
B's final teacher-forced diagnostics contain9 wrong tokens, concentrated in
those tasks plus one in39. B is preserved in full regardless of this refinement.

Hypothesis: averaging long program losses and minibatch interference dilute
individual branch decisions. Supervise the first wrong canonical token of
failed tasks, then the next weakest canonical decisions, with all546 text
parameters still trainable. This teaches the SAME eight deliberately observed
solutions; it is benchmark specialization, not independent validation or a
causal identification of uniquely faulty/thought weights. Correct prefixes
are provided ONLY in training. Final generation gets only problem statements.

Before each step, measure all8 canonical programs with teacher forcing. For
each task choose its FIRST incorrect argmax token, otherwise its minimum-margin
token. Prioritize currently incorrect32/129, then other incorrect tasks, then
lowest margins; select2 distinct tasks. Truncate each training input immediately
before its selected gold token; one-token CE is averaged over the pair. This
concentrates supervision on branch decisions and also records differences
between full-program diagnostic and truncated-prefix logits. No private tests
or MBPP/control responses enter gradients/mining. No randomness in weight edits.

Start from exact saved B, not original or rejected014. Reuse B Adafactor factor
states, override relative lr to.0005, no weight decay, same BF16/FP32 and native
optimizer-in-backward/checkpointed per-visit computation. Keep every architecture
component/positive normalized visit gain,153vision tensors frozen. Maximum6
updates, stop if all1098gold/EOS tokens are argmax-correct and worst margin>=1.
A fixed bounded refinement is not a mathematical global optimum.

Save exact lossless XORs against B, preserving B's full original-parent chain,
optimizer/RNG, every mining decision and learning curve. Cold-restore B then C
and verify all546target hashes; audit all699finite and vision unchanged.
Cumulative change counts also compare C with the immutable principal. Never
replace or remove B or principal. No full master FP32 copy/new adapters.

Final C evaluation: SAME8HumanEval taught targets,320token greedy/seed0/
thinking-off/cache/eager/BF16/4thread settings and original014judge/tests;
SAME8MBPP and12controls/NLL language as diagnostics. MBPP is already observed
in014 AND B; no independent/unseen claim and no refitting from its outcomes.
Reuse immutable original/principal/B outputs. Preserve C as best experimental
benchmark specialist only if it gains complete target tasks and loses no B
correct target. Otherwise retain B as benchmark specialist. Principal stays
unchanged regardless of in-sample fit. Report all regressions and both snapshots.
No worker persists after the turn ends. C starts only after B evaluation exits.
