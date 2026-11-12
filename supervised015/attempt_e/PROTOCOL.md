# Study015 E — repair terminal-label mismatch within D's original budget

D's real, UNFORCED result was7/8, gaining minPath but losing find_zero to repeated
assistant turns after an otherwise correct canonical function. It is rejected
as a replacement for C by the predeclared no-task-loss rule. Preserve D fully.

A concrete implementation mismatch was then verified in eos_mismatch_001.json:
GenerationConfig.from_model_config yields native EOS248044(<|endoftext|>), while
all earlier teaching used tokenizer.eos_token248046(<|im_end|>). The latter closes
a chat turn but does NOT stop this unchanged native evaluation configuration.
D learned all1098 old labels with margin>=1, including this wrong terminal target.
This is an openly recorded training-label repair, not a hidden new dose search.

Keep runtime EOS, prompts,320/64tokens, greedy/seed0/thinking-off/BF16/eager/cache/
4threads, official judges/golds and every reference PROGRAM unchanged. Correct
ONLY the final target label of each of8 cached training trajectories from248046
to248044. Their x/r states were computed BEFORE the final output token, so no
state recollection is needed. Preserve original D cache/labels; save exact index
mapping for E. No MBPP/control outputs/labels in training.

Restore D's FP32 master/AdamW state and use at most the SIX remaining updates
from D's original maximum12; D used6. Same lr5e-5, betas, sparse active-competitor
margin gradient, native full-vocabulary scans, norm/embedding/frozen backbone,
minPathweight4, <=1% FP32 Frobenius displacement from C. Stop if all corrected1098
labels have margin>=1. Temporary precision/master affects only the final3,670,016
matrix values; infer in BF16. B/C's changes to all546 text tensors stay preserved.

Save E separately as full raw BF16 last-matrix patch against C, not overwrite D.
Preserve optimizer/master/RNG, label mapping and all steps; reuse original D
cache through verified chunk hashes. Cold-restore principal->B->C->E, verify all
546text hashes, all699finite, other698parameters unchanged,153vision unchanged.

Final evaluation is ordinary UNFORCED native generation, no teaching processor,
same8 intentionally taught HumanEval targets,8 previously observed MBPP problems,
12controls/NLL. Existing original/principal/B/C/D outputs reused, not repeated.
Select E only if it exceeds C7/8 and loses no C correct target. Otherwise keep C.
No principal general promotion. This ends015; no more optimization after E.
Record both the implementation failure and its measured repair, all regressions
and benchmark contamination. End with no model worker running.
