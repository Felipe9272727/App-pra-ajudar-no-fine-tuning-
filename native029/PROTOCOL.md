# Native029 — four more research epochs on the selected best

Authorization: user “Treine o melhor+4 épocas”. The selected best remains the
MAIN general checkpoint rsi100/checkpoints/best.pt, SHA256
46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8.
028SFT/PPO were rejected, so four new epochs start from this preserved parent,
with fresh AdamW rather than claiming six accumulated epochs on a failed model.
No prior trial is restarted, overwritten or erased. RAM archives from028were
cleared by the environment between turns; their verified Git copies remain.
Only the intact selected parent and pinned base files are required here.

Four epochs/192paired updates, same verified48teaching problems, two mode views
per problem,2699label-token presentations/epoch and10796total. Same12retention
anchors and cached parent top32+other probabilities, verified by SHA. Reuse of
the successful historical backward/zero-delta preflight is technical provenance,
not new training or newly collected teacher data. Actual first-step finite
gradients and699parent hashes must still pass in this run.

Scope and math remain028: rank8DCT/zeroBinitialization on150projections,276native
controllers, BF16backbone plus FP32factor/master states, shared physical blocks
on both real visits.32physical/56executions,mHC2,conv7,local256. Gradientclip1,
projectiontrust1%,controllertrust0.5%,RMSfloor0.01, strict actual-BF16export bound.
To reduce prior forgetting: factorlr5e-5,controllerlr1.25e-5 (one quarter028),
coarse-parent-KLweight1.0 (versus0.3),10warmup steps, cosine to0.25over192updates,
seed20261114029. These are deliberate additional changes, so results cannot be
attributed to epoch count alone. Save initial and all4epochs, optimizer/RNG,
rolling state every update, all699native-folded hashes. No PPO in this study.

Freeze sources/data/protocol before learning. Complete all4epochs before seeing
validation outputs. Evaluate original Qwen,selected parent,epoch01..04with the
same native-folded BF16greedy4thread inference, context,tokenizer and dualEOS.
New validation:4code families(chunks,anagramgroups,slidingmax,graphcomponents),
20cases,8general controls without thinking; same4code+first4general with thinking.
Budgets128code/48general,192total with thinking. Unclosed thought has no final.
These short-budget scores do not establish extended-thinking or4Bsuperiority.

Observed retention:028's4code/8general nonthinking probes, clearly labelled
legacy, not an independent benchmark. Replay parent once in this NEW study;
compare its outputs/case bits to the saved028parent to detect numerical drift.
Do not rerun to obtain a preferred baseline. If drift exists, stop promotion.
Evaluate each epoch on the same legacy probes; retain every parent-correct case
and general control. The new validation cannot mask known prior regressions.

Eligibility: strict gain in total completed NEW code tasks across both modes,
no fewer tasks in either mode, no loss of ANY parent-correct new or legacy code
case or general control. Rank eligible epochs by tasks,cases,lower tokens,then
earlier epoch. Loss cannot select a checkpoint. Freeze the winner once.

Final: the unqueried028final4code+4general is inherited as RESERVED final, its
original bytes preserved, not used in teaching/selection. It has never received
project-model inference. Only an eligible frozen winner opens it, once each for
original,parent,winner, both modes, same budgets. Promotion requires another
strict completed-code gain and per-case/control retention. If no winner, keep
final closed and parent selected. Preserve rejected snapshots, all outputs and
reports; no automatic APK/default replacement. Close all model workers.
