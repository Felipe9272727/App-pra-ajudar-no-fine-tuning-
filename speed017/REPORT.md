# Speed017 — exact runtime prototype

Preserved the installed0.1.0 APK and every canonical model weight. The new
implementation is isolated in speed017/runtime; the installed app is not updated
by this experiment. Same32physical layers,56executions, independent visit states,
two mHC streams, positive gains, conv7 and window256. No quantization.

Implemented row-major DeltaNet reductions with identical per-column FP32 order,
constant gates only for routers with exactly zero matrices, and an exact token-
prefix/session cache across turns. Changed prefixes safely fall back to a fresh
session. The current chat template and greedy lowest-ID tie rule are preserved.

Validation: seven technical tests pass. A sixteen-token live trace compares
912hidden vectors,896virtual cache-slot snapshots and3,973,120vocabulary logits:
all bit-identical to reference. Three chat requests (including a later turn and
a changed prefix) produce26identical generated token IDs and identical text and
finish reason. Finite probes establish measured equivalence, not a universal
proof for every input or for Android/ARM floating-point implementations.

Four ABBA-ordered pairs of16tokens on the cloud x86 CPU, four threads:
reference mean2.4006s, optimized mean2.1395s, ratio1.1220x (~10.88% less time).
This measures the backbone, excluding vocabulary readout/tokenization. Paired
sign-flip two-sided p=.125;95%paired-difference interval[-.0732,.5954]seconds
includes zero. Thus an observed speed signal, not a statistically confirmed
speedup. Raw short and extended measurements are both preserved.

In the single two-turn chat probe,22prefix tokens were reused: preparation
6.0365s→2.6822s (2.2506x). Decode1.6016s→1.5182s. This is a host observation,
not a phone result, benchmark-quality gain, or estimate of overall app speed.

Phase timing on extended runs (means, seconds/16tokens): DeltaNet including
projections1.0812→.9045; MLP1.0723→.9951; attention.2156→.2203; routing
.01276→.00259. Unchanged MLP/attention timing also varies, illustrating noise.
No physical-phone or new Android-binary validation was performed in this study.

Research review and exact95M-parameter budget are in RESEARCH_REVIEW.md and
reports/parameter_budget.json. That is a design, not trained small weights.
The current official DSpine README was rechecked and archived with a hash.
A later app selector is recorded in MODEL_SELECTOR_BACKLOG.md; main research
priority remains measured speed plus a separate supervised-reasoning pilot.
