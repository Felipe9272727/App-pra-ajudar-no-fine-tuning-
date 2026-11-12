# Balanced joint adaptation016 — client date12/11/2026

Recovered015E exactly from fd844c3f8049061deda32f45a77043a96c5b2a2d. It scored8/8
deliberately taught HumanEval tasks,0/8 MBPP diagnostics and6/12 strict controls,
versus original/general principal1/8,0/8,10/12. Those sets are observed development
and retention diagnostics, not fresh independent validation. Preserve E as the
existing benchmark specialist and best.pt as general principal throughout.

Hypothesis: narrow all-text specialization damaged general response/routing,
including ordering/subtraction and one-word formatting. Balanced supervision on
NEW general examples, with old code as retention replay, may recalibrate norms,
context-sensitive mHC routing and Liquid-inspired temporal memory while freezing
bulk pretrained attention/MLP/embeddings. This is a hypothesis, not unique causal
blame or a dedicated thought-weight claim.

Train330exact parameter tensors/6,345,904values listed in trainable.json: all
native visit gains and mHC routers, temporal in_proj_a/b,A_log,dt_bias,conv7,
normalizations and existing physical31MLP down projection. Loop/Liquid parameters
receive gradients in the SAME loss and both shared middle-block visits. Bulk
QKV/other MLPs/embeddings are frozen. Preserve32physical/56executions/mHC2/conv7/
local256/two positive normalized visit gains. Vision153 stays frozen.

Sixteen fixed updates. Batch2: old code retention task step%8 plus each of16new
general examples in fixed order. Each example's answer/EOS token CE is averaged,
then code/general mean. General training questions AND answer strings exclude
all12old control questions/answers; examples are different subjects/numbers and
ordinary related skill families, not evidence of task-family independence.
Native stop ID248044 asserted from the loaded model; answers are appended with
that integer. No tokenizer.eos248046. No incorrect solution injected at test.

Adafactor relative lr.0005, no decay, beta2_decay-.8,eps(1e-16,1e-3),d1,seed20261112.
Use015normal-clone/tied-alias loader, explicit per-visit nonreentrant activation
checkpointing and optimizer-in-backward accumulated exactly once per selected
leaf. Real selective backward preflight changes NO weights before optimization.
After each step, project each selected tensor's displacement versus E to <=.5%
of max(original L2, sqrt(numel)*.001), then positive normalized visit gains.
Report FP32 mathematical projection and BF16 rounding without pretending every
coordinate must change. No random parameter perturbation or dose search.

No training-loss-based checkpoint search: save final16-step candidate once.
Log losses/coverage and per-family actual gradient presence. Save optimizer/RNG,
full text XOR checkpoint against exact E, per-tensor/part hashes. Frozen tensors
must match all369E hashes. Cold-restore and verify all546text hashes and699finite.
With6.35M trainable values, checkpoint is bounded well below full-model storage;
preserve all prior weight files and archives. Four threads, CPU, offline env-i.

Development/retention candidate ONLY: same8taught HumanEval,8observed MBPP and12
old controls/anchor NLL. Greedy/seed0/thinking-off/cache/eager/BF16/4threads,320tokens
code/64controls, no solutions/private tests in generation. Use ORIGINAL014judges
and unchanged labels. Original/general principal/E existing scores are reused.
Gate to open sealed validation:8/8retained taught tasks; every parent-correct old
control remains correct and total>=10/12; no E MBPP task or test-group loss; anchor
NLL <= principal+.005. Teacher forcing never suffices for this gate.

If the gate fails, record rejection; retain E specialist/principal and leave
all new validation questions unqueried. If it passes, freeze candidate and run
ONCE the8new custom016programming problems and8new general controls against
original,principal,E,candidate under the SAME inference settings. References
passed all3direct-assert groups each and all8None-mutants were rejected before
model outputs. Input-preservation/error behavior tests are also frozen.

New questions are authored custom tests, NOT HumanEval/MBPP aggregate scores.
Ordinary algorithm-family overlap exists, including stack/graph/list skills.
No validation row participates in gradients, candidate choice or hyperparameter
adaptation. Report paired complete-task deltas/statistics and all losses. Even
a positive8-task pilot cannot establish higher intelligence/4B superiority or
justify general principal promotion. Preserve as a promising research candidate
only if it beats E/principal on new task-complete programming without a loss of
their correct cases, retains all new general controls, and meets all development
gates. No follow-up fitting from observed sealed outputs in016.

This is ONE hypothesis and ONE bounded candidate. Source/data/protocol hashes
are committed before training. End with no active model worker and verified
GitHub persistence, not a promise of background improvement.
