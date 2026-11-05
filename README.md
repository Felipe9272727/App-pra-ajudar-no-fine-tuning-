# Liquid Sense 0.8B LOOP

Experimento de Felipe: adaptar diretamente os pesos de Qwen3.5-0.8B a um decoder loop/mHC inspirado em SenseNova-Loop-9B e a operadores compatíveis inspirados em Liquid LFM3.

Registro inicial (histórico): calibração algébrica concluída; ciclos de melhoria e avaliação em preparação. Não há demonstração de autoaperfeiçoamento recursivo geral ou de ganho de inteligência.

Este repositório será usado para código, estado retomável, logs reais, checkpoints incrementais e resultados. O histórico inicial fica na branch `codex/qwen-sensenova-liquid-rsi-20261103`.

## Varredura integral e adaptação nativa 010 — 05/11/2026

Python examinou todos os **1.020.252.592 valores em 699 tensores únicos** do híbrido carregado, além dos buffers e de 20,45 milhões de pesos MTP preservados fora do runtime. Não encontrou pesos não finitos.

Foram construídos e salvos três candidatos com as 32 camadas ativas, 56 execuções e até 48 roteadores mHC condicionais, alterando até **140,1 milhões de valores**, sem gradientes ou respostas nas entradas. A triagem foi **8/36, 11/36 e 11/36 casos**, todos 0/7 tarefas, contra o parent **27/36 e 3/7** e o Qwen original **27/36 e 5/7**. **Nenhum foi promovido; best.pt permanece intacto.** A validação inédita não foi consumida.

[Relatório, comparações e forma correta de recarregar os checkpoints incrementais](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/blob/f123d822d04694f431cdf1277f14ed9467201653/NATIVE_ARCHITECTURE_REPORT.md). Fontes, pesos incrementais, hashes e ativações estão na branch `codex/liquid-sense-native-audit-20261105`. Os 55 testes técnicos e as nove sondas de cache passaram. Estudo encerrado, sem processo em segundo plano e sem demonstração de superioridade sobre modelos maiores.

## Pesquisa mais recente — edições distribuídas 008/009 concluídas

[Relatório e comparações, fixados por commit](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/blob/f8a0a7f5801baeeb225aad38996e951c6f00ded7/MULTI_TENSOR_REPORT.md).
[Código, pesos e estado retomável](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/tree/codex/liquid-sense-multi-tensor-20261105).

Foram construídas duas candidatas independentes por edição direta: 32.281 valores em 40 tensores de normalização, e 4.994.722 valores em quatro matrizes MLP das camadas 5, 13, 25 e 31. Sem gradientes nem soluções corretas nas entradas; o original forneceu apenas vetores internos dos enunciados.

Na mesma triagem de sete problemas, ambas fizeram 27/36 casos e 3/7 tarefas completas, iguais ao híbrido pai. Controles inversos também não acrescentaram acertos. Não houve ganho demonstrado e nenhuma candidata foi promovida. O checkpoint anterior permanece selecionado.

Foram preservados e conferidos 22 artefatos de tensores, com os pesos exatos e as ativações. Os 46 testes técnicos passaram. Os testes de modelo terminaram; não há execução permanente nem retomada automática das 100 rodadas. O conjunto reservado continua sem execução nesta continuação, pois as candidatas falharam na triagem.

## Pesquisa anterior — diagnóstico concluído em 2026-11-05

[Relatório completo, fixado por commit](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/blob/c57b3124986268e495ff5324bdfdbe831028970e/ERROR_ANALYSIS_REPORT.md).
[Código, checkpoints e estado retomável](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/tree/codex/liquid-sense-error-analysis-20261105).

As edições diretas 006 e 007 foram concluídas sem promoção. A 006 ganhou um caso de programação, mas piorou a NLL de linguagem contra o pai. A 007 separou os fluxos mHC que operavam em igualdade, porém não mudou os acertos. Os pesos anteriores e os cinco novos artefatos de tensores foram preservados e conferidos.

Nos mesmos 16 problemas de desenvolvimento, o Qwen original resolveu 12 tarefas e 66/81 casos; o híbrido preservado resolveu 11 tarefas e 69/81 casos, ambos com 4/4 controles. São trocas entre tarefas, sem superioridade geral demonstrada. Em três problemas diagnósticos já observados, com raciocínio e até 1.024 tokens, o Qwen concluiu 2/3 respostas corretas e o híbrido 0/3, preso em repetição. O modo de raciocínio ficou opcional e experimental.

O checkpoint híbrido pai continua selecionado. Nenhuma melhoria nova nos pesos foi validada. Todos os testes deste ciclo terminaram; nenhum processo de modelo foi deixado rodando entre turnos.

## Retomada concluída em 2026-11-05

Estado desta etapa histórica: [branch de recuperação e validação](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/tree/codex/mentor002-independent-validation-20261104).
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
