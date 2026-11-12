# Post-screen long-budget diagnostic (not selection)

Candidate finished the registered256-token teaching probes with0/2 completed
final answers and preserved10/12 general controls. Weight selection remains
closed on this pilot even if a longer budget helps; no promotion from a
post-hoc budget change. No fresh validation will be consumed for this candidate.

One fixed observed teaching problem above_0 gets a secondary1024-token greedy
comparison, original/parent/candidate under the same thinking prefix, seed0,
nativeEOS248044,4threads. Its purpose is to distinguish short-budget truncation
from failure to finish even when permitted long thinking. No weight updates.
For an already EOS-finished256 run, reuse it: a higher maximum cannot change
an already-complete greedy sequence. Otherwise generate1024 and require the
first256decoded-token-prefix digest to match the saved256run exactly. The
latter reruns that prefix because the previous cache was not saved; it adds a
new declared budget diagnostic, not another copy of the old screen score.

Report final correctness, closure/completion, actual token/time and limit hit.
Do not treat longer text, hidden-state movement or elapsed time as intelligence.
Keep all256 results and this diagnostic separate; no gold in model inputs.
