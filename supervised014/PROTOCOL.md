# Study014 — correct benchmark programs written into an existing matrix

User request11/11/2026 explicitly authorizes correct solutions to supervise
weight edits, followed by evaluation on that benchmark AND a different one.
Both datasets must be evaluated even if the taught-set result is poor.

## Data and limits

Pinned HumanEval b9453e8f1865df0a0057a1383767caa400acfbcf, selected algorithmic
IDs32,39,75,114,119,129,132,147. All eight canonical programs may teach weights.
The same eight problems are then tested by free generation. This is IN-SAMPLE
resubstitution/memorization, not a valid independent HumanEval benchmark score.
References are archived unchanged; the teaching program strips docstrings by
AST, without altering its algorithm. All official tests remain unchanged.

Transfer: sanitized MBPP pinned file revision
f82046ba5aabbbb427dbfd38a254d26bff08b533, IDs129,239,245,247,306,392,407,463,
all in its published test-ID range11..510. This selects longer combinatorial/
dynamic-programming tasks, not a recognized official hard split. MBPP in general
is basic Python. Its references/tests never enter learning, dosing or selection.
The grader can validate reference programs before any model results.

These are8+8-problem subsets, not164/427-problem complete benchmark scores.
No identical solution AST across the subsets; algorithmic concepts can overlap.
Both are old public datasets; pretraining contamination is unknown. The model
will intentionally be contaminated for these eight taught HumanEval questions.
HumanEval upstream is now deprecated/unmaintained; its frozen tests are used
for this local experiment, not evidence of contemporary frontier competence.

Evaluation prompt is a neutral chat request for a COMPLETE Python program.
HumanEval includes its original public prefix/docstring/examples/helpers.
MBPP includes its original problem and required signature, derived as interface
metadata, with no examples of private tests or reference implementation.
Prompts are not canonical raw-completion/three-shot benchmark formats.

## One deterministic direct edit, frozen before any free evaluation

Start unchanged best.pt SHA256
46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8.
No rejected013 adapters. Preserve32physical/56executions, mHC2 and Liquid-inspired
convolutions/local windows. Edit ONLY existing
model.language_model.layers.31.mlp.down_proj.weight (1024x3584, BF16).
No new model parameters, random edits, loss gradients, backward or optimizer.

Teacher force the eight correct HumanEval programs and EOS. Capture EVERY
response decision's last-MLP input x and final pre-RMSNorm h. The last layer
is outside the shared loop and has only RMSNorm/unembedding downstream. Thus
DeltaW*x changes this final residual directly, apart from BF16 rounding; no
identity approximation through four intervening layers as in013.

For wrong-next-token positions, use eight strongest original competitors.
With a=(E_gold-E_competitor)*(1+norm.weight), a constant-norm h lies on a sphere
and the normalized logit-margin inequality becomes a linear halfspace.
Eight fixed closest-point rotations target margin.5 against these competitors.
Cap target residual displacement at15% of ||h||. Already-correct positions
target zero change. This does not guarantee gold wins against all other tokens.

Add zero-target protection on the last<=8 positions of each of12 old language
anchors. Normalize each equation by ||x||. Solve the minimum-change dual ridge
system, lambda=1e-4 times mean Gram diagonal, then cap DeltaW Frobenius norm at
20% of parent W norm. Write BF16 once; no retries, rank/dose search or inverse
control candidates. This is supervised algebraic parameter learning, not SFT/
LoRA or a lookup table/program pasted in a prompt. Actual teacher-forced NLL,
token accuracy, changed coordinates and every original tensor hash are recorded.

## Free generation, transfer and retention

Freeze exact candidate and its SHA256 before evaluation. Compare original Qwen,
immediate parent and edited Liquid under identical statements, tokenizer,
greedy/seed0, thinking off,320newtokens, BF16/eager/cache,4CPUthreads. Largest
selected reference program is221tokens; the320 budget exceeds all references.
Original has24executions; parent/edited56, so no compute-equal claim versus Qwen.

Run taught8, transfer8 and old12 language/reasoning controls for ALL3models.
No inference receives a reference implementation, private test or feedback.
Public examples/helpers already present in an official statement stay present.
Single program, no repair or reranking. Use official assertions in a credential-
free seccomp process, with fixed stdlib policy, independent trusted test context,
and single underscore allowed. Validate all16 correct references and reject
all16 None-return mutants before freezing. Security/geometry tests also pass.

Primary metric: wholly solved programs/8 in each dataset. HumanEval has one
official check group per problem; MBPP has three assertions, not comparable
counts of individual assertions. Aggregate only task pass@1 across datasets.
Report per-ID transitions, truncation, latency and paired exact/bootstrapped
uncertainty. Taught score cannot establish transfer; improvement solely there
is benchmark specialization/memorization.

Do not promote unless transfer has positive task gain, no previously correct
task/test loss, no loss of parent-correct controls, language-anchor NLL rise
<=.005, and paired one-sided task p<=.05. Even passing8task pilot cannot prove
general intelligence/4B superiority. Never retune after transfer results.
Preserve parent, direct matrix snapshots, activations, references and outputs.
The old40final/32validation and RSI100 reserved sets stay unused in014.
