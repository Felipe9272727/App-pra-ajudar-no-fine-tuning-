# Spec026 — scaled from-scratch hybrid drafters and measured greedy speculation

User authorization: create the small speculative AI from scratch with the same
active architectural family as Liquid Sense, study achievable speed and small
standalone quality. This is a NEW experiment, not continuation of025optimizer.
025summary/report/checkpoints are complete/rejected; its status label remains
comparison_complete_pending_report. No old training/evaluation is repeated.

Create two TEXT-ONLY children without loading/copying pretrained weights.
Shared original tokenizer/vocabulary248320and tied input/output embeddings are
required for direct token proposals. Preserve32physical layers, loop4..27twice
(56visits),2-stream mHC,3GDN:1attention pattern,conv7and256windows at7/15/27.
Widths: small h64/MLP256/GDN1x16/attention1x64, and large h256/MLP1024/GDN4x32/
attention4x64; KV1,RoPEpartial.25sections3/3/2. Expected~18M/~95M parameters,
actual unique counts audited. All branches initialize normally, not neutral
clones of the teacher. Initial visit gains[.5,.5],positive normalized during
training. Router defaults FP32; all other child weights trained from seeded
initialization. Teacher weight/config provenance and all initial hashes saved.

Use existing observed verified120review013TRAIN programs and16balanced016
TRAIN general examples,32constructed checked multiplication examples, plus24new teacher-generated training conversations
(max48tokens each). Teacher outputs are raw behavior traces, NOT assumed correct
solutions. Teacher remains frozen and uses cache/greedy/no textual thinking.
Children receive no held-out quality/speed references as training data. Newly
authored standalone quality8code+8general questions and speculative8prefix
prompts stay separate. No old013/016/RSI100final sets are opened.

Training from scratch is bounded pilot, not corpus-scale pretraining:3epochs over
packed128token blocks,batch2, same token exposures for both sizes. Causal CE on
full conversations (including user text) teaches a fresh tokenizer embedding;
outputs/assistant content are not inserted into evaluation prompts. Adafactor
FP32 master parameters with BF16 CPU autocast, matrix lr.03/controllers lr.003,
10step warmup then cosine to.25,gradient norm1. Embedding/residual forward uses
BF16 and GDN recurrence remains FP32 to match inference arithmetic contracts. All child parameters eligible.
Save seeded FP32 initial and exact final train state/optimizer/RNG in verified
parts; save BF16 inference variant separately, with routers/gains FP32. Scores
and speculation use saved BF16 variants. Save loss/gradient/memory per step.
No tuning using final benchmark outputs. Report corpus/tokens actually trained.

Implement normal greedy baseline and cached-block speculative prototype. Target
is preserved general parent46f6697... in PyTorch BF16/eager,4threads, not the
quantized Android runtime. Keep target and draft caches synchronized. Retain all
56virtual GDN/conv/KV states in snapshots; on rejection restore and recompute
committed prefix before continuing. Pending-token/bonus work must be accounted
in next block or measured correction, never free acceleration. All returned
output tokens must be selected/accepted by the frozen target.

GDN cached blocks may use the identical sequential recurrent rule across time,
with batched projections; initial prefill stays unchanged. Test block versus
serial token outputs and rollback, including rejection at every position.
If block path differs in target greedy output on frozen parity probes, classify
it ineligible; retain serial verification as exact slower fallback. Do not
present a faster different-output path as lossless or deploy it by default.
Only greedy distribution is studied. Unit mock/oracle cases are correctness
tests, not claimed real model acceleration or intelligence.

Freeze quality prompts and timing plan before outputs. Report initial/final
child standalone task correctness separately from target matching/acceptance.
Evaluate target plus both BF16 children, identical prompts/greedy/budgets96code,
32general. Primary speculative timing:8new prefixes,32target output tokens,
block4,one warmup per variant then6fixed ABBA pairs over3of those prefixes.
Measure serial target versus each trained child with all per-request overhead
with models already resident (tokenization, prefill, draft, rollback and decoding;
weight loading excluded and reported separately);
report decode-only timing separately, plus proposals, acceptance,rejections,
forward calls, evaluated tokens,TTFT and resident memory. No repeat to select a
better result, no Android/Snapdragon claim or copied DSpine speed estimate.

This tiny corpus cannot establish general intelligence, minimum possible size
or superiority to larger pretrained models. Retain target/APK and all old
checkpoints. Even if faster on these probes, this is a CPU research prototype,
not a new Android release. Freeze sources/data before training/quality/timing;
record engineering fixes without rewriting reference labels or prior outputs.
Persist all artifacts, close workers and verify Git outcomes before final.
