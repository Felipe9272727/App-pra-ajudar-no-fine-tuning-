# Liquid Sense 0.8B LOOP

Experimento de Felipe: adaptar diretamente os pesos de Qwen3.5-0.8B a um decoder loop/mHC inspirado em SenseNova-Loop-9B e a operadores compatíveis inspirados em Liquid LFM3.

Status inicial: calibração algébrica concluída; ciclos de melhoria e avaliação em preparação. Não há demonstração de autoaperfeiçoamento recursivo geral ou de ganho de inteligência.

Este repositório será usado para código, estado retomável, logs reais, checkpoints incrementais e resultados. O histórico inicial fica na branch `codex/qwen-sensenova-liquid-rsi-20261103`.

## Retomada concluída em 2026-11-05

Estado mais recente: [branch de recuperação e validação](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/tree/codex/mentor002-independent-validation-20261104).
[Relatório completo, fixado por commit](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/blob/478cc5933a11925ef050507ae4f761234f0569ad/MENTOR002_VALIDATION_REPORT.md).

A hipótese 002 original tinha somente sua triagem salva; o checkpoint final não foi encontrado no estado persistido acessível. A reconstrução da hipótese reproduziu 11→12 tarefas e 69→72 casos no desenvolvimento, com 4/4 controles. Não se afirma identidade bit a bit com os pesos não salvos.

Na validação nova congelada (24 tarefas / 192 casos), Qwen original fez 5/24 e 71/192; híbrido pai fez 7/24 e 85/192; candidata reconstruída fez 7/24 e 78/192. Todos fizeram 6/12 controles estritos, com limitações e diferenças por item documentadas. A candidata ganhou 5 casos, perdeu 12 e não ganhou tarefas completas em relação ao pai. **Sem promoção: manter o checkpoint pai.**

Seleção preservada: `rsi100/checkpoints/best.pt`, SHA256 `46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8`.
A candidata, suas ativações e todos os resultados continuam arquivados como experimento. Loop/mHC + operadores inspirados em Liquid permanecem ativos; o híbrido tem aproximadamente 1,02B parâmetros carregados. Os 31 descartes antigos e a V3 NCM foram preservados. A busca automática não foi reiniciada. Avaliação concluída, sem processo de pesquisa em segundo plano.

## Pesquisa guiada e identidade — conclusão de 2026-11-05

Continuação atual: [código, pesos e artefatos](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/tree/codex/liquid-sense-reasoning-20261105).
[Relatório fixado por commit](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/blob/982cafd27ae51847d3dabdbbddc17919c723ea29/REASONING_BENCHMARK_REPORT.md).

Foram testadas três novas hipóteses: reforço dos pesos de visita em camadas selecionadas por ativações, edição direta da MLP com proteção de 137 estados e terceira visita seletiva (80 execuções de camada). As intervenções de loop não ganharam casos na triagem. A edição da MLP fez 69→70 casos de desenvolvimento, com controles preservados, mas piorou a NLL das âncoras (3,183729→3,189105) e foi rejeitada. **Nenhuma candidata promovida; manter o pai.**

| Piloto em subconjuntos fixados | Qwen original | Liquid Sense preservado |
|---|---:|---:|
| LiveCodeBench v6 (8 problemas) | 1/8 | 2/8 |
| GSM8K, resposta concisa (16 questões) | 1/16 | 1/16 |
| IFEval estrito (12 prompts) | 8/12 | 8/12 |

Os protocolos locais usam limites e um executor restrito; não reproduzem as pontuações completas publicadas pela Liquid AI. As amostras são pequenas, com trocas de acertos detalhadas no relatório e sem evidência estatística de superioridade geral.

O chat se apresenta como **Liquid Sense**, projeto independente conduzido por um desenvolvedor, com base Qwen e adaptações inspiradas em SenseNova/Liquid. Essa identidade é configuração da aplicação, sem alegação de aprendizado nos pesos nem de criação do Qwen do zero. A apresentação real e suas tentativas estão preservadas.

Foram aprovados 39 testes técnicos. Pesos anteriores, candidatas e ativações permanecem arquivados. A execução terminou; nenhum processo de pesquisa ficou em segundo plano.
