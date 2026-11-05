# Qwen SenseNova Liquid — RSI assistido

Experimento de Felipe: adaptar diretamente os pesos de Qwen3.5-0.8B a um decoder loop/mHC inspirado em SenseNova-Loop-9B e a operadores compatíveis inspirados em Liquid LFM3.

Status inicial: calibração algébrica concluída; ciclos de melhoria e avaliação em preparação. Não há demonstração de autoaperfeiçoamento recursivo geral ou de ganho de inteligência.

Este repositório será usado para código, estado retomável, logs reais, checkpoints incrementais e resultados. O trabalho ativo fica na branch `codex/qwen-sensenova-liquid-rsi-20261103`.

## Retomada concluída em 2026-11-05

Estado mais recente: [branch de recuperação e validação](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/tree/codex/mentor002-independent-validation-20261104).
[Relatório completo, fixado por commit](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/blob/478cc5933a11925ef050507ae4f761234f0569ad/MENTOR002_VALIDATION_REPORT.md).

A hipótese 002 original tinha somente sua triagem salva; o checkpoint final não foi encontrado no estado persistido acessível. A reconstrução da hipótese reproduziu 11→12 tarefas e 69→72 casos no desenvolvimento, com 4/4 controles. Não se afirma identidade bit a bit com os pesos não salvos.

Na validação nova congelada (24 tarefas / 192 casos), Qwen original fez 5/24 e 71/192; híbrido pai fez 7/24 e 85/192; candidata reconstruída fez 7/24 e 78/192. Todos fizeram 6/12 controles estritos, com limitações e diferenças por item documentadas. A candidata ganhou 5 casos, perdeu 12 e não ganhou tarefas completas em relação ao pai. **Sem promoção: manter o checkpoint pai.**

Seleção preservada: `rsi100/checkpoints/best.pt`, SHA256 `46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8`.
A candidata, suas ativações e todos os resultados continuam arquivados como experimento. Loop/mHC + operadores inspirados em Liquid permanecem ativos; o híbrido tem aproximadamente 1,02B parâmetros carregados. Os 31 descartes antigos e a V3 NCM foram preservados. A busca automática não foi reiniciada. Avaliação concluída, sem processo de pesquisa em segundo plano.
