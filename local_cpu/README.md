# Local CPU continuation

The assistant moves the existing finite weight search to its local CPU runtime.
Base: Qwen3.5-0.8B, active hybrid about 1.02B loaded parameters; existing Loop/mHC
and Liquid-inspired operators remain active. No gradient training, reference
solutions in prompts, or new model-quality claims.

Measured environment: 8 CPU quota, 8 GiB RAM, no GPU. Three unchanged tasks took
33.028s with four threads and 34.163s with eight, with identical generated outputs.
Peak process RSS was 2.591 GiB. Chosen search setting: four threads. Compare
benchmark_result.json with the committed GitHub runner calibration; these are
single timing trials on observed tasks, not accuracy gains.

The pinned upstream weight SHA256 was verified. PyTorch 2.15.0+cpu and the same
pinned Transformers/runtime packages are installed in an isolated virtualenv.
The local judge passed syscall-denial, correct/wrong-code, prohibited-import/file
access and infinite-loop timeout checks; the complete suite passed 35 tests.

controller.py runs engine chunks and later fresh validation/final phases.
publisher.py blocks each publication until coordinator.js commits via the user's
connected GitHub tools and checks the branch head. Connector credentials stay
outside the inference process. Checkpoint publication uses no force push.

The remote jobs were canceled before local mutation. The original search branch
contains a migration pointer; all ongoing decisions live on this branch. At
completion the coordinator can fast-forward the original search branch only if
its migration lease is unchanged. This transient session is not a permanent
training service.
