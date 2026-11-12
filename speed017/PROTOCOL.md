# Speed017: exact runtime work, followed by a separate reasoning pilot

Parent: Android source commit 5a7d0a2bb32c63da55b59f6e9b23b245710f5c83.
The installed APK uses the preserved general principal, not specialist015E.
Canonical principal SHA256: 46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8.

This study does not change model weights. Preserve 32 physical layers, all56
visits, independent visit caches, positive gains, both mHC streams, conv7 and
window256. Keep Android baseline source immutable; prototype in runtime/.
Never claim official Liquid LFM or official SenseNova weights.

Frozen hypotheses, before timing or candidate runs:
1. Gated DeltaNet currently reads recurrent state with a stride128 inner loop.
   Traverse rows and vectorize independent output columns instead. Preserve
   each output's multiplication and addition order, FP32 state and BF16 casts.
2. Routers with exactly zero input matrices have constant gates. Cache the
   same gate computation; do not bypass the two-stream merges or visits.
3. Reuse only an exact token prefix and its entire per-visit state across chat
   turns. The app currently re-prefills the whole conversation. Do not change
   its chat template or pretend the empty think suffix is actual thinking.

Evaluate reference/optimized toggles in the SAME new binary, four threads,
same weights/token IDs, greedy lowest-ID tie policy. Require bit-identical
hidden states, recurrent/conv/KV states and logits on the trace fixture, plus
identical generated token IDs on conversation probes. Prefix cache mismatch,
new conversation, or context trimming must fall back safely. No speculative
sampling, quantization, approximate arithmetic or layer pruning in this study.
Timing: one warmup, then ABBA order; report individual observations and paired
speed ratios. Explicitly label cloud x86 CPU; no phone speed measurement.
A finite equivalence suite is evidence within its tested domain, not a proof
for every possible input. The rejected historical quality trials stay rejected.

Research followup: retain and cite supplied dossier/official archived DSpine
sources. Cost a ~100M text architecture including tied vocabulary embeddings.
Do not create random weights or claim a trained small model. Serial target
verification cannot deliver speculative speedup; needs block verification and
correct cache rollback before a compatible trained drafter can help.

Reasoning training must use a new directory/protocol, supervised targets only,
native EOS248044, both actual visits in backward. It is separate from exact
runtime speed work. Long output by itself is not correctness or intelligence.
Keep general principal and previous specialist checkpoints immutable. End all
model processes and persist complete reports, including failed hypotheses.
