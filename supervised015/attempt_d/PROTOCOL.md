# Study015 D — final cached-generation readout alignment

C scored7/8 deliberately taught HumanEval targets,0/8 diagnostic MBPP,3/12
strict controls, and preserved B's six correct target tasks. General principal
remains unchanged. C's minPath free generation starts with val=0 instead of the
canonical n=len(grid), makes wrong neighbor bounds, repeats a scan and returns
coordinates. Its final uncached teacher-forcing accuracy was1096/1098. This
observed gap motivates actual CACHED generation states, not a new random edit.

All546 text tensors have already changed in B/C. D preserves those modifications
and refines ONLY the existing last physical31 MLP down-projection (1024x3584).
Layer31 is outside the repeated middle block and executes once, after its own
attention-cache update. Given fixed input tokens, its pre-MLP residual and MLP
input features do not depend on this final projection. This permits supervised
readout optimization on cached native forward states without recomputing the
frozen backbone. It does not identify this tensor as the unique cause of errors
or as a dedicated coding/thought module.

Collect all1098 canonical answer/EOS prediction states for the SAME8 target
programs through native model.generate/use_cache=True, greedy/seed0/thinking-off.
For this TRAINING COLLECTOR ONLY, a logits processor forces canonical next tokens
after recording the unmodified raw argmax/margins. This provides exact native
cached states under correct prefixes. These forced outputs are NEVER graded or
reported as benchmark results. Save x (final MLP input), r (pre-MLP residual),
native normalized h and raw predictions, every token label and context metadata.
No MBPP/control labels/outputs enter optimization. No private tests in training.

Refine W in h=final_norm(r+linear(x,W)). Full dense vocabulary scans select the
strongest non-gold competitor. Minimize squared hinge max(0,1-gold+competitor)^2,
with minPath states weight4 and other taught programs weight1. The analytic
subgradient for the active competitor uses only its and the gold embedding rows;
forward margins come from the real BF16 full-vocabulary logits. This avoids a
large dense-head backward while following its active logit-margin derivative.

Use a temporary FP32 master of this ONE3,670,016-element matrix; forward casts
it to BF16, so small accumulated updates can survive quantization. Frozen norm
and embedding are normal tensors suitable for backward; all other weights
remain C. AdamW lr5e-5, betas(.9,.999), eps1e-8, weight_decay0. Max12 updates,
project the FP32 displacement to <=1% of C matrix Frobenius norm after each step.
Stop early only when every collected gold token has real dense-head margin>=1.
No random initialization or perturbation. Verify native/reconstructed hidden
rounding differences and full-vocabulary diagnostic before first update; final
native generation, not fit, determines success.

Save raw BF16 final matrix as lossless chunks with hashes/C-parent tensor hash;
save cached states, FP32 master, optimizer/RNG and every training step in chunks.
C, B and principal remain fully preserved. Cold-load principal->B->C->D and
verify all546 text hashes; confirm all699finite and153vision unchanged. Overall
change counts replace only this matrix's count versus principal, never sum
repeated-coordinate updates. Architecture remains32physical/56executions/mHC2/
conv7/local256/two positive normalized visits.

Final evaluation is unforced, standard native greedy model.generate from ONLY
problem statements,320tokens code/64controls, seed0/thinking-off/BF16/eager/cache/
4threads, unchanged014judges/golds. Evaluate SAME8 taught targets,8 already-
observed MBPP diagnostic tasks,12controls/NLL anchors. No fresh benchmark claim.
Select D as experimental specialist only if it exceeds C's7/8 and loses no C
correct target. Otherwise retain C. No general principal promotion regardless
of in-sample success; report all regressions. This is the final bounded attempt
in015, not an unbounded benchmark search. End with no model worker running.
