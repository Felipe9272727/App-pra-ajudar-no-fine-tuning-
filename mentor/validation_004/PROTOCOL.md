# Frozen independent validation of reconstructed mentor hypothesis 002

Freeze this protocol, task/oracle hashes and the candidate checkpoint BEFORE
any output on this set. This is one evaluation, with no dose adjustment, prompt
repair, retries with error feedback, or new selection from its observed tasks.
Existing reserved data remain closed. The new dataset is project-unseen; we
cannot establish absence from upstream pretraining. The assistant authored
these tasks after seeing the hypothesis, so this is not a blinded external audit.

Variants: original pinned Qwen3.5-0.8B; immediate parent `best.pt` SHA256
46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8;
reconstructed hypothesis 002 SHA256
8fd291019b20f7d327e775c05a30f5b991395718040e4ad2fe52ed986ff748ef.
The recovered file is not claimed bit-identical to the unsaved old candidate.
Loop/mHC/Liquid stay active for both hybrids. Original is the canonical
unmodified model, without hybrid expansion, to provide the requested baseline.

Identical tokenizer, user prompt, context, BF16, eager kernels, greedy decoding,
thinking off, seed 0, use_cache=True, max_new_tokens=160 for code and 32 for
controls; four CPU threads and no model-side tools. No code samples, expected
values, test cases or reference functions enter generation. Only `prompt` or
`question` strings are passed. Hidden cases use the existing isolated seccomp
AST judge; do not repair generated code or alter the judge to improve scores.
Each completed output/result is checkpointed. An infrastructure error halts;
it must not be counted as a model failure. A 160-token truncation is a failure
under the locked budget and is reported explicitly for all models.

24 programming tasks, 8 cases each: 20 far-transfer and 4 prelabelled
near-transfer tasks related to overlapping windows. Primary unit is a complete
task, not 192 independent cases. Report far and near results separately.
12 controls span language, reasoning, knowledge and instruction following.
Eight new natural-language anchors measure NLL on their last eight tokens;
these are ordinary prose, not answer keys. NLL is a secondary diagnostic,
not evidence of better generated language. Existing development anchors and
4/4 controls retain their original strict gates before eligibility.

Repeat tasks 0, 6, 16 and 20 with unchanged settings in each variant. Greedy
repeats must have identical text and case bits, or halt with instability.
These repeats check numerical/execution stability; they are not additional
independent samples. Use one exact two-sided paired McNemar/sign test on
complete-task discordances and a fixed-seed task bootstrap (10,000 draws) for
the difference in pass@1. Report uncertainty and descriptive per-case wins
and losses without treating within-task cases as independent evidence.

Promotion rule, fixed before observing validation: all existing paired AND
historical development gates must pass; no previously correct validation
case or control may be lost versus the immediate parent; full-task accuracy
must improve on far-transfer tasks (not only near-transfer); aggregate paired
task p <= 0.05; new anchor mean NLL may not increase beyond 1e-6. Comparison
with original is always reported but does not excuse regression versus parent.
If a gate fails or evidence is underpowered, keep the old best checkpoint and
archive the candidate as an unpromoted experiment. Do not declare universal
preservation or increased general intelligence from this small custom suite.

No further weight hypothesis may be selected with this validation as a new
final test. Further research needs a different, still-unobserved test set.
All old checkpoints, trial reports and branches remain intact.
