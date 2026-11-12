# Next hypothesis prepared from018, not executed

018 actually trained Loop/mHC/temporal/norm parameters together. It did not
train the16frozen neutral output matrices. Their exact zero values disconnect
60selected branch tensors from the supervised loss, as verified by the chain
rule and matching per-family gradient counts. This is a scope limitation, not
evidence that all observed generation failures have that cause: original Qwen
also fails the two256-token thinking probes.

A separate next pilot should start from the immutable GENERAL parent, opening
those16exit projections along with the329current tensors. Exact dense scope:
345tensors /48,813,232values. This is not all model weights or "thought weights".
The16exits contain46,137,344values, both attention/GDN and MLP outputs of the
eight inserted neutral layers. Preserve32physical layers and56actual visits.

A rank8 training alternative adds491,520trainable adapter values to the current
2,675,888, total3,167,408. Eight MLP matrices contribute8*8*(3584+1024)=294,912;
eight attention/GDN outputs8*8*(2048+1024)=196,608. Initialize the second factor
to zero so initial forward behavior stays identical; a declared seeded first
factor is adapter initialization, never random perturbation of existing model
weights. At step1 only the zero second factor may receive useful gradients;
after it learns, require real nonzero upstream gradients on previously blocked
branches. Do not report eligibility as actual gradient coverage.

Validate the MERGED BF16 dense checkpoint, because a low-rank two-matmul path
and merged BF16 weights have different rounding. Preserve the temporary adapter
checkpoint, merged weights and exact parent hashes separately. Standard loss
must supervise correct final/EOS as well as checked educational explanations;
verbosity is not an objective. General replay and a bounded teacher-retention
term need a fixed data/compute budget before training. Do not resume018with a
new scope/learning rate or erase its negative outcome.

To establish useful loop behavior, inspect both actual visits and run a separate
paired causal exit replacement after a quality gate. A changed state, nonzero
router or larger second-visit gain is insufficient. Stronger/increased loops
also increase per-token compute, so they require measured correctness benefit
at a fixed response budget and latency. DSpine still needs efficient block
verification/cache rollback before a trained small drafter offers lossless speed.

This file is a concrete dimensional/training design only; no019training,
new adapter, random model, or improved checkpoint is claimed. The final018
1024-token diagnostic and confirmatory speed measurements remain separate.

If formerly zero exits learn nonzero values,019must not shortcut those matrices.
It detects actual bytes at load, so benchmark the newly merged checkpoint again;
the measured general-parent speed ratio cannot be assumed for new weights.
