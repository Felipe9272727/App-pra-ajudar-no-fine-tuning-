# Hypothesis008 — coordinated multi-tensor activation calibration

New user request: change multiple weights to seek broader competence. Start
from preserved hybrid best.pt SHA256
46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8.
006/007 and all older experiments remain complete and are not replayed.
This is one new authored hypothesis, with one inverse-sign control, no dose grid.
The earlier1.86M-scalar edit was confined to one matrix. Here the intervention
is distributed across computational stages, not chosen by number of scalars.

## Rationale and data, before new measurements

Loop/Liquid changes alter the distributions seen by copied pretrained weights.
A source-compatible diagonal gain correction may reduce that mismatch while
keeping both architectural operator families active. Smaller distribution
distance is a mechanism diagnostic, never proof of intelligence or task quality.
No dedicated thinking module is assumed and repetition may remain unfixed.

Collect output second moments of input_layernorm and post_attention_layernorm
in all24 non-neutral physical layers (48 existing1024-element tensors).
Exclude inserted identity layers8–11 and20–23. Match original donor layers
using SOURCE_LAYERS. Original and parent receive byte-identical *unlabelled*
inputs:12 newly authored ordinary texts and the seven existing coding prompts
prefix_sums,rotate_right,longest_run,overlap_count,sum_abs,palindrome,binary_search.
Forward use_cache=False only, no generated/correct/reference program supplied.
Aggregate moments per episode first, then average episodes equally.
In the hybrid, combine loop visits with their existing .95/.05 contribution
weights; unlooped layers have weight1. Record visit statistics separately.

Separately capture new actual cached-decoding moments on the seven parent
coding tasks at160 tokens, and verify generated text against the completed
parent reference. This is new internal instrumentation missing from prior
traces, not a new task score or replay of an old parameter edit. These decoding
moments diagnose errors/guards; they do not introduce an answer target.
The original does not generate reference solutions for fitting.

## Fixed simultaneous construction

For every eligible norm, let m_ref/m_parent be per-channel second moments.
z = .25*.5*[log(m_ref+1e-6)-log(m_parent+1e-6)].
Subtract z's channel mean, then clip z to[-.02,+.02].
Qwen uses effective gain g=1+w, so write w'=BF16(g*exp(z)-1).
This is a damped diagonal moment correction to existing weights, not a gradient
update, optimizer, conventional fine-tuning or a target-token fit.
Apply all48 proposed vectors together. Do not force changes in unchanged
coordinates. Preserve gain signs/zeros; revert any quantized coordinate whose
actual relative gain change exceeds3%. Record every actual tensor/value change.
Inverse control uses -z at the same locations, never selectable as the winner.
Restore ALL saved norm vectors as well as the parent overlay between variants.
The old parent loader alone does not reset these new parameter families.

Keep32 physical layers, two loop visits/56 executions, mHC and active Liquid
convolutions/windows. Four threads, BF16/eager with existing FP32 router params,
greedy cache generation, seed0, thinkingFalse. No branding in quality inputs.
Save original weights, moment checkpoints, both exact overlays and hashes.

## Gates

Measure actual post-edit moments on the same inputs for the inverse control
and target, but never accept by this distance. Screen inverse first, then
target on the seven coding tasks (36 cases; parent27 correct). Require at
least one extra correct case and no previously correct case lost. If target
fails, reject; do not choose the inverse or start a new dose.

If it passes, run all16 development tasks, four general controls and the12
existing language anchors. These anchors are OUT of calibration. Require
strict monotone case gain, no lost controls, and anchor NLL no worse than
paired AND historical parent+1e-6. The paired parent must restore all norms;
it must reproduce saved case bits. Compare original using the completed
identical-protocol development baseline (12 tasks,66/81 cases,4/4 controls).

Only after passing development, freeze exact candidate hashes and validation
source on GitHub before running the still-unobserved RSI100 eight-task
validation plus its general controls, original/parent/candidate under matched
160-code/32-control budgets. Require at least one more complete task, strict
case gain, no case/control losses and no worse NLL versus parent. Otherwise
retain the parent. This validates a limited suite, not general intelligence.
No more weight selection after observing that validation.

The old24-task validation004, public36-task pilot, and3-task thought-budget
diagnostic are observed; never relabel them as a fresh final. New008 is not
a promotion of006/007. Finish all workers and verify outcome commits on GitHub
before ending the turn. Do not promise persistent background research.
