# Study015 amended attempt B: conservative full-text supervision

The original fixed-lr .01 attempt A was INTERRUPTED after observed training
instability; see ../attempt_a_stop.json and its preserved steps/learning curve.
Its in-memory weights were not saved; do not call them a rejected benchmark
checkpoint or invent generation scores. All old/principal weights are unchanged.
This is an openly amended new trial, not the original fixed protocol claiming
no dose search. The learning-rate change uses ONLY observed training loss.

Hypothesis: relative Adafactor lr .01 applied across pretrained recurrent,
attention, norm, mHC and embedding parameters disrupted the pretrained state.
A tenfold lower relative lr .001 should permit stable supervised adaptation.
This is a hypothesis, not an isolated causal proof. All other optimizer,
precision, data, loss and architecture settings remain the same as attempt A.
All546 text tensors remain eligible; vision153 is frozen. No random weight
perturbations, no new adapters and no parameter subset branded coding-only.

Start afresh from the immutable selected best.pt parent hash
46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8,
not unsaved A and not rejected014. Seed20261112, batch2, max8epochs/32steps,
early stopping at1098/1098 correct answer/EOS tokens and minimum margin .5.
Bounded optimization does not establish a global maximum on these eight tasks.

Training/evaluation data and evaluation protocol are unchanged. Same eight
HumanEval TARGET tasks intentionally taught, same320-token greedy free
generation and original tests, baseline references reused from014. MBPP8 has
been previously observed; use only as diagnostic, never as weight selection
or an unseen final. Controls12 and language-anchor NLL must still be measured.
Keep principal unchanged regardless of target memorization. Save experimental
specialist separately with exact XOR restore, optimizer/RNG and tensor audit.
No model/evaluation process continues after the turn ends.
