# Recovery of hypothesis 002 — 2026-11-04

Verified source: `45b51522a1d7b2d8bbed464da97cff1291362969` on
`codex/liquid-sense-mentor-20261104`. All 11 repository branch heads were
enumerated; the mentor tree has no `mentor/checkpoints/negative_002.pt`.
There are no releases and no Actions run for the mentor branch. Recent
recovery Actions artifacts were empty. The coding-run artifacts predate this
hypothesis. The current local environment was empty, with no prior processes.

The saved trial has only the completed overlap_count screen: parent 2/5,
matched random 2/5, candidate 5/5, then `screen_passed_measuring_full_parent`.
Its `model_process_active: true` is stale. The claimed full scores 11→12 tasks,
69→72 cases and 4/4 controls are conversation evidence, not a saved result.
Do not credit them until independently recovered. Legacy search actually has
31 saved rejections and zero accepted edits (not 30 rejections).

Verified parent: `rsi100/checkpoints/best.pt`, SHA256
`46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8`.
Verified old trial source SHA256:
`3115a908681bc80eea2a9237cbe2522b35717b04c119d17d709f6ffb2321f4a3`.
Historical parent has 11/16 complete tasks, 69/81 cases, 4/4 controls,
anchor NLL 3.1837292512257895.

Only unfinished work is replayed: recover the SAME predeclared 0.012 edit
from actual cached generation, assert exact parent tokens against the saved
trial, save the candidate and directions before lengthy evaluation, and run
resumable full paired/historical retention. Do not repeat 31 rounds, trial 001,
the completed random screen, or change the hypothesis/dose from feedback.
No bitwise identity claim is possible for an unsaved candidate.

The only edited tensor is
`model.language_model.layers.31.mlp.down_proj.weight` (donor Qwen layer 23).
For preceding activation rows P and faulty-step activation h:
v = normalize(h - P.T (P P.T + lambda I)^(-1) P h),
lambda = 1e-5 mean(row_squared_norm(P)); u is the normalized existing
unembedding row of the student's bad token 2343 (` len`).
W' = BF16(W - 0.012 ||W||_F u v.T).
This is a negative-only intervention, without a correct replacement token,
gradient, optimizer or runtime adapter. Other checkpoint tensors must be equal.

Runtime: pinned upstream revision and SHA256, Torch 2.15.0+cpu,
Transformers 5.22.1, four inference threads, greedy 160 tokens, thinking off,
same prompt and cache path. This machine has only 2 CPU quota and 8 GiB RAM;
timings are not comparable with the old machine. Keep architecture checks.
Evaluate generated code only using the existing syscall-filtered AST judge.

After recovery, freeze the checkpoint hash before any new validation output.
Use new project tasks with hidden offline oracles, all three model variants,
identical inference settings, per-case regression reporting and paired
task-level uncertainty. Near-transfer overlap tasks must be reported separately
from other programming tasks. No claim of pretraining novelty is possible.
No edit selection uses this validation. Preserve all prior files and parent.
Save every completed phase on GitHub before ending the turn; a local process
is not a durable background service.
