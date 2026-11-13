# Spec026 — from-scratch native hybrid drafters
- User explicitly authorizes creating a NEW small AI from scratch as speculative
  part of Liquid Sense, studying speed, standalone quality and size/efficiency.
- This supersedes design-only/no-random-initialization limits of study017 FOR
  new child models only. Never perturb target or resume rejected025training.
- Same active text family:32physical/56visits,Loop4..27,mHC2,DeltaNet/conv7,
  selected256windows. Scale widths; omit unused vision. Same tokenizer/vocabulary,
  tied embedding; NO pretrained teacher tensor copied into children.
- Create and train18M/95M budgets; preserve seed/config/initial/final checkpoints.
  Report finite training corpus/steps. Initialization is not learned capability.
- Main target is immutable GENERAL parent46f6697..., not rejected025epochs.
- Greedy-only verified speculation. Measure all draft/prefill/block/rollback/
  correction costs. Serial checking cannot yield speculative acceleration.
- Cached GDN block path must be correct,56slots rollback safely. Gate block
  candidate on target token agreement against serial reference. Finite probes
  do not prove bitwise/universal/Android equivalence. Never claim SGLang/DSpine.
- Standalone task correctness is separate from next-token alignment/acceptance.
  Training labels allowed only in teaching; no golds in benchmark prefixes.
- Use4threads, single orchestrated worker,8GiB/2CPU. No paid GPU or phone claim.
  Preserve existing files and all negative results; no worker left at final.
