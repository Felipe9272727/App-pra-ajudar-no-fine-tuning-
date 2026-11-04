# Assistant-guided direct-weight research

The user changed the outer-loop controller: the capable assistant authors each
hypothesis from actual student errors, own generated tokens and causal tests.
The previous five-family automatic search is paused after 31 saved rejections;
it is not described as a completed 100-round run or autonomous self-improvement.
Keep Qwen-sized Loop/mHC and Liquid-inspired components active; no gradients,
SGD, positive reference solution, correct next-token label or oracle answer in
the student's prompts. This is external model-guided optimization.

Each hypothesis is recorded before its end-to-end trial. The teacher can identify
a semantic mistake in the student's own response and test whether an algebraic
edit changes a related token decision. A wrong token can be a symptom of a broader
planning error; neither correlation nor a fixed-prefix logit change proves that
a coding ability has been located. Use matched random/reverse controls and
preserve unrelated contexts before making a quality claim.

The first hypothesis uses a negative-only rank-one update of the final existing
MLP projection. Its input direction is residualized against earlier length-call
contexts produced by the student; its output direction comes from the existing
unembedding row of the undesirable student token. No correct replacement token
is supplied. Exploratory dose/reverse/random diagnostics are saved separately
from actual code-generation scores. The selected 0.003 norm fraction is fixed
before trial_001's generation/correctness feedback.

Test parent, matched random and selected negative edit on observed development.
If selected screening does not strictly gain cases without loss, reject and
restore parent. Otherwise rerun full parent and candidate under the same local
execution, and require strict execution gain versus both paired and historical
incumbent, preservation of every correct case/control and no anchor-NLL increase
beyond 1e-6. Passing observed search only makes a candidate eligible for later
fresh validation; it does not deploy or prove generalization.

Initial research budget: up to four assistant-authored hypotheses. The assistant
reviews each result before choosing the next intervention; no automatic template
loop continues. Keep the old reserved validation/final sets closed until freezing
the guided candidates; after observing them, do not reopen adaptation using those
same reserved sets. Old round logs and baseline/best weight files remain intact.

Execute generated code only with the validated local syscall-filtered AST judge.
Save source, hypothesis, diagnostics, directions and actual outcomes to GitHub.
Rejections keep audit logs and restore/delete provisional weight edits.
