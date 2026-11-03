# Piloto de RSI assistido — Qwen, SenseNova e motivos LFM3

Data: 03/11/2026. Execução real em CPU, com edições diretas dos pesos, calibração algébrica e controle pelo assistente.

## Estado salvo

- Rodadas de desenvolvimento concluídas: **6**.
- Candidatas promovidas nestas rodadas: **0**.
- O código, o patch de convoluções, a receita incremental, sugestões reais e as decisões estão versionados nesta branch.
- O piloto está concluído e pausado no checkpoint. Não há processo permanente de treinamento ou API paga em execução.

## Comparação final em 24 perguntas novas

| Modelo | Acertos | Média de tempo por pergunta | Pico RSS |
|---|---:|---:|---:|
| Qwen original | 17/24 | 1.967 s | 2076.3 MiB |
| Checkpoint preservado, loop adaptado | 18/24 | 10.419 s | 2794.4 MiB |
| Loop + convoluções calibradas e janela LFM3 (experimental) | 19/24 | 3.930 s | 2795.7 MiB |

O teste foi congelado antes de calibrar e não escolheu a receita. Usamos geração greedy, thinking desativado, no máximo 12 tokens novos por resposta, CPU com oito threads e backbone BF16. Roteadores e controles permanecem FP32. Respostas numéricas aceitam somente um número; JSON é comparado semanticamente; texto é normalizado respeitando exigências explícitas de caixa. São questões autorais básicas, não benchmarks padronizados de inteligência.

O tempo é de uma única execução por variante e depende do comprimento das respostas, aquecimento e carga do host. Não usamos esses tempos para atribuir um ganho de velocidade à atenção local da Liquid; os prompts deste teste são curtos.

As 24 perguntas diferem do antigo teste de 48 itens. Não compare diretamente os escores antigos com estes. Não houve reajuste dos pesos depois que os resultados reservados foram observados.

A comparação de caixa é estrita quando o pedido exige maiúsculas/minúsculas ou um símbolo químico. Nos demais itens textuais, ignoramos caixa e ponto final. A regra foi conferida uniformemente sobre as respostas brutas salvas.

## Seis ciclos registrados

| Rodada | gain | beta | liquid_mix | NLL da candidata | NLL do checkpoint medido | Decisão |
|---|---:|---:|---:|---:|---:|---|
| 1 | 0.05 | 0.025 | 0.0 | 0.400030 | 0.385319 | Rejeitada |
| 2 | 0.03125 | 0.0 | 0.0 | 0.408024 | 0.385319 | Rejeitada |
| 3 | 0.05 | 0.0 | 0.25 | 0.408835 | 0.385319 | Rejeitada |
| 4 | 0.04 | 0.0 | 0.0 | 0.402538 | 0.385319 | Rejeitada |
| 5 | 0.05 | 0.005 | 0.0 | 0.386972 | 0.385319 | Rejeitada |
| 6 | 0.05 | 0.0 | 0.01 | 0.410365 | 0.385319 | Rejeitada |

Menor NLL de desenvolvimento é melhor. A regra de promoção foi redução maior que 0,0001, definida no código. As rodadas 5 e 6 incluíram controle sem mudança de pesos após pedir sugestão ao modelo. As diferenças desses controles foram 0.0, 0.0. Não somamos resultados de calibração ou escores de testes diferentes para anunciar uma melhora.

## O que o assistente e a IA pequena fizeram

O assistente foi o controlador: escolheu as candidatas, executou as cirurgias numéricas, leu as métricas e decidiu promoção ou rejeição. A IA pequena foi consultada em cada rodada, e suas respostas brutas estão nos logs. Elas repetiram os parâmetros correntes; algumas ficaram truncadas e não formaram JSON completo. Não atribuímos ao modelo sugestões novas que ele não produziu. Os testes deste piloto não demonstram autoaperfeiçoamento recursivo autônomo ou geral.

## Arquitetura e adaptação efetivas

O código preserva o mecanismo de decoder da SenseNova: 32 camadas físicas, 56 execuções e mHC com duas vias, em dimensões do Qwen. Adicionamos controles de contribuição por visita. Primeiro reconstruímos uma inicialização conservadora: nas duas sondas testadas, os logits eram bit a bit iguais aos do original antes de ativar a segunda passagem.

A calibração das convoluções foi uma regressão ridge fechada sobre oito textos (269 tokens), sem backward ou otimizador. Ela reescreveu 440.792 coeficientes BF16, incluindo 221.184 coeficientes novos de histórico. Isso é aprendizagem algébrica por dados, e não um processo inteiramente livre de treinamento. O patch ajustado foi preservado como candidata; ele não está automaticamente ativo no checkpoint principal.

