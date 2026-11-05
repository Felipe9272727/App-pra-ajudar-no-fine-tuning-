# Loop usefulness, language comparison and one protected temporal-gate edit

Start from unchanged selected best.pt hash
46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8.
011 complete; reuse its actual recorded activations and tokens rather than
repeat the 699-parameter scan. No restart RSI100, no gradient/optimizer,
random parameter perturbation, correct solution/target token in model input.

Measure parent first/second loop outputs from the 21 saved decision snapshots:
relative L2 drift, cosine, and per-layer/visit changes. Real nonzero state
difference is only a mechanism check. Counterfactual diagnostic replaces layer27
second-visit output by its first-visit output; all 56 computations, virtual
caches, gains and Liquid/mHC operators stay executed. It is NOT a promotable
single-pass model or the Qwen original. Generate the same five errors and two
correct guards as011; compare exact text, complete tasks and case bits to parent.

At each of the seven old suspected/guard decision positions, capture actual
HF-generate kwargs and a deep copy of its prior cache BEFORE that forward.
Cold replay of the same cached call must reproduce raw logits (tolerance1e-6)
and top token; compare second-output bypass against this SAME cached baseline.
Record next-token probability/logit/argmax changes, not code correctness gains.
This explicitly avoids011's full-prefill-versus-cache confound. Save only
replay IDs/configuration and measured tensors; caches are transient objects.

Language: six new prompts in style_inputs.json, identical literal inputs and
128-token greedy thinking-off budgets, no branding/system identity. Original
Qwen vs preserved parent; candidate only if it passes development. Structural
constraints (sentence/bullet count, valid JSON, mandatory text facts) are checked
in Python; sentence splitting is a heuristic. Also read ALL paired outputs
for correctness, clarity, unsupported additions and repetition. Style difference
alone is not a benefit or general intelligence. Never use these prompts or
outputs to construct the edit, tune dose or choose which weights to target.

New weight hypothesis: specialize shared DeltaNet in_proj_a projections at
physical layers6 and25 for second-pass inputs, where011 observed largest
in-loop activation contrasts. Layer28 is outside the loop and excluded BEFORE
construction. This is distinct from prior norm/down-proj/loop-gain edits.
Target only overlap_count and longest_run, where the previously measured
original solved more cases. Original teacher receives only the same student
prefix already emitted in011, forced through HF cache preparation; it generates
no reference program/solution or correct target token for the student.
Collect only its internal a projection at the recorded decision. Parent targets
and all error/guard snapshots come from011 actual cached generation.

Protect both visits at all three snapshots of all non-target tasks, first
visits of target tasks, and their non-target second-visit snapshots. Protect
last-token a-input vectors of both visits on the 12 already-used ordinary texts
from reasoning/multi008/inputs.json. No new style prompt is a training input.
Projection uses SVD relative cutoff1e-5. Residualize target second-visit inputs
against protected vectors; abort any layer with residual ratio<.05.
D=teacher_a-parent_second_a, component clip +/- .125 and per-target relative
L2 cap5% of parent a. Solve rank<=2 closed-form ridge update in residual input
space, ridge=.01*mean(diag(RR.T)); Frobenius update cap .02*||W||.
Quantize once to BF16; actual norm must <=.025*||W||. Protected change relative
L2 must <=.01 (denominator floor .1) and absolute output RMS change<=.01.
Abort on nonfinite/shape/guard failure; do not tune thresholds after results.
Save exact target and equal-dose opposite-direction control matrices, hashes,
construction states and stability diagnostics. Control is not eligible to promote.
First-visit protection is sampled, not a global guarantee; general tests decide.

Quality: five error tasks + sum_abs,binary_search (35 cases, parent23/35,2/7).
Target and inverse use cold parent plus exact two-matrix overlays. Screen
requires a strict complete-task gain AND no lost parent case. If qualifying,
require full16 tasks,4 controls,12 anchor NLL against paired+historical parent:
strict complete-task gain, no case/control loss, NLL<=parent+1e-6, and language
retention. Freeze exact eligible candidate before unused RSI100 validation8;
same independent gains/retention required for promotion. No unvalidated edit
becomes parent. If screen fails, preserve parent and keep validation unused.
No additional dose search or follow-on hypothesis in this finite study.
