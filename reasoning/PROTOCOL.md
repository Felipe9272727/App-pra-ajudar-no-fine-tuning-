# Assistant-guided reasoning and direct-weight continuation — 2026-11-05

Start from the preserved hybrid parent, best.pt SHA256
46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8.
Hypothesis 002 failed independent validation and is never the new parent.
Its 24 observed tasks are exhausted as a final test. All historical files stay.

The user requests stronger reasoning and reinforcement of SenseNova looping,
followed by further activation-guided edits and external benchmark comparison.
There are no established dedicated "thinking weights". Activation contrast
identifies candidates; controlled interventions and execution decide whether
they help. Longer thinking text is not a quality metric.

No gradients, optimizers, conventional fine-tuning, random parameter search,
positive solution labels, correct replacement tokens or test cases in generation.
All hybrids keep 32 physical layers, Loop/mHC and active Liquid convolutions.
Four inference threads, pinned BF16/eager runtime, greedy cache generation.
Research uses the original 160-code-token budget for historical comparability.
Generated code only runs in the existing capability-cleared seccomp AST judge.

## Diagnostic and hypothesis 003 (fixed before its execution scores)

Capture actual cached generation on observed development tasks prefix_sums,
rotate_right and longest_run (errors), and sum_abs, palindrome and binary_search
(successful guards). Verify outputs against the unchanged saved parent.
Collect final MLP inputs and per-layer/per-visit MLP input drift, cosine and
top active coordinates for every loop layer. Exclude the eight neutral inserted
layers from ranking. Large activations alone do not establish causal blame.

Rank the active loop layers by error-minus-guard mean log(1+relative visit drift).
Target the top three (tie: layer index). Directly overwrite their existing
native_visit_gain FP32 parameters from [0.95,0.05] to [0.925,0.075]. The sum stays
one and both visits stay positive. Other parameters remain equal to parent.
This reinforces the contribution of the second visit without adding tokens.
Use the three bottom-ranked active layers as an equal-dose layer control.
Screen on the same six observed tasks, then restore parent. Require strict
case gain with no correct case lost. If screening fails, reject immediately.
Otherwise require full paired AND historical 16-task/4-control/NLL gates,
followed by a new, independently frozen validation before any promotion.

## Hypothesis 004 (separate, fixed negative-only intervention)

After reviewing 003, start from a validated selected checkpoint; if 003 has not
passed new validation, use the unchanged parent. Analyze the actual wrong
left-slice index in the student's rotate_right output. Suppress only the
student's own erroneous index token at that state with an existing final-MLP
rank-one write. Preserve all preceding states from that output AND all captured
states of the three successful guard tasks, using ridge residualization.
Use fixed relative Frobenius dose 0.006, not a feedback-selected dose grid.
Abort if residual activation norm is less than 5% of the original norm.
W' = BF16(W - 0.006 ||W|| normalize(unembedding[bad_token]) v.T).
No correct replacement index/sign/slice or solution is supplied to the student.
Require monotone six-task screening, then the unchanged full paired/historical
gates. Preserve the directions, exact resulting matrix and any rejection.
No automatic new hypothesis or dose is started after this finite pair.

## Independent comparison and identity

Freeze public benchmark IDs, source revisions, scoring, prompts, seeds and
budgets BEFORE any benchmark generation. Do not use their results to edit or
select weights. Compare original Qwen and selected Liquid Sense under identical
inference settings, with a parent reference if a new candidate qualifies.
Report measured subsets as subsets, not full leaderboards or vendor-equivalent
scores. Report truncation, uncertainty, limitations and every regression.

Branding is a separate, honest application configuration: Liquid Sense is an
independent project led by one developer, derived from Qwen with experimental
SenseNova/Liquid-inspired components. Do not claim the pretrained backbone was
created entirely by that developer. A system prompt/config identity is not a
weight-learned identity or a capability gain. Keep branding out of raw benchmarks.

Save and verify each outcome commit on GitHub. End with no active local worker;
never promise transient local execution continues between turns.

## Authored amendment after hypothesis 003, before public outputs

003's fixed two-visit gain shift changed no case outcomes. The continued user
request also motivates a separate hypothesis about actual added depth. Read
hypothesis_005.md: one selective third-visit intervention with a matched depth
control, from unchanged parent, not a dose grid or stacking of unvalidated 004.
The finite continuation now contains hypotheses 003/004/005. All qualifying
candidates are frozen together before the single unopened RSI100 validation.
No hypothesis is added after that validation or after public benchmarks.
