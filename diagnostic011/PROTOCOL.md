# Diagnostic 011: all-parameter tracing of actual incorrect generations

Selected parent only: best.pt SHA256
46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8.
Native 010 variants were rejected; do not analyze them as the selected model.
No weight edit, gradient, backward, optimizer or promotion in this diagnostic.

Goal metric: Delta4B_pp = 100*(problem_pass_at_1(Liquid Sense)-
problem_pass_at_1(pinned Qwen/Qwen3.5-4B)). A problem counts only when all its
fixed cases pass from ONE generation. Partial cases are secondary diagnostics.
Matched problems, literal prompt context, generation budget, thinking mode,
precision, sampling and judge are required. Public primary target is a new,
frozen LiveCodeBench subset, not the observed internal 16-task development.
Use at least 100 fresh problem pairs for a confirmatory superiority claim,
strictly positive paired-bootstrap 95% lower bound and exact one-sided paired
sign/McNemar p<.05, with preserved general/language controls and a frozen
checkpoint before outputs. Report task-level uncertainty, not independent-case
confidence. This is coding superiority at that budget, not general intelligence.
If actual 4B outputs are missing, Delta4B is UNMEASURED, never imputed from
parameter count or vendor tables. No paid service or larger runner is enabled.

New instrumentation replays five already-observed wrong parent responses:
prefix_sums, overlap_count, run_lengths, rotate_right, longest_run. Compare two
successful responses sum_abs,binary_search. These are NOT fresh validation.
Greedy, thinking off, 160 new tokens, same four-thread BF16 CPU runtime. Feed
only each enunciado and the model's own autoregressive tokens; no reference
solution, correct target token, gold case or old response is teacher-forced.
Old responses are used outside inference to select diagnostic timepoints and
to assert exact replay. Save actual generated IDs and per-step next-token logits.

Enumerate all 699 unique parameters (tied embedding/head counted once). During
EVERY real model forward in generation, TorchDispatch records raw parameter
storage accesses, separating view/metadata, dtype/copy transformations and
mathematical operators, with current module and physical-loop visit. A raw read
is participation evidence; it is not causal error attribution. Derived copies
can leave raw storage, so do not call this a complete operator dependency graph.

Hook all direct-parameter owners, all physical layers, and relevant ancestors.
Collect last-decision input/output RMS, mean, abs max, exact zero fraction,
nonfinite counts and vector sizes at each call/visit of EVERY generation step.
For shared gated RMSNorm flattening, include all value heads of the last token;
for attention head norms keep the last token's full head group. Report actual
owner/ancestor relationships. Functional convolution weights may be read without
calling nn.Conv1d.forward; they inherit their actual invoked ancestor and have
QKV activation coverage. Never mistake the absence of a Conv module hook for
an unused weight. Vision/MTP non-use in text inference is explicit.

Preserve exact last-decision activation tensors (their actual dtypes) for all
invoked hooked modules at three predeclared positions per response: middle,
last, and one suspected semantic-error span from the old model output (or
first position for successful guards). The span is only a hypothesis. Verify
its actual generated-token mapping afterwards; do not invent missed snapshots.
Also aggregate full input-coordinate second moments for every actual Linear
and normalized-router use across ALL decisions, each response equally weighted
in error/guard comparisons. Store all coordinates, not only top features.

Tensor activity proxy for compatible linear uses is sqrt(sum_j ||W[:,j]||^2
E[x_j^2]/output_width). It uses all columns and excludes cross-covariances; it
is NOT causal importance, a gradient, or a prediction of which weight to edit.
No arbitrary error/guard contrast can independently authorize a weight edit.
Check full parameter hashes before/after and original checkpoint hash; outputs
and case bits must exactly match the prior parent. Instrumentation must not
change predictions. Tests cover functional parameter access, aliases, metadata,
last-token/head selection, metrics and criterion rejection for missing/mismatched
4B results. Save code, raw per-step numeric profiles, selected activations,
all-tensor tables, reports and state on GitHub. Independent validation stays shut.
