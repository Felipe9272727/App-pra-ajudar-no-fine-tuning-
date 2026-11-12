# Original Qwen reference, no candidate/selection changes

In addition to the frozen parent/candidate comparison, run original Qwen under
the same greedy thinking=True256-token conditions on the same two observed
teaching probes, using evaluate_with_original.py original. Reuse the completed
original10/12 controls under matching nonthinking64-token conditions. This is
an extra reference, never a change of golds, budget, gates or weight selection.
The existing parent/candidate worker uses immutable evaluate.py as registered.
No original thinking code result from this protocol had been queried at this
addition. Principal and candidate native EOS and vocabulary stay unchanged.
