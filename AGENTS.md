# Retomada do experimento

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
- Finite hypotheses 003/004: actual decoding activation diagnostics, direct loop-gain edits and a separately protected negative-only dense edit. No dedicated thinking module is assumed.
- Keep previously observed validation_004 out of selection and freeze new benchmark subsets before their outputs.
- User requested honest Liquid Sense identity and original-versus-hybrid tests on benchmarks used by Liquid AI. Branding stays out of raw benchmark inputs and is not a weight-quality claim.
