# Retomada do experimento

## Latest user authorization — supervised015

- User explicitly selected "Usar treino supervisionado com gradientes". See
  supervised015/authorization.json. This supersedes the earlier no-gradient,
  no-backprop and algebraic-only restrictions for the requested supervised
  specialization. Do not ask for the same method authorization again.
- Aim: maximize the previously measured eight HumanEval tasks. All546 active
  text tensors/919659696 unique parameters are eligible, including loop/mHC,
  attention, MLP, embeddings and temporal operators. Vision153 stays frozen.
  Do not claim any exclusively programming-only weight subset is known.
- Parent is unchanged best.pt hash46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8.
  Never start from rejected014. Keep benchmark-specialist snapshots separate
  from the general selected checkpoint, and label all taught-set scores.
- Native inference loaders create inference tensors; use the normal-clone,
  alias-preserving training loader and explicit per-visit checkpoint contexts
  in supervised015/train_runtime.py. Both real backward preflights passed
  without changing parent weights. Read status/protocol before restarting.
- Archived studies' frozen AGENTS hashes apply at their recorded commits;
  this new authorization does not rewrite those historical source snapshots.

## Latest instruction and study013 — supervised review (2026-11-11)

- User now explicitly allows correct answers for TEACHING. Historical bans on
  reference solutions do not apply to learning in review013. Keep solutions,
  expected cases and feedback OUT of evaluation prompts. No silent SFT/LoRA.
- Start from unchanged best.pt hash46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8.
  Read review013/PROTOCOL.md, status.json and frozen.json before any inference.
- Study012 and mentor002 independent validation are COMPLETE/rejected; do not
  repeat them. The empty old review-loop branch contained no013 experiment.
- Study013 learns new rank16 second-visit adapters by closed-form supervised
  embedding steering. Actual gold programs only120 train tasks; no gradients,
  backward pass, optimizer or full-model fine-tuning. Test families stay closed
  until the frozen screen/full-validation gates pass. Preserve every artifact.
- DSpine concerns acceleration; no skill gain can be inferred from its speed.

- No novo piloto, leia primeiro `lab_rsi/status.json`, `lab_rsi/archive.json`
  (quando existir) e `lab_rsi/frozen.json` (quando existir). O primeiro piloto
  em `rsi/` é histórico e não autoriza desligar partes da arquitetura atual.
- Requisito do usuário: manter SenseNova loop/mHC e os componentes Liquid
  ativos em todas as novas candidatas. Use `lab_rsi/common.py:architecture_check`.
- O nome atual é `liquid sense 0.8 b LOOP`; informe que a base nominal é 0,8B
  e o híbrido ampliado tem aproximadamente 1,02B parâmetros carregados.

- Leia `rsi/status.json`, `rsi/pending.json`, `checkpoints/incumbent.json` e a
  última rodada antes de rodar inferência. Não repita rodada finalizada.
- O pedido atual é edição direta dos pesos com adaptação algébrica e feedback;
  não usar backpropagation/otimizadores de gradiente sem nova instrução do usuário.
- O assistente é o controlador. Sugestões reais do modelo devem ser preservadas
  como saíram; não inventar sugestões ou alegar autonomia que não ocorreu.
- Propostas são avaliadas em desenvolvimento. Não promover pesos por resultado
  do conjunto reservado. Depois que o teste reservado for observado, uma nova
  pesquisa precisa de outro teste final ainda não usado.
- Salve rodada, checkpoint incremental e estado no GitHub após cada decisão.
  Confirme o commit/ref antes de afirmar que foi salvo. Não usar force push.
- Compare sempre com o original sob o mesmo protocolo. Descreva as partes LFM3
  como inspiração compatível, não como o modelo Liquid completo.
- Campos `pending` e `status` devem refletir a execução real; não afirmar que um
  processo continua rodando depois de encerrado.
- O fluxo GitHub está em `.github/workflows/liquid-sense-benchmark.yml`.
  Use somente runners padrão públicos, até quatro máquinas de avaliação,
  quatro threads por máquina. Não habilitar cobrança ou runners maiores.
- Leia os jobs/artifacts antes de retomar um fluxo incerto. Depois de congelar
  e observar o teste, não reabra a seleção com esse mesmo teste.

## Ciclo 2 ativo

