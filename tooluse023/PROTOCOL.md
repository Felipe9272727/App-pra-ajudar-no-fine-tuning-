# Study023 — native-cache supervised tools from the preserved general hybrid

022 is rejected: exactE0/4new tool tasks, readout adapter0/4, original3/4 by
automatic lookup/calc criteria. Qwen also adds one false API description, so
the small automated score is not a full factual-quality measure. No022candidate
promotion. Keep its exact weights, optimizer,631teacher states and all outputs.

Hypothesis023 changes two identified limitations: start preserved general
best.pt (independently selected by prior general retention, NOT by these new
test outputs), and use actual cached generation states for supervised replay.
Full-prefill teacher features can disagree with cached generation in this
hybrid (previous011diagnostic). This is a hypothesis, not a confirmed cause
of022failure. Neither model has dedicated identifiable 'thinking weights'.

Reuse the same eight tool-teaching traces/16assistant targets as022; only correct
targets and actual observations in TRAINING. No022fresh question/answer enters
teaching. Teacher replay forces its labels only during collection, never
scoring. Collect actual last-layer MLP inputs x, residual r and normalized
hidden states at every teacher decision through model.generate(use_cache=True).
First-prefix full prefill plus subsequent token cache matches its normal
generation path. Record source argmax/margins and verify readout reconstruction.

Keep all Loop/mHC/temporal operators active and frozen. Fit a rank32 update
to physical31.down_proj: W_eff=BF16(W+B@A). A is the top32PCA directions of
teaching x, deterministic Gram eigendecomposition; B starts0. A32x3584 and
B1024x32 are147456new factor values,32768of them gradient-trained. Save both
factors, optimizer and exact BF16 merged matrix. This is a supervised low-rank
weight edit; deployment may absorb factors, so do not advertise a1.2Bmodel.
No claim of joint controller retraining or new learned neural-loop depth.

Maximum32AdamW updates, lr.0003,seed20261123,weight_decay0. Loss is squared
hinge on the real full-vocabulary gold-minus-highest-other-token margin, goal.5.
Rescan all631native teacher decisions after each update. Gradient uses the
selected embedding pair; BF16 conversion uses autograd's usual surrogate.
Project B to enforce ||B@A||F<=.01||W||F (A rows orthonormal), no other dose
search. Stop early only if all teacher margins>=.5. Cache reconstruction
must have>=.99argmax agreement and max hidden error<=.0625 before training.
All other698old tensors remain bitwise unchanged; parent best.pt untouched.

Screen on the four already-observed022tool questions, labeled DEVELOPMENT,
parent and candidate, same original022runtime256tokens/turn,2calls,greedy,
seed0,thinkingFalse,4threads,4096context. Candidate needs more correct finals,
no loss of any parent-correct task, and no new false tool-execution claims.
Preserve same12raw general controls and old parent-correct coding cases with
the original budgets/judges. If a screen fails, reject; do not query sealed
fresh tests or change this fixed dose/data to fit the screen.

Freeze four NEW tool questions and graders before model generation or updates:
two changed computations, a different Python API lookup and a Go API lookup.
If screen+retention pass, one locked original/parent/candidate comparison on
these four with the same tools/runtime. Solutions/private test data never in
inference; real stdout/URLs only. Keep automatic criteria and manual claim
audit separate, report truncation and live search drift. No statistical or
larger-model superiority claims from this small custom pilot.

Android tooling022 is implemented/compiled (Rust+JavaDEX+isolated MicroPython),
but no new Tools APK has been released or claimed validated. Integrate only
eligible weights with separate Base/Specialist options and verified provenance.
Keep the released specialist021APK and all earlier APK bytes/checkpoints.
