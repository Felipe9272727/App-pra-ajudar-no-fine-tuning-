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

## Pedido atual: localizar grupos associados a programação

- Branch `codex/liquid-sense-code-focus-20261104`; estado em `code_focus/status.json`.
- A busca de 100 rodadas segue intacta em sua própria branch. O novo workflow
  `.github/workflows/liquid-sense-code-focus.yml` aguarda seu sucesso e importa
  apenas a seleção congelada por hash, sem usar seu teste final para escolher.
- Leia `code_focus/PROTOCOL.md`, `parent_import.json`, `archive.json` e `frozen.json`
  quando existirem. Erros de programas não identificam causas neurais por si.
- Grupos selecionados por ativação são hipóteses. Comparar ablações-alvo e controles;
  não alegar ter localizado um módulo exclusivo de programação.
- Os patches escrevem 64 colunas existentes por camada; manter loops/mHC/Liquid
  do pai. Sem gradientes, referências ou tokens-alvo nos prompts.
