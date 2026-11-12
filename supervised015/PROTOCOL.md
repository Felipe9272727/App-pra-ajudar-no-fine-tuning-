# Study015 — authorized full-text supervised specialization

Client date11/11/2026; UTC execution branch identifier20261112. User explicitly
selected "Usar treino supervisionado com gradientes" after the prior restriction
was explained. Correct answers and conventional gradient/backprop training are
now authorized. This is genuine full text-parameter SFT, not another algebraic
last-matrix edit or LoRA. No exclusively coding-only parameters are known.

## Objective and immutable reference

Maximize correct programs on the SAME eight HumanEval questions measured in014:
32,39,75,114,119,129,132,147. Use their validated canonical solutions, same prompt
strings and EOS. These are eight target tasks, NOT the complete164-task suite.
No solution/reference or private test is inserted during generation. Public
examples/helpers already in the original problem remain present. The measured
target benchmark is intentionally trained on and cannot demonstrate independent
general intelligence or a clean HumanEval leaderboard score.

Start from best.pt SHA25646f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8,
not rejected014 or013. Preserve all old weights/reports. Keep the new specialist
separate from the general principal checkpoint regardless of fit improvement.

## Training scope and correctness

All546 unique active text parameter tensors (919659696 scalar parameters)
require gradients: embeddings/tied head, every32physical-layer attention and
MLP, norms, DeltaNet decay/conv7 operators, mHC weights/biases and24visit-gain
arrays. All153 vision tensors (100592896 parameters) are frozen. Rotary/position
buffers are not trainable weights. Zero gradients are possible by symmetry or
initially neutral branches; never add arbitrary noise merely to claim all
coordinates changed. Report eligible/present/nonzero/actually changed counts.

32physical layers,56executions,24-layer loop visited twice, mHC2, conv7/local256
remain structurally active. Visit gains are projected positive and normalized
after each optimizer step, preserving a valid two-visit inference configuration.
No architecture replacement. Parameters/buffers must first be normal-cloned
from inference-only tensors while preserving shared aliases.

Every layer execution uses nonreentrant activation checkpointing, with a
captured per-physical visit context restored during recomputation. Correct
forward and shared/tied gradient accumulation have been tested on real weights
without an update. Full ordinary-gradient preflight reached the8GiB limit;
the actual trainer releases each leaf gradient after Adafactor's step, verified
equivalent to an ordinary optimizer on a shared/tied checkpointed test graph.
Model preflight with two examples saw exactly one accumulated callback for
each of546text tensors. No optimizer update occurred in these preflights.

## Fixed bounded optimization, benchmark specialization

Batch2 examples, separately forwarded then their mean loss backpropagated once.
Adafactor per-parameter, no weight decay/momentum, lr.01, beta2_decay-.8,
eps=(1e-16,1e-3), clipping d=1, foreachFalse. Factor states use little memory.
BF16 backbone/gradients and FP32 mHC/visit gains remain as loaded. CE is FP32;
the tied head loss is checkpointed in16-token chunks to limit vocabulary RAM.
No weight master copy or new adapters. CPU4threads, seed20261112.

Maximum16epochs,64optimizer steps/128supervised example presentations.
Measure all eight training programs after each epoch. Stop early only if all
1098answer/EOS tokens are argmax-correct AND the worst gold-vs-competitor margin
is at least.5. Teacher-forced loss/accuracy are diagnostics, not final task score.
No dose search or initialization perturbations. Final free generation determines
how many complete programs are correct. Do not claim a mathematical global
maximum if the bounded budget falls short of8/8.

Training logs each completed step/epoch. A single final weight snapshot is
stored losslessly as streamed XORs against the immutable parent, compressed
into4MiB chunks, to fit local disk. Persist optimizer state, scalar/tensor
coverage, hashes and RNG state. Cold-restore all546text tensors and verify
their exact hashes before claiming checkpoint integrity. Do not overwrite a
completed checkpoint or blindly restart if a partial training log exists.

## Final evaluation and reporting

Use the original014judge/tests, exact same target prompts and320token greedy
seed0/thinking-off/cache/eager/BF16/4thread settings. Reuse completed unchanged
parent/original014references, with their source hashes; do not rerun them.
They each scored1/8 on this target. The new candidate must use cold-restored
saved weights and normal original native inference, not a training wrapper.

Evaluate eight target problems, eight MBPP diagnostic problems from014 and12
language/reasoning controls; record NLL on12old language anchors. MBPP was
already observed in014: held out of this training, but NOT a new unseen final
benchmark. It never chooses this specialist's weights. Run the separate known
magic-square counterexample too; preserve official counts separately.

If target improves, preserve as an experimental benchmark specialist. It is
not automatically promoted as the generally better Liquid Sense. Report
regressions, exact-vs-semantic control differences and benchmark contamination.
The old40final/32validation and RSI100reserved data remain unused. End with no
active training/evaluation worker and verified GitHub persistence.
