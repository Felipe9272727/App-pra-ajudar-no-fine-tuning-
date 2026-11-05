# Paired diagnostic extension, fixed before1024-token outputs

The original's completed512-token thinking diagnostic has one final answer,
while two outputs reach the cap without closing thinking. This cannot decide
whether the model would finish. Extend *every* capped thinking-on diagnostic
row, in both original and unchanged parent, to1024 greedy tokens. No selection
by correctness. Reuse uncapped completed outputs, which already terminated
before either budget. Never change prompts, answers, weights or grading.

This is a separate, observed diagnostic, not a fresh benchmark or weight gain.
Compare thinking512 versus thinking1024 to isolate output budget. The original
512 off/on factorial remains unchanged. Do not claim a matched off/on1024
comparison: off1024 is not run. No output is used as a positive target.
Capture exact token IDs and check that the first512 generated IDs/text equal
the prior capped row. Stop at1024, even if no final answer. Report completion
separately from correct arithmetic mentioned inside unfinished thinking.
