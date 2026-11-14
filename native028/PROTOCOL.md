# Native028 — hypothesis and fixed main-model pilot

Authorization: user explicitly asks to apply productive-thinking training to
the MAIN Liquid Sense after current-peer research027. Supervised gradients are
already allowed. Parent GENERAL best.pt SHA256:
46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8.

Hypothesis: verified short planning/checking/repair examples in both native
thinking modes, conservative shared-block adaptation and parent retention may
improve delivered correct programs without damaging general instructions.
Do not equate trace length with intelligence or two visits with useful checking.

Scope: physical layers4..27. Deterministic rank8 factors on nn.Linear weights
except selected direct controllers. Initialize A with orthonormal DCT rows and
B with zero; initial effective delta is zero. Train A/B and the276control tensors
of025excluding its16dense exits. This includes mHC, conv7,DeltaNet decay/input
gates,norms and visit gains. Base linear weights,embedding/head,outer layers and
vision stay frozen during optimization. Low-rank exit updates open formerly
zero exits; measure delayed upstream gradients rather than assuming all gradients
are nonzero at initialization. Both actual visits share factors and controls;
use the verified explicit-visit nonreentrant checkpoint wrapper.

Training preserves BF16 backbone arithmetic and FP32 routers/gains. Factors,
optimizer and controller master copies are FP32. Initial zero-adapter parity
and no-update backward checks must pass. Native controls are copied to their
original runtime dtype after updates. Only finite gradients, normclip1.
Trust regions:1%relative Frobenius per factor-merged projection and0.5% per native
controller, with RMSfloor0.01for zero/tiny tensors. Gain projection keeps a
positive normalized two-entry vector. Check effective BF16 export constraints
before scoring; deterministic projection is not benchmark-based dose selection.

SFT:32verified code problems,12general problems,4tool examples, each shown with
thinking and nonthinking prefixes:96assistant-target conversations,48paired
updates/epoch,two epochs/96updates. Only assistant target tokens get CE.
Twelve separate retention anchors provide parent top32token probabilities plus
the complement mass on their teaching prefixes. This is coarse KL, not full
logit distillation from a larger teacher. Each update averages its two teaching
losses and adds0.3*anchor KL. AdamW factor lr0.0002/controller lr0.00005,
10step warmup,cosine to0.25,no weight decay. Save epoch1andSFTfinal.

Policy stage:8fixed TRAIN code prompts,4samples/group,temperature0.8,full-vocabulary
sampling,128new tokens,seeded. No references/cases in rollout prompts. Execute
delivered final code through the existing sandbox. Reward =0.75*all_pass+
0.25*case_fraction, minus0.05*length/128onlyifall_pass, minus0.1if no delivered
think closure, minus0.05if cut off without EOS. Normalize group advantages.
Zero reward variance => record and skip that group, never pretend an update.
For nonzero groups: one clipped group-relative PPO update,clip0.2, factor lr
0.00002/controller lr0.000005, plus0.1*parent anchor KL. Record cached behavior
logprobs and full-sequence replay ratios before updates; numerical train/infer
mismatch is measured, not assumed absent. This small policy pilot is not full
DAPO/GRPO infrastructure or multi-teacher OPD. Save final factors/controllers/
optimizer/RNG even if no policy group updates.

Export/restore: low-rank deltas fold into native BF16 matrices; save authoritative
controller runtime values and exact merged hashes for all699tensors. The saved
factor representation is lossless construction state, not a claim of bitwise
equivalence between additive training arithmetic and folded inference. Score
only the folded native checkpoint. Restore cold and verify all699hashes.

Validation: original Qwen,parent,SFTfinal,policyfinal. New4code tasks+8general
controls in nonthinking mode; same4code+first4general in thinking mode. Greedy,
same prompts,tokenizer,4threads,BF16/native cache,dualEOS248044/248046. Budgets:
128code/48general without thinking;192total with thinking. Strip only actual
think delimiters before judging final output; unfinished thinking is failure.
Record syntax,fulltask/case correctness,completion,repetition,tokens/time.

Candidate eligibility requires strictly more total completed code tasks across
the two modes than parent, no loss of any parent-correct code case or general
control in either mode, and no fewer completed tasks in either mode. Tie-break
by tasks,cases,then lower generated-token count,then earlierSFTstage. No selection
using teacher-forced loss. Qwen is a reference, not a substitute parent gate.

Only a frozen eligible winner opens sealed final4newcode+4general in both modes,
compared once to parent and original. Final promotion requires another strict
completed-code gain and retention of every parent-correct final case/control.
If no eligible winner, final stays unused and parent remains selected.

Causal loop diagnostic after selection is fixed: parent versus selected winner,
or policyfinalifnone,on first2validation code tasks,thinking mode. Replace only
the SECOND layer27exit by saved FIRST exit, still executing all56visits. Compare
program/case bits; activation change alone is not useful-loop evidence. This
diagnostic is not a cheaper deployable one-pass model.

Two new tool probes are descriptive Python tool-use checks, not BFCL or a claim
of internet reliability. They are run once per variant after core validation,
with the same tool schemas/actual executor. No tool gains override a failed
code/general preservation gate. No new APK or overwrite of immutable best.pt.
Validated research candidate may be selected separately; preserve prior main.
No large-model or general-intelligence claim from this pilot. Archive everything
and close workers. Prior025/026and sealed013/016/RSI100sets are not rerun.
