# Error attribution and thought-budget continuation

New user request after the completed public pilot; parent remains best.pt
SHA256 46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8.
All previous benchmark outputs are observed diagnostics, never a fresh final.
Keep every old artifact and frozen evaluator unchanged. No automatic search.

## Measurement audit

Quantify stopped/capped generations, repetition, syntax/AST rejection and
semantic errors separately from the saved outputs. A code validator rejecting
`for _ in ...` is a harness limitation, not evidence of faulty reasoning.
Do not change old primary scores or infer that allowing `_` fixes the program.

Matched greedy diagnostic on observed gsm8k:914, gsm8k:501, lcb:abc387_a:
original and unchanged hybrid, thinking off/on, each with 512 output tokens.
Prompts remain byte-identical to the earlier pilot, including no worked answers.
Same BF16/eager, cache, seed0, four threads. Unlike the older runtime's thinking
helper, do NOT switch sampling on when enabling thinking. Capture own tokens
and actual final-MLP decoding states for the hybrid. Scores are exploratory,
not a test of weight improvement. Report cap hits and whether thinking ended.
This tests two factors separately: new budget (vs historical budget) and
thinking template (off vs on at equal512). No model identity system context.

## Hypothesis 006: protect language as well as code in negative-only edit

004 gained one development case but worsened anchor NLL. Its preservation
subspace covered code guards, not ordinary-language anchors. From unchanged
parent, use exactly its own rotate_right erroneous token `[k` and real cached
state; do not supply a correct replacement. Add actual final-MLP input states
from all existing plain-language anchor texts to the 137 earlier protected
code states. These contain no coding solutions. Compute an SVD null-space
residual, using relative singular-value cutoff1e-5; abort if its norm <5%.
Write the existing BF16 tensor layers.31.mlp.down_proj.weight using
W' = BF16(W - .006 ||W|| normalize(unembedding[bad_token]) v.T).
No dose grid, no gradients, no positive targets. Archive actual rounding drift,
changed coordinates and directions. This is an intervention candidate, not
proof that this matrix uniquely causes the error or is a dedicated thought area.
Record predicted direct projection at the target and protected states before
and after BF16 rounding. Compare to archived004, without replaying it.

Run the same six-task160-token screen as003/004/005. If strict case gain and
retention pass, run all16 development tasks, four general controls and anchor
NLL; require paired AND historical monotonic gates (NLL tolerance1e-6).
Restore parent after any failure. No other edit is authorized by this finite
preregistration. All Loop/mHC and Liquid operators remain active.

Only if006 passes development, freeze its exact file hash before the untouched
RSI100 validation8 and val controls, with original/parent/candidate matched160.
Require at least one more complete task and strict case gain vs parent,
no lost correct cases/controls, and no worse NLL. Otherwise no promotion.
Once final results are observed there is no more selection or editing here.

Finish and verify GitHub outcome commits, with no local worker left running.
