# Supplied CCORE/DSpine dossier and speed constraints

Read the user's full PESQUISAS_LIQUID_SENSE_CCORE_DSPINE_CODEX.md attachment,
also preserved in review013/USER_RESEARCH.md, and the primary sources archived
in review013/sources/. The previous review013/PLANO_DSPINE analysis is preserved.

CCORE teaches a useful engineering lesson: train on validated executable
artifacts and partition data before selection. Its advertised GLB/3D examples
are domain training; they do not establish a speed or general-reasoning gain
for our checkpoint. Explanations and correct programs can be teaching targets
with the user's gradient authorization; answers must remain outside test inputs.

DSpine: https://github.com/Tencent/DSpine and the official
`tencent/Qwen3.8-27B-DSpine-b16` config in review013/sources/. The released drafter
has2,025,912,064 parameters, five layers, hidden5120, block16 and target feature
layers46/61. Our text width1024/32physical layers and vocabulary/cache contract
are different. This is not a compatible auxiliary checkpoint for Liquid Sense.
Author throughput speedups2.71–3.84x were measured with GPU SGLang0.5.22, BF16,
FA3 and concurrency8; they are not accuracy increases or phone measurements.

Let Ct be one target-token cost, Cd one draft-token cost, k the drafted block,
a the number of accepted verified draft tokens, and Cv(k) target verification cost.
Speed ratio = a*Ct / (k*Cd + Cv(k) + overhead).
Any bonus token must also advance target state; count that cost over successive
blocks rather than treating unfinished target-state work as free.
Our current target processes tokens sequentially, so Cv(k) is approximately
k*Ct. Since a<=k and Cd>0, merely adding a drafter cannot improve this ratio.
First implement efficient block verification and state rollback (all56virtual
GDN/conv/KV caches), then train a tokenizer/feature-compatible small drafter.
Greedy verification must preserve exact target tokens; sampled verification
must preserve the target distribution. Do not call an unchecked draft lossless.

A possible text-only model with the same32/56Loop/mHC/conv7/window256 layout is
costed in parameter_budget.py, including the large248320-token vocabulary and
tied embeddings. Result94,832,240unique parameters; embeddings consume~67%.
This is an audited dimensional design, not a trained100M model or a quality
claim. Width256, intermediate1024, four32-dimensional GDN heads, four64-dimensional
attention heads and one KV head. BF16 weight lower bound~189.7MB, before runtime
state. Existing Rust hardcoded dimensions require a separate implementation.
A standalone small model needs distillation/training and separate validation;
quality retention is possible via checked drafting, not guaranteed by shrinking.

First action in this study is exact runtime improvement. The installed app
forces an empty think block and limits generation to256tokens; it therefore
is not currently providing the extensive-thinking behavior requested. Enabling
longer output must be evaluated with actual correctness and completion checks,
not an assumption that extra text or a larger loop gain creates reasoning.
