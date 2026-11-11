# Study 013 — supervised loop/temporal refinement (2026-11-11)

User explicitly authorized correct answers for teaching on 2026-11-11. This
supersedes old no-solutions rules ONLY for learning. No correct program, test
case, expected value, execution feedback, or demonstration is given during
free-generation evaluation. No SFT/LoRA, gradient, backward pass or optimizer.

## Recovery and immutable parent

Completed study012 commit0a70bfbd0a877c6e4793cc24742116581b0428a2 is the starting
point. Empty review-loop branch had no executed013 experiment/checkpoint.
All prior experiments remain preserved. best.pt SHA256
46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8 remains selected.
The old promising second hypothesis was reconstructed (original final weights
were not found), saved, independently evaluated, and rejected in mentor004:
development69->72/81 cases, independent85->78/192, both7/24 complete tasks.
It must not be promoted or repeated as a pending experiment.

## Data and partitions

200 parameterized problems:12 train families x10=120;4 validation families
x10=40;4 test families x10=40. Twenty independently computed cases per task.
All200 reference programs must pass the existing credential-free seccomp/AST
sandbox. Assert disjoint families and no identical solution AST across splits.
These are20 custom families, NOT200 independent algorithm families and NOT a
canonical benchmark or a guarantee against pretraining contamination. Existing
observed studies, RSI100 validation8 and heldout16 are not reused as final data.
No CCORE code/data is imported into this custom Python pilot.

## Fixed learning hypothesis

Freeze all parent tensors. Hook physical27 AFTER the second loop visit; its
first visit is unchanged by placement. Keep32physical/56executions, mHC2,
DeltaNet convolution7 and local256 active. New FP32 frozen parameters are a
rank16 review adapter, with ONLY serial request-local temporal history.

On each training solution use teacher forcing with the neutral thinking-off
template, answer tokens and EOS. Capture both loop exits. At fixed uniformly
spaced<=24 answer decisions, featureL=(h2-h1)/RMS(h2-h1); featureT is normalized
h2 minus its causal seven-tap exponentially weighted history (taps1,2,...,64
over127, zero left padding). History is equivalent in prefill and incremental
decode; clear at each new request. Two FIXED candidates:

- loop: featureL only,1024x16+16x1024=32768 learned values.
- joint: concatenate L,T,2048x16+16x1024=49152 learned values.

If the parent top token differs from the correct next token, targetY=.02 times
the RMS-normalized difference between their output embedding rows; otherwise
targetY=0. This is a LOCAL SURROGATE: it assumes an identity transport through
the remaining four layers. It is not an exact loss-minimizing update and may
fail. Fit deterministic top16 principal directions and ridge coefficient.01
times mean Gram diagonal. No dose, rank, tap or ridge search after evaluation.
Apply predictedY times RMS(h2), cap per-token update at2% RMS(h2), second visit
only. Parent weights unmodified; each candidate cold-loads parent.

Internal fit MSE, teacher-forced NLL/accuracy and state change are diagnostics,
never sufficient for promotion. Target states use only120 training programs.
Report parent/candidate teacher-forced NLL on24fixed training examples
(variants0,9 of each trainfamily), separately from free-generation scores.
Collect old12 language-anchor NLL for every model alongside controls.

## Evaluation and gates

Same tokenizer, BF16backbone/FP32adapter, CPU4threads, eager kernels, seed0,
greedy, thinking off, cache on,160newtokens, one candidate program, no repair.
Compare original Qwen, parent, loop and joint on the predeclared8-problem
screen (variants0,9 in each validation family). This screen is NEW but becomes
observed development immediately. Record every case bit, truncation, tokens,
latency, adapter update size. Original differs in depth/compute; do not call
its comparison compute-matched. Loop/joint/parent share56layerexecutions.

Require at least one newly complete task and no lost previously complete task
or case against parent, with no loss of initially correct language/reasoning
controls. Controls: four old controls plus eight new frozen simple controls.
If neither qualifies, reject both, retain parent, do not consume40finaltasks or
the remaining32validationtasks. Controls still run to measure collateral effect.
If any qualifies, evaluate full40validation under all qualified variants and
matched original/parent. Select lexicographically by complete tasks, then cases,
then fewer parameters, using only validation and controls. Candidate must retain
all previously correct validationcases and complete at least one extra task;
old12 language anchors NLL may rise at most.005. Freeze its exact hash/selection.

Only then open final40problems for original, parent, one frozen candidate.
Require positive task gain, no lost cases/controls and paired one-sided exact
task p<=.05; report paired bootstrap95%CI with family-cluster uncertainty.
With only4testfamilies strong population inference is limited even if a task
p-value passes. Promotion is a validated pilot candidate, not general intelligence
or4Bsuperiority. Final outputs can never tune a replacement candidate.

Three or more passages are deferred until a two-pass learner passes screening;
more computation alone did not improve previous study005. No adaptive skipping
with incomplete per-visit caches. DSpine is a separate speed line, not a skill
training method. End the turn with no active model processes.