- A branch `codex/liquid-sense-rsi-cycle2-20261104` continua o híbrido ativo
  do commit `86e3f6b22a7e809e23883bd982e54523225c0478`, sem a V3.
- O piloto anterior está em `history/` e na branch original; não usar seus
  conjuntos observados como teste final deste ciclo.
- Fluxo atual: `.github/workflows/liquid-sense-rsi-cycle2.yml`.
- `lab_rsi/PROTOCOL.md` e `data.json` fixam três etapas e critérios antes
  dos resultados. Não reabrir seleção depois do teste final.
- Não promover edição só porque baixou NLL. Exigir geração correta e
  preservação dos controles, conforme `protocol.validation_passes`.

## Programação: ciclo atual separado

- A branch `codex/liquid-sense-code-rsi-20261104` contém o pedido mais recente:
  programação, edição literal dos pesos, feedback sem soluções prontas e
  teste opcional de mais loops. Leia `code_rsi/status.json`, `archive.json`
  e `frozen.json` quando existirem. Os diretórios anteriores são históricos.
- Protocolo fixo em `code_rsi/PROTOCOL.md`; workflow
  `.github/workflows/liquid-sense-coding-rsi.yml`. Gates e caches permitem
  2/3/4 passagens, mantendo ambas as famílias arquiteturais ativas.
- Não enviar valores esperados, referência ou tokens-alvo ao modelo de adaptação.
  Sinais permitidos: ativações próprias, status de execução e fração aprovada.
- Não afirmar causa interna única a partir de correlação de ativações.
- Código gerado só roda no executor isolado; não dar credenciais nem montagens.
- Não alegar melhor modelo pequeno com este piloto customizado.

## Pedido mais recente: 100 tentativas com rollback

- Branch `codex/liquid-sense-rsi100-20261104`; estado em `rsi100/status.json`.
  Leia `rsi100/PROTOCOL.md`, `best_metrics.json` e `frozen.json` quando existirem.
- São 100 rodadas de busca por recompensa sem gradientes, não 100 passagens
  internas. O bloco continua com 2/3/4 passagens positivas e Liquid ativo.
- Descartar candidatas com qualquer perda de casos corretos ou qualidade medida.
  Restaurar o melhor peso e preservar sua cópia, com commit após cada decisão.
- O currículo observado pode ser otimizado repetidamente; novos conjuntos de
  validação e teste não podem participar das 100 decisões de busca.
- Workflow `.github/workflows/liquid-sense-rsi100.yml` aguarda o anterior para
  respeitar o limite de quatro máquinas. Não disparar outra cópia em paralelo.

## Local CPU continuation

- Active continuation: branch codex/liquid-sense-local-cpu-20261104. The remote
  search and its waiting follow-on were canceled before local weight search.
- Local environment: CPU quota 8, RAM 8 GiB, no GPU. Use FOUR inference threads:
  three unchanged tasks took 33.028s at 4 versus 34.163s at 8, identical outputs.
- Retain direct algebraic weight edits only, both architectural components, the
  paired AND historical acceptance gates, and unseen validation/final isolation.
- local_cpu/controller.py runs the existing engine through local_cpu/runner.py.
  Generated code uses the same AST judge in a credential-free subprocess with
  capability clearing, deny-by-default seccomp and finite CPU/memory limits.
  This is a distinct execution environment, not a Docker run.
- local_cpu/publisher.py pauses after every completed decision. The assistant's
  local_cpu/coordinator.js uses connected GitHub tools, verifies branch SHA and
  acknowledges only after durable commit. Never claim unsaved rounds or gains.
- Runtime credentials must not be given to the model process. Do not duplicate
  a round already saved. Runtime scratch/cache files are not durable checkpoints.
- The finite continuation ends after 100 rounds, fresh validation and original
  versus hybrid final evaluation; it is not autonomous recursive self-improvement.

## Latest user steering: assistant-guided research

- The fixed automatic 100-round loop is PAUSED after 31 saved rejections.
  Do not restart cell 43 or local_cpu/controller.py without reconciling state.
- Active new branch: codex/liquid-sense-mentor-20261104; read mentor/status.json,
  mentor/PROTOCOL.md and mentor/hypothesis_001.json.
- The assistant authors each hypothesis from real semantic errors, own token
  traces and controlled interventions. No correct solution/target token in the
  student's input, no gradients, no claim of autonomous RSI.
