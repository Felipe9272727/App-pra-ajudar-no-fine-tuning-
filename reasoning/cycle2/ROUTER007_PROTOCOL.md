# Separate hypothesis007 after completed006, before any new validation output

006 is rejected and parent retained. Its eight-task validation was not opened.
The new user request covers diagnosis and direct edits that can improve thought.
This separate, finite follow-up addresses an architectural limitation identified
by the saved static audit: all48 mHC input-weight tensors are zero and all
parent post-stream bias pairs equal zero. Equal streams enter mHC, symmetric
mixing and equal updates preserve equality. Runtime equality is measured
separately without changing parameters. No dedicated thought neurons assumed.

Use unchanged parent only. Layer25 was the top error-versus-guard activation
contrast in the already completed diagnostic, not selected by new scores.
Change exactly two FP32 entries of its existing mhc_ffn.bias: indices2/3
(post-stream logits) from[0,0] to[-0.2,+0.2]. Output gains become
2*sigmoid(-0.2),2*sigmoid(+0.2), positive with sum2. In exact arithmetic
the immediate stream-mean residual update stays equal to the old update;
streams can diverge before layers26/27 recombine them. This does not imply
learned reasoning or guaranteed preservation after nonlinear later layers.
Existing pre-weights[.25,.75] favour the stream with the larger update.
Both loop visits use the saved bias. All other weights and gains remain parent.

Matched inverse control uses[+0.2,-0.2]. Run it first, then target; the control
can never be selected, even if it scores better. No random edits or dose grid.
Record actual input stream divergence, per-case wins/losses, both checkpoints.
No solutions/expected values/tokens are passed into generation; no gradients.
Keep Loop/mHC, active Liquid, BF16/eager, four threads, greedy160 token budget.

Same six-task31-case screen. Require strict monotone gain vs unchanged parent.
If it passes, evaluate all16 development tasks, four general controls and
12 existing language anchors against paired AND historical gates (1e-6 NLL).
Only then freeze exact candidate hash and unopened validation protocol before
any original/parent/candidate validation. Promotion requires one more complete
fresh task, strict case gain, no lost correct case/control, no worse anchor NLL.
Otherwise keep parent, archive failure. No further weight hypothesis in this
follow-up. Prior001–006 decisions and frozen public scores remain unchanged.
