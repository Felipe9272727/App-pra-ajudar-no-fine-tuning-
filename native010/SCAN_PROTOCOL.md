# Complete selected-checkpoint audit, before new native adaptation

Selected model is preserved best.pt parent SHA256
46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8.
008/009 completed without promotion; do not replay them or restart RSI100.
The new user asks for an extensive Python audit of all weights and a deeper
adaptation to the Loop/mHC plus Liquid-inspired architecture, aiming eventually
to outperform larger models. This audit cannot establish that capability.

Load the real selected hybrid including the parent overlay, not only its raw
safetensors scaffold. Inspect every value of every unique Parameter, every
registered Buffer, and record aliases such as tied input/output embeddings.
No subsampling of scalar integrity/distribution/source-difference statistics.
Streaming chunks bound memory; all scalar counts must sum to actual tensor
sizes and unique model.parameters() count. Inspect vision weights too, while
distinguishing text-only non-use from a broken module.

For each tensor record dtype/shape/bytes/hash, finiteness, exact zero/sign counts,
min/max/mean/std/RMS/L2, and full-value magnitude histogram. Compare every
reference-compatible scalar to its pinned Qwen donor; for seven-tap convolutions
use the explicit original four-tap alignment plus the new three history taps.
Record changed-value counts, difference norms and source identity. New router
or visit parameters have no original counterpart; do not invent one.

Inspect actual architecture, branch-zero/neutral layers, router input dependence,
stream symmetry conditions, per-visit gains, convolution history and local
attention. Statistics alone are not a unique causal assignment for model errors.
Do not modify model weights during scanning. Preserve full per-tensor JSONL,
summaries, code and hashes on GitHub. A separate native-adaptation hypothesis
and tests must be fixed before evaluating any new candidate.

Also compute complete row/column norm vectors for every matrix (flatten by
first axis for convolutions), and six deterministic full-matrix power iterations
as explicitly approximate spectral diagnostics. No claim of exact full SVD.
Trace actual parameter-storage reads during a text prefill and one own-token
step using TorchDispatch, including direct functional weight use; distinguish
observed access, zero branch contribution and vision non-use in text inference.
Record per-layer convolution history norms/DC gains and DeltaNet A_log/dt_bias.

No gradients, conventional fine-tuning, random weight edits, answer/solution
injection, gold edits or premature promotion. All previous checkpoints remain.
