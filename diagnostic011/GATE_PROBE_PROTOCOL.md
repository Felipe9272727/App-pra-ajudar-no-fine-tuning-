# Read-only causal sensitivity probe, after observational ranking

This adds no weight candidate and does not alter metric/test/gold definitions.
The full 699-parameter trace is already complete. Its largest absolute
error/guard reader-output RMS contrasts are in_proj_a weights at physical
layers 25,6,28. A is the input projection governing DeltaNet log decay:
g=-exp(A_log)*softplus(a+dt_bias). Higher RMS alone does not establish stronger
forgetting, because the sign and per-head offsets also matter.

For the five observed error responses, use the actual captured token prefix
ending immediately before the predeclared suspected-span start. Only the
student's own prefix is in context; no teacher/correct solution is supplied.
Compare a paired full-prefill baseline with one physical layer's last-token
in_proj_a activation scaled to .99 or 1.01 on both loop visits (outer layer28
has one visit). Keep all earlier token activations, all weight parameters,
loop settings and Liquid operators fixed. The parameter tensors must match
before and after. BF16 changes are reported, not assumed equal to requested1%.

Report max/L2 logit difference, argmax change, actual activation-change norm,
and log probability of the student's own original token. Comparing full
prefill to cached logits is a separate numerical diagnostic, never an edit
benefit. These probes show local sensitivity, not which weight uniquely caused
a semantic error, code correctness, a quality gain or 4B superiority. No new
program is graded/promoted and no independent validation is opened.
