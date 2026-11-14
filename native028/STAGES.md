# Policy and evaluation implementation freeze

This addendum fixes remaining implementation details before policy updates or
any validation generation. The initial SFT source/data freeze stays unchanged.
Policy source freeze is `frozen_policy.json`; evaluation source freeze is
`frozen_evaluation.json`. Both include their added dependencies. Models are
run singly; no paid compute and no changes to the Android app.

Policy uses the first eight already fixed TRAIN code rows, thinking prefixes,
32 independent reproducibly seeded full-vocabulary samples, including EOS in
the sequence likelihood. Its additive training arithmetic and cached versus
full-prefill BF16 replay may differ; record ratios before any clipped update.
No policy learning uses validation cases or golds. Partial sampled groups save
every completed sample. Policy optimizer/RNG and completed-group state are
saved after each group. A partial state must be investigated before `--resume`.

Code scores use the unchanged syscall-filtered canonical judge. For syntax or
contract rejection before execution, its existing `passed=0` has no case bits;
the evaluation record explicitly derives all-false bits for retention comparison.
This does not change any score or repair a program. An unfinished thinking trace
has no delivered code. Completion, repetition and token use remain descriptive.

Two Python probes use the exact compact teaching system and run_python schema.
All models get nonthinking prefixes, 128 output tokens per turn, three turns and
at most two model calls per probe. A fixed prior error on the second probe is
actually executed before model generation. Success requires a valid actual
model-initiated Python execution plus the requested numeric-only correct final;
integers or equivalent decimal representations are accepted uniformly. Actual
observations are projected to tool/ok/stdout/error as in training. No web calls,
fabricated execution, protocol repairs or automatic model-specific retries.

Selection's command is `run_clean.py evaluate --select`; the filename `decide.py`
avoids shadowing Python's standard-library select module. The loop diagnostic
compares its two outputs to the already saved matching normal validation rows;
normal rows are not generated again. Replacement retains all56 computations,
so it cannot demonstrate a cheaper architecture or an inference speed gain.

A separate cold native load for scored candidates checks all699 merged hashes.
The initial representation and epoch1 are construction archives; cold verification
may be run without generation after all learning, one model at a time. Export
hashes and trust bounds do not imply skill gains. Parent remains selected until
both independent, strict preregistered gates pass. If validation fails, sealed
final is not queried and cannot be used to tune the next candidate.