- Token/logit diagnostics are not quality gains. Full paired/historical retention
  and unseen validation remain required. Review each result before proposing
  another edit; budget initially four authored hypotheses.
- Keep old Loop/mHC + Liquid operators, all original checkpoints and logs.

## Local execution durability correction

- Local files/processes and functions.exec cells were lost between turns.
  An active local process is not a durable background training service.
- Before ending a turn, finish the current local subtrial and verify its outcome
  commit on GitHub. Never promise that a local search continues between messages.
- On resumption inspect durable branch head and records first. Missing local
  outcomes are unknown, not improvements or completed trials. Recovery replays
  must be recorded explicitly; do not repeat decisions already durably saved.
- Current recovery journal: mentor/recovery_003.json, same predeclared trial 002.

## Recovery and independent validation 004

- Latest continuation: `codex/mentor002-independent-validation-20261104`.
- Read `mentor/RECOVERY_004.md` and `mentor/recovery_004/frozen.json` first.
  The prior commit saved only screening; its claimed full gain was unpublished.
- `negative_002_recovered.pt` is a reconstruction of the fixed hypothesis,
  not proof of bitwise identity with unsaved weights. Never conflate the two.
- Run only missing phases in `mentor/recover_004.py` and locked three-way
  `mentor/validation_004/evaluate.py`; results checkpoint every completed row.
- Validation protocol and hashes must be committed before observing outputs.
  No tuning or new hypotheses use this test; no new 100-round loop is authorized.
- Preserve old best unless all declared gates pass. Commit outcome before
  ending the turn; no promise of local work continuing between turns.

## Reasoning continuation 2026-11-05

- Active branch: codex/liquid-sense-reasoning-20261105. Read reasoning/status.json and reasoning/PROTOCOL.md.
- Start from preserved best.pt; hypothesis 002 remains unpromoted.
- Finite hypotheses 003/004/005 (005 was preregistered after the null 003 result): actual decoding activation diagnostics, direct loop-gain edits and a separately protected negative-only dense edit. No dedicated thinking module is assumed.
- Keep previously observed validation_004 out of selection and freeze new benchmark subsets before their outputs.
- User requested honest Liquid Sense identity and original-versus-hybrid tests on benchmarks used by Liquid AI. Branding stays out of raw benchmark inputs and is not a weight-quality claim.

- Current cycle: all three new hypotheses completed without promotion. Public benchmark generation is a locked audit; do not change weights, source judges, answers or selected IDs after its outputs. Resume only missing rows from benchmarks/reasoning_20261105/results_*.json.

## Latest error-analysis continuation — 2026-11-05

- Branch `codex/liquid-sense-error-analysis-20261105`; read
  `reasoning/cycle2/status.json`, `selection.json`, `ERROR_ANALYSIS_REPORT.md`
  and the cycle's protocols before inference. Earlier statuses are historical.
- 006 is complete: 69→70/81 development cases, 11/16 tasks unchanged, 4/4
  controls, but anchor NLL 3.183729251→3.185465773; rejected. 007 is complete:
  two FP32 post-stream bias values separate mHC streams, but target/inverse
  both remain 25/31 screen cases; rejected. Do not repeat either decision.
- Retain the unchanged best.pt parent hash 46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8.
  Original paired development is 12/16 tasks, 66/81 cases versus parent 11/16,
  69/81: partial-case gains are not unambiguous superiority.
- Static and actual generation audits show 48 zero input-weight router tensors
  and exactly equal parent mHC streams in 201312 measured router calls.
  Structural presence is not learned conditional routing or a thought module.
- The public 36-task pilot and the new 3-task thought-budget diagnostic are
  OBSERVED, not fresh final data. Keep original judges/golds/frozen files.
  Corrected AST scoring is a separate audit and changed no old LCB totals.
- All 512/1024 diagnostic rows are complete; do not repeat them. At 1024,
  original completed 2/3 correct finals versus hybrid 0/3; both hybrid math
  traces calculate correctly but repeat invented/metatext instructions.
  Weight selection is locked to parent independently of those outputs.
  No live worker should be promised after a turn ends; all were finished.
- RSI100's eight validation tasks remain unconsumed because neither new edit
  passed development. Any future candidate needs a new preregistration and
  exact-hash freeze before a genuinely unobserved final comparison.
- `liquid_sense_chat.py --thinking` is optional native inference configuration,
  not learned identity or a validated weight improvement. Keep branding out
  of raw tests and distinguish unfinished thought from a delivered answer.

