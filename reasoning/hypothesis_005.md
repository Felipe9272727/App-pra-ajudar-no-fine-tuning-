# Hypothesis 005 — selective third loop visit, preregistered after 003

User steering: continue improving and explicitly reinforce SenseNova looping
in components implicated by errors. Trial 003 changed the weights of two
existing visits but changed no case outcomes. It did not test an extra visit.
This additional authored hypothesis tests actual computation depth, separately
from the rank-one dense edit. No feedback-selected dose grid is introduced.

Start from unchanged parent; do not stack unvalidated 004. Keep shared weights,
32 physical layers, mHC and all Liquid operators. Use three complete virtual
visits with independent recurrent/KV caches: 82 layer executions per step.
For diagnostic-selected layers 25,27,26, directly store FP32 visit weights
[0.925,0.05,0.025]. Other middle layers store [0.949999,0.05,0.000001]. Every
visit is positive and each layer's gains sum to one. The tiny non-target third
gain keeps the intervention concentrated on the measured target layers while
leaving all architectural components active. This adds actual compute and
does not prove better reasoning. Runtime/latency differences must be reported.

Use the bottom-three diagnostic layers 19,12,13 as a matched equal-depth,
equal-dose control. Compare actual six-task free generation to the saved
unchanged parent with the same 160-token output budget. Run the real tiny
three-visit cache test before scoring. Require strict case gain and no case
loss, followed by full paired/historical gates. Any qualifying candidate joins
004 in the single unopened RSI100 validation. Freeze all candidates first;
no more weight hypotheses after this finite third intervention in this request.
The public benchmark suite remains unobserved and never selects a new edit.

Historical edit_plus_loop3 used a different dense matrix and uniform gates.
This trial uses parent weights and selective per-layer third-visit gates; it is
not a replay of that completed experiment. Preserve both candidates and logs.