As ideias LFM3 implementadas são convolução com sete posições e atenção local de 256 tokens em três camadas de atenção. O mecanismo sequencial principal continua sendo Gated DeltaNet; não portamos o operador completo nem os pesos treinados do LFM3. Testamos a causalidade em 300 posições e a equivalência da máscara de um passo com cache. O benchmark curto não mede qualidade de contexto longo ou ganhos de velocidade desses operadores.

Receita do checkpoint principal: `{"gain": 0.05, "beta": 0.0, "liquid_mix": 0.0, "development_nll": 0.3853193211834878}`.

Com beta zero, as oito camadas físicas inseridas continuam neutras; as tentativas de ativá-las foram rejeitadas. Com liquid_mix zero, o delta de convolução aprendido e a janela local ficam desativados no checkpoint principal. A variante experimental Liquid é avaliada separadamente. Ter os módulos no código não equivale a ter aprendido a usá-los bem.

As medições de desenvolvimento antes e depois de expandir o kernel podem apresentar diferenças numéricas BF16. Cada ciclo reavaliou o checkpoint e a candidata na mesma implementação; não atribuímos essas diferenças de implementação a uma rodada de RSI.

## Todas as respostas lado a lado

| ID | Gabarito | Original | Checkpoint preservado | Liquid experimental |
|---|---|---|---|---|
| arithmetic_01 | `71` | `71` (acerto) | `71` (acerto) | `71` (acerto) |
| arithmetic_02 | `63` | `63` (acerto) | `63` (acerto) | `63` (acerto) |
| arithmetic_03 | `83` | `83` (acerto) | `83` (acerto) | `83` (acerto) |
| arithmetic_04 | `92` | `92` (acerto) | `92` (acerto) | `92` (acerto) |
| arithmetic_05 | `63` | `63` (acerto) | `63` (acerto) | `63` (acerto) |
| arithmetic_06 | `66` | `66` (acerto) | `66` (acerto) | `66` (acerto) |
| arithmetic_07 | `25` | `18 + 7 = 25` (erro) | `18 + 7 = 25` (erro) | `18 + 7 = 25` (erro) |
| arithmetic_08 | `36` | `36.00` (acerto) | `36.00` (acerto) | `36.00` (acerto) |
| knowledge_01 | `Tokyo` | `Tokyo` (acerto) | `Tokyo` (acerto) | `Tokyo` (acerto) |
| knowledge_02 | `Saturn` | `Saturn` (acerto) | `Saturn` (acerto) | `Saturn` (acerto) |
| knowledge_03 | `3` | `3` (acerto) | `3` (acerto) | `3` (acerto) |
| knowledge_04 | `Au` | `Au` (acerto) | `Au` (acerto) | `Au` (acerto) |
| code_01 | `15` | `10` (erro) | `15` (acerto) | `15` (acerto) |
| code_02 | `6` | `5 ⏎ ` (erro) | `5 ⏎ ` (erro) | `5 ⏎ ` (erro) |
| code_03 | `3` | `10 // 3 = 3 ⏎ ` (erro) | `10 // 3 = 3 ⏎ ` (erro) | `3` (acerto) |
| code_04 | `9` | `9` (acerto) | `9` (acerto) | `9` (acerto) |
| instruction_01 | `janela` | `janela` (acerto) | `janela` (acerto) | `janela` (acerto) |
| instruction_02 | `GARDEN` | `GARDEN ENTIRELY IN UPPERCASE.` (erro) | `GARDEN ENTIRELY IN UPPERCASE.` (erro) | `GARDEN ENTIRELY IN UPPERCASE.` (erro) |
| instruction_03 | `{"n":7}` | `{"n": 7}` (acerto) | `{"n": 7}` (acerto) | `'''json ⏎ {"n": 7} ⏎ '''` (erro) |
| instruction_04 | `Tadeu` | `Tadeu` (acerto) | `Tadeu` (acerto) | `Tadeu` (acerto) |
| logic_01 | `yes` | `yes` (acerto) | `yes` (acerto) | `yes` (acerto) |
| logic_02 | `Pia` | `Omar` (erro) | `Omar` (erro) | `Pia` (acerto) |
| logic_03 | `no` | `no` (acerto) | `no` (acerto) | `no` (acerto) |
| logic_04 | `20` | `10` (erro) | `16` (erro) | `16` (erro) |

## Retomar

Leia AGENTS.md, rsi/status.json, rsi/pending.json e checkpoints/incumbent.json. Não repetir rodadas já finalizadas. Como o conjunto reservado já foi avaliado, uma nova pesquisa precisa de outro conjunto de teste ainda não observado para verificar o próximo resultado.

O checkpoint é incremental: modelo público na revisão fixa + scripts versionados + receita JSON + patch de tensores. Isso reconstrói os mesmos pesos sem subir gigabytes de base. O usuário não pediu entrega dos pesos completos agora.

Fontes e licenças: README.md, LICENSE e NOTICE. Os limites e os resultados negativos fazem parte do registro do experimento.
