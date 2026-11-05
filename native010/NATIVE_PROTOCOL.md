# Native architectural warmstart, frozen before candidate quality outputs

Audit: 699 unique tensors, 1,020,252,592 scalars, no nonfinite values.
Parent SHA256: 46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8.
All prior studies stay archived; no previous failed candidate becomes the parent.
No gradients/backward, optimizer, random perturbation, model-generated teacher
solution, answer label, or gold-program input is allowed in construction.

Three fixed component ablations, each reconstructed from the preserved parent:

A / depth: restore the two zero output projectors of layers 8:12 from 4:8
and 20:24 from 16:20, including corresponding complete seven-tap temporal filters.
Copy donor local-window choices. Before any scaling, clone all donor tensors.
For every middle layer 4:28 multiply its attention output and MLP down matrix
by 1/(2*k), where k is the number of middle physical occurrences of its
original Qwen donor. Set all middle visit gains to [1,1]. Thus every original
donor has aggregate output-projection coefficient one across its physical
copies and both visits. This is only a first-order split-step initialization;
nonlinear blocks do NOT commute, so quality may regress. Both passes and all
32 physical layers become active without adding parameters or executions.

B / liquid: start from A. Use exactly the 19 already-observed, unlabelled inputs
in reasoning/multi008/inputs.json. At 12 uniformly spaced positions per input,
collect original-Qwen convolution preactivations, never generated answers.
On A, collect seven input lags per channel at matching positions and all visits.
Each repeated visit has weight 1/2; outer layers have weight 1. Solve independent
seven-coefficient ridge systems, lambda=.1*mean(diagonal(Gram))+1e-6, with A's
filter as prior. Cap each channel's coefficient-change L2 to 5% of its prior
L2; omit corrections smaller than .1%. Quantize to BF16; reject nonfinite
results. No change to recurrent A_log or dt_bias without a causal hypothesis.

C / routed: start from B. On the same unlabelled inputs, capture the last-token
normalized mHC residual input on both visits, for both routers in all 24 middle
layers. Direction = mean(second-first); center its projection at the combined
mean; scale so maximum calibration absolute logit perturbation <=.125. If
zero direction, keep that router unchanged. Write paired opposite pre/post
rows and symmetric opposite mixer rows; preserve pre sigmoid sum 1, post sum
2, doubly stochastic mixing. These constraints bound calibration perturbation,
not universal generalization. Input-dependent route may separate streams.

Before quality evaluation: save reconstruction manifest, hashes of every
modified tensor, exact temporal/router overlays, frozen source/data hashes;
cold-reload each bundle and compare every modified tensor bitwise. Test cache
prefill/decode equivalence at lengths 17,257,513 (including local-window edge),
requiring same top token and max logit difference <=.5 as in prior protocol.
No candidate with failed integrity/cache checks is eligible.

Matched development screen: the same seven tasks prefix_sums, rotate_right,
longest_run, overlap_count, sum_abs, palindrome, binary_search; greedy,
thinking off, 160 new tokens, four CPU threads, identical tokenizer/context,
no feedback. Compare case-level pairs and complete tasks to both preserved
parent and original Qwen. Parent and Qwen rows are reusable only with exact
source/data/inference identity; otherwise rerun. No claim these are new tests.

Predeclared staged gates: only a candidate with strictly more passed cases,
no lost previously-passed parent case, and no fewer complete tasks on screen
receives full 16-task development, 4 controls and 12 language NLL anchors.
Full gate requires a strict complete-task improvement, no case/control loss,
and NLL <= parent+1e-6. If multiple qualify, choose most complete tasks, then
cases, then lower NLL, then least added component (A before B before C).
Freeze that exact checkpoint before opening RSI100 validation's 8 unused tasks
and validation controls. Promotion requires the same full gate on independent
validation; report original Qwen comparison too. On failure preserve parent.
Do not consume independent validation if development cannot justify it.

No changed golds, no replay of old experiments, no benchmark-wide intelligence
claim, and no claim to beat a larger model without a matched larger baseline.
Preserve all rejected ablations as reproducible incremental checkpoints.
