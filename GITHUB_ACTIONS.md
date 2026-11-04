# CPUs do GitHub para liquid sense 0.8 b LOOP

Este pipeline testa o código e os checkpoints salvos neste repositório público.
Usa apenas `ubuntu-24.04` padrão, com quatro threads por máquina. O GitHub
documenta 4 vCPUs e 16 GB de RAM nesse runner público e computação gratuita
para runners padrão em repositórios públicos. Runners maiores não fazem parte
deste fluxo. Os limites e a disponibilidade da conta continuam se aplicando.

Fontes oficiais:

- https://docs.github.com/en/actions/reference/runners/github-hosted-runners
- https://docs.github.com/en/actions/reference/limits
- https://docs.github.com/en/billing/concepts/product-billing/github-actions

## Divisão do trabalho

| Etapa | Máquinas simultâneas | Função |
|---|---:|---|
| Preparação | 1 | Baixar a revisão Qwen fixada e reconstruir o port |
| Desenvolvimento | 1 | Comparar as cinco candidatas na mesma configuração de CPU |
| Validação | Até 3 | Gerar respostas da base ativa e de até duas candidatas |
| Congelamento | 1 | Escolher exclusivamente por desenvolvimento e validação |
| Teste final | Até 4 | Avaliar os mesmos grupos de perguntas em original/base/final |
| Relatório | 1 | Conferir partições, calcular os resultados e salvar |

O máximo de 16 vCPUs é a soma de quatro máquinas independentes. Não é uma
máquina de 16 núcleos nem treinamento distribuído de um único modelo.
O ganho principal é medir variantes e partições simultaneamente. Os cinco
deltas de pesos já foram calculados e salvos; não precisam ser treinados outra vez.

SenseNova loop/mHC e as adaptações Liquid permanecem ativos em todas as
candidatas. Só o Qwen original de comparação usa sua arquitetura original.
Nenhuma etapa acrescenta backpropagation, ferramentas à inferência ou pesos
de outro modelo incompatível. O nome nominal é 0,8B, mas o híbrido ampliado
carrega aproximadamente 1,02B parâmetros.

## Persistência e retomada

Cada etapa grava resultados pequenos como artifacts durante sete dias. Os
arquivos de pesos base ficam em um único cache compartilhado; não são enviados
como artifacts. Os cinco ajustes pequenos já estão no histórico Git.
Ao terminar, o job `save` grava resultados e manifesto do modelo na branch.
Ele recusa sobrescrever a branch se o código mudar durante a avaliação; nesse
caso os artifacts continuam disponíveis para recuperação.

Os resultados anteriores de desenvolvimento são preservados separadamente.
Todas as candidatas são medidas novamente na mesma máquina de quatro threads
para não misturar métricas de hardwares diferentes na seleção. Isso não refaz
o ajuste dos pesos nem usa perguntas do teste para selecionar candidatas.

No celular: abra **Actions → liquid sense - verified CPU pilot**, veja os jobs
e seus logs. Um arquivo `LAB_REPORT.md` confirmado no Git e o artifact
`liquid-final-report` indicam conclusão; jobs pendentes ou em execução não são
resultados finalizados. Uma falha não autoriza inventar respostas ausentes.

Cada job tem um limite explícito de 10–60 minutos e só há um fluxo por branch.
Não há agendamento recorrente, criação de contas, runners pagos ou serviço de
treinamento permanente. Um push posterior dos resultados não dispara outro ciclo.

O pipeline é disparado nesta branch ao adicionar/alterar o workflow ou o pedido
`lab_rsi/ci_run_request.json`. Uma nova execução depois de observar o teste final
exige outro piloto com outro teste; o controlador recusa reabrir o mesmo teste.

Mais CPUs aceleram experimentos. A melhoria do modelo continua dependendo dos
resultados medidos, e não do tempo que as máquinas ficam ligadas.
