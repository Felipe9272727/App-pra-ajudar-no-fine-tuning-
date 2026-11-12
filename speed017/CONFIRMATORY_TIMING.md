# One fixed confirmatory timing replication

Initial exploratory four16-token pairs showed ratio1.122x with paired p=.125
and a95%difference interval including zero. Do not pool, replace, or discard
those measurements. The result is unresolved, not confirmed speed benefit.

Before any new timing run, freeze one replication: THREE new serial processes,
each using the unchanged bench `time` mode (two warmups, then four ABBA-ordered
pairs of the same16token IDs). Twelve new pairs total; all must be included.
Four threads, same weights, machine and immutable executable. Wait until all
PyTorch model workers finish. No further replication or stopping based on p.

Primary analysis: paired mean time saved, two-sided exact sign-flip test over
all2^12sign assignments; paired95%t interval with11degrees of freedom. Claim
confirmed cloud-CPU backbone benefit only if p<.05 and the lower interval bound
is positive. Report ratio of all reference/optimized means and every pair.
No phone, vocabulary-readout or overall app-speed extrapolation. This resolves
an existing uncertainty with a separately registered test; no new code/weights
or quality-selection criterion. Publish null/negative outcomes too.