## Latest distributed-weight studies 008/009 — complete

- Current branch: codex/liquid-sense-multi-tensor-20261105. Read
  MULTI_TENSOR_REPORT.md and reasoning/multi008/status.json plus
  reasoning/multi009/status.json, summary.json, selection.json and protocols.
- Both studies are complete and rejected on their seven-task screen. 008
  changed 32281 values in 40 gain tensors across 20 layers. 009 changed 4994722
  values in four down_proj matrices at physical layers 5,13,25,31. Target and
  inverse controls all remained 27/36 cases and 3/7 complete tasks, zero gains
  or losses. Do not repeat them or describe internal alignment as intelligence.
- Both start from the unchanged parent, not from each other. 008 requires
  restoring ALL saved norm vectors; the legacy parent loader does not do that.
  009 likewise restores ALL four dense matrices, including layers absent from
  the legacy best.pt overlay. Exact matrices and activation samples are saved.
- 009's targeting correction was committed before constructing/evaluating
  any 009 candidate, based only on the prior original/parent comparison;
  initial_preregistration.json preserves its preceding source hashes. No golds
  or evaluation cases changed; original reference forwards used enunciados only.
- Keep best.pt parent hash 46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8.
  Full/general/independent gates were not run for these candidates because
  neither passed screening. RSI100 validation 8 remains unused in this cycle.
- 46 technical tests passed; 22 tensor artifacts are audited. All workers end
  before the turn ends. Automatic RSI100 remains paused after 31 rejections.
- A future study needs a new hypothesis/registration and actual decoding
  states at the erroneous decision; do not invent missing full-precision
  activations or silently reuse an observed set as a new independent test.

## Complete weight audit and native architectural ablations 010 — complete

- Branch: codex/liquid-sense-native-audit-20261105. Read
  NATIVE_ARCHITECTURE_REPORT.md and native010/status.json, selection.json,
  NATIVE_PROTOCOL.md and screen_comparison.json before inference.
- Python scanned all 1,020,252,592 values in 699 unique loaded tensors, all
  buffers, and separately all 20,452,864 values in 15 preserved, unused MTP
  tensors. No nonfinite weights. Vision was inspected, not functionally tested.
- Three frozen native ablations finished: depth 8/36 cases, liquid 11/36,
  routed 11/36, all 0/7 complete tasks. Repeated parent is 27/36, 3/7;
  original Qwen is 27/36, 5/7. No candidate passed the monotone screen.
- They changed 138639155 / 139308551 / 140095367 scalar values respectively;
  all 32 physical layers were active, with 56 executions and two-stream mHC.
  Routed initialized all 48 input-dependent routers; the probe observed
  post-gate differences in 48 and stream separation in 47. Mechanism change
  and 10.37% temporal calibration-MSE reduction are not intelligence gains.
- Preserve unchanged best.pt SHA256 46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8.
  Validation eight remains unused; no full/general gate was run on these
  rejected candidates. Do not repeat completed experiments or restart RSI100.
- Native experiments are deterministic incremental bundles, not monolithic
  safetensors. Use native010.reload.load_candidate, which checks all parent
  tensors and reconstructs overlays AFTER the legacy loader. Legacy load_port
  alone resets source layers and would erase their native adaptation.
- Code, exact overlays, per-tensor hashes and outputs are preserved. Construction
  activations are ZIP data in nine chunks with a hash-checked restoration
  script. No previous checkpoint/report was removed. 55 technical tests and
  all nine cache probes passed; no background model worker remains.
- Official configs are pinned in native010/official; Loop phase/mHC layout
  matches SenseNova, but Qwen widths/DeltaNet remain Liquid-inspired operators,
  not full LFM3. No larger-model superiority or general improvement is shown.

## Wrong-response all-tensor diagnostics 011 — complete

- Branch: codex/liquid-sense-error-tensors-20261105. Read
  TENSOR_ERROR_ANALYSIS_REPORT.md and diagnostic011/status.json,
  capture_complete.json, analysis.json, metric_current.json and protocols.
- No weight candidate was created. Retain unchanged best.pt parent SHA256
  46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8.
- All five observed development errors and two correct guards were replayed
  for NEW complete instrumentation: 417 real decisions, 813 module-call slots
  each, all 699 parameter tensors catalogued, 546 accessed on both errors and
  successes, 153 unused vision tensors, no exclusively error-accessed weights.
  All outputs/case bits matched the old parent exactly; all parameter hashes
  stayed unchanged. Snapshot coverage at all five suspected spans was checked.
