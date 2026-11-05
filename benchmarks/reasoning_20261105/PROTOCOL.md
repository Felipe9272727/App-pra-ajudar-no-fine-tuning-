# Frozen public-benchmark pilot

Use benchmark families documented by Liquid AI: LiveCodeBench v6 and IFEval
(LFM3 model card), GSM8K (LFM2.5-1.2B-Thinking announcement). This is an
independent, bounded CPU pilot on official-source subsets, not a reproduction
of the vendors' full vLLM/temperature/context/agent protocols or leaderboard.

Data and source revisions are fixed in sources.json. Select IDs by SHA256 of
the fixed seed 2026110501 and each original ID, before any benchmark inference.
- LiveCodeBench release_v6: eight easy AtCoder stdin/stdout problems from the
  test6 increment included in release_v6. Remove publisher sample-I/O sections
  from the model input to honor the no-test-answer requirement. Score only up
  to 16 private cases/problem selected by the same seed; preserve their original
  expected strings. Strict whitespace-normalized stdout matching, no numerical
  tolerance or manual repair. This restricted private-case subset is not the
  full canonical LiveCodeBench score. Generated programs run only in a
  seccomp worker with CPU/memory caps and allowlisted standard-library imports.
- GSM8K: 16 original test questions. No reference reasoning, demonstrations or
  worked solutions in the prompt. Ask only the final numeric answer. Score the
  original #### numeric target, exact numeric equivalence; ambiguous final
  lines are wrong. This zero-shot concise-answer variant is not a 5-shot CoT run.
- IFEval: 12 official prompts with one short, verifiable instruction from the
  preregistered lightweight whitelist in build_data.py. Use the official Google
  strict and loose instruction checker, unmodified and pinned. This filtered
  subset is not the full IFEval score. No reference output is put in the prompt.

Original Qwen and the selected hybrid use the same question/context/template,
BF16/eager kernels, greedy decoding, seed 0, use_cache=True and four threads.
Thinking tags are disabled for the matched raw comparison; increased latent
loop contribution is evaluated in the authored weight trials. Code budget 384,
GSM8K 64 and IFEval 192 new tokens. Report caps, generated text and per-case
outcomes. Branding prompts are excluded. Hybrid FLOPs exceed original Qwen.
Report CIs at task level, not treating correlated private cases as independent.

Freeze hashes and selected model checkpoint before observing these outputs.
No public-benchmark result chooses a new edit/dose. No post-hoc gold/alias,
case filtering or judge changes to obtain better scores. Dataset membership
does not establish absence from Qwen pretraining. No tools/answers are supplied
to the model; hidden oracles are only used offline for grading.
