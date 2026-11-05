# Hypothesis009 — protected vector transport across four MLP matrices

008 is complete: target and inverse both27/36 correct screen cases, no gains
or losses. Moment distance improved without task improvement. New user request
still seeks coordinated changes across model stages; this separate hypothesis
tests vector geometry rather than another norm dose. Start from unchanged
parent, never stack rejected008. No random edits, gradients or dose grid.

Target down_proj weights at physical layers5,13,25,31, each[1024,3584]. Layers
5/13 had large measured distribution deviations;25 had the strongest earlier
error/guard contrast;31 is the final MLP stage implicated by prior own errors.
Keep Loop/mHC and active Liquid,56 executions and all other weights unchanged.

Use exactly the19 unlabelled inputs frozen for008. Original and parent do
forward passes only: no reference solutions are generated or supplied.
Capture true down_proj input/output vectors at up to12 uniformly spaced token
positions per input, including the final position. For hybrid loop layers,
combine visits tokenwise with their existing .95/.05 gains. Other layers have
weight1. Original donor mapping is SOURCE_LAYERS. Inputs/token positions match.

At each layer, states P from12 ordinary texts AND the five matched prompts
where parent is equal/better define a preservation subspace. Code-prompt
states X from longest_run and overlap_count are residualized by
SVD against P, relative cutoff1e-5. Abort if residual norm <5% of original.
Let R be the residual states, D=Y_original-Y_parent at the same positions.
No token labels, correct replacement code or answers enter D: it consists
only of internal vectors from enunciados without any solution in context.

Fit one damped ridge correction:
  deltaW = .25 * [R.T @ solve(R@R.T + lambda I, D)].T
  lambda = .01 * mean(diag(R@R.T)).
Clip its Frobenius norm to .002*||W|| if necessary, once by this formula,
then write BF16(W+deltaW). Inverse control writes BF16(W-deltaW), never
selectable. Abort if quantized relative norm exceeds .003. Record actual
changes, fit residuals and protected-state leakage before/after BF16.
All four matrices are applied together, with complete rollback between variants.
Save exact per-matrix overlays, original tensor hashes and sampled states.

Compare actual jointly edited internal outputs on the same inputs, but accept
only by generated-code performance. Same seven-task36-case screen, inverse
first, target second; parent27 correct. Require at least one case gain with
no correct case lost. If it passes, run16-task/4-control/language-anchor paired
AND historical gates at160/32 greedy tokens, thinkingFalse, BF16/eager/four
threads. Anchor tolerance1e-6; original12/16 tasks and66/81 cases remains the
matched reference. Generated code runs only in the existing isolated judge.

Only a development-qualified target may be frozen by exact hashes and committed
before the untouched eight-task validation and its general controls. Compare
original, parent and target with identical settings. Require a complete-task
gain, strict case gain, no case/control losses and no worse NLL versus parent.
No tuning after that validation; otherwise retain parent. Observed old public
or diagnostic tests are never a new final. Finish workers and save decisions
on GitHub before ending the turn; no permanent background execution.

## Targeting correction before construction and candidate quality

The initial source1824a66 collected the same19 inputs but proposed transporting
all seven coding prompts. No009 candidate was constructed or evaluated from
that proposal. Before any edit, narrow its targets using the already-published
original/parent development comparison: longest_run5→4 and overlap_count5→2.
Protect prefix_sums,rotate_right,sum_abs,palindrome,binary_search instead of
copying original behavior where it is equal/worse. This uses existing case
fractions, never reference program text or any new validation result.
Capture methods, input texts, sampling, evaluation cases and thresholds stay
unchanged. initial_preregistration.json preserves the preceding file hashes.
The updated source and hashes are committed before any009 weight construction.
