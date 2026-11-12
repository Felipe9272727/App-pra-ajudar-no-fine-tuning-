# Speed019: exact zero-projection multiplication shortcut

New runtime hypothesis after018's structural audit; NO additional weight training.
Source: speed017/runtime. Its completed/confirmatory results remain immutable.
Source checkpoint principal46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8.

Exactly16BF16 output matrices contain only positive/negative zero bits,46,137,344
values total. At load, inspect matrix bytes, never infer zeros from names. On
AVX2 or NEON, the reference dot starts positive-zero accumulators. With finite
inputs, multiplying these matrices yields positive zero in every row, exactly.
Return that result directly for proven-zero matrices. Keep reference fallback
on scalar architectures and nonfinite inputs; preserve propagation behavior.

Do NOT skip a physical/virtual layer, temporal state/conv update, router merge,
normalizer or MLP input projection. All32physical/56visits and allcache states
must remain active and bit-identical. No parameter/payload or template changes.
Baseline optimize=false vs all approved prototypes+new shortcut optimize=true.

Before adoption: tests for signed-zero/SIMD behavior,16-token complete hidden,
conv/recurrent/KV/logit comparison, three chat-token equivalence probes. Expect
16proven zero matrices and32shortcut hits per token, never fewer virtual states.
Measure one fixed12-pair backbone timing (three processes, each warmup+fourABBA
pairs) ONLY after model workers and speed017confirmation finish. Include every
pair; no stopping/repeating on p. Primary two-sided exact sign-flip and95%paired
t interval; claim CPU benefit only if p<.05 and lower interval>0. No Android
phone claim or new APK without ARM build/device checks. No further runtime
hypotheses in this bounded work packet regardless of outcome.