- Largest exploratory reader-output RMS contrasts were in_proj_a projections
  at physical layers25,6,28. Their role is DeltaNet decay, but RMS is not
  causal blame, a forgetting rate, or evidence of improved intelligence.
- Thirty preregistered +/-1% activation-only probes affected logits (max .25)
  but changed no argmax against matched full-prefill baselines. Longest_run
  full-prefill baseline disagreed with cached generation at the same prefix;
  that execution-path difference is separate from intervention effects.
  No new program-quality gain was measured or promoted.
- Delta4B_pp is task-complete pass@1(Liquid) minus pinned Qwen3.5-4B in pp,
  requiring matched protocol, fresh >=100 pairs, positive 95% lower bound,
  paired p<.05 and general/language retention. It remains UNMEASURED; only
  internal development 11/16 (68.75%) and 69/81 cases are known here.
- 4B revision851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a and seven file hashes
  are recorded. Its 9.32GB weights were not downloaded or evaluated in this
  8GiB/2.1GB-free environment. evaluate_4b.py is an offline executor for a
  suitable machine, not an already-completed larger-model comparison.
- Actual observations are losslessly archived in 11 tar.xz chunks (216106259
  uncompressed bytes). Use restore_traces.py; do not repeat completed captures
  to reconstruct them. all_tensors.csv/jsonl cover every parameter.
- Nine NEW technical tests passed. General/language tests and eight unused
  RSI100 validation tasks were not consumed. No model worker remains active;
  automatic RSI100 stays paused, and no background research is promised.

## Loop/language research and protected gate edit 012 — complete

- Branch codex/liquid-sense-loop-language-20261105. Read
  LOOP_LANGUAGE_RESEARCH_REPORT.md and loop012/decision.json, recovery.json,
  selection.json, PROTOCOL.md and status.json. No new checkpoint promoted.
- The actual first/second loop exit differs at all21 saved decisions: mean
  relative L2 .05979967, cosine .99822564. Seven real cached-call replays were
  bit-exact before causal output replacement; no full-prefill/cache confound.
- Replacing only the second loop exit with the first (all56 computations still
  executed) changed four of seven program texts/ASTs but no case bits:23/35
  cases,2/7 tasks both ways. This diagnostic is not an eligible single-pass model.
  Mechanical influence is not a demonstrated coding benefit.
- Neutral language pilot6: four outputs differ from Qwen original, two equal.
  Anonymous-order assistant review preferred Liquid2, Qwen2, ties2; not an
  independent human/general-superiority evaluation. Liquid had3 truncations,
  original2. Some Liquid outputs emitted stray think-closing tags. Strict JSON
  boolean check was more restrictive than the prompt; keep it unchanged and
  distinguish the semantic review accepting both identical string-sim outputs.
- One new direct closed-form edit changed24522 BF16 values in in_proj_a weights
  of physical layers6,25. It protects64 sampled inputs per layer and aligns
  second-pass internal teacher signals, not correct answer tokens/programs.
  First-visit/sample protection is not a global guarantee. No gradient/optimizer.
- Target and opposite-direction control both completed the7-task/35-case screen:
 23/35 cases,2/7 tasks, zero gains/losses against paired/historical parent.
  Internal activation fit is not a quality gain. Both exact overlays and all
  construction states are preserved; no more dose search in this study.
- Parent remains best.pt hash46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8.
  Eight RSI100 validation tasks remain unused; full/general/candidate-language
  gates were not run after failed screening. Original matched7-task reference
  is23/35 and4/7, not another earlier27/36 screen.
- Executor restarted before any screen row was saved. Checkpoints were already
  committed. Recovery verified hashes and reran only unsaved scoring phases,
  with a new paired parent replay matching every old text and case bit.
  Use resume_screen.py to resume only missing rows if another interruption occurs.
- To inspect rejected edits, use loop012.core.load_variant('target'/'inverse').
  To restore parent, cold-load it or restore BOTH saved parent_gate_weights.pt
  matrices: legacy e.apply does not reset this parameter family. Do not replace
  best.pt with the incremental overlay format. Five new technical tests passed.
  All model workers end before the turn ends; RSI100 stays paused.
