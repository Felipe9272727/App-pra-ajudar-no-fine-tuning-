# liquid sense 0.8 b LOOP — segundo piloto

Nenhuma nova edição densa passou pelos critérios registrados. O checkpoint final mantém o híbrido com SenseNova e Liquid ativos.

Os pesos foram realmente ajustados e avaliados. Não houve backward/autograd nem calculadora na inferência. O assistente controlou os experimentos; isso não demonstra RSI autônomo geral.

## Comparação final nova — 64 perguntas

| Modelo | Formato exato | Conteúdo | Numérico/código (conteúdo) | Controles gerais |
|---|---:|---:|---:|---:|
| Qwen3.5-0.8B original | 34/64 | 34/64 | 26/48 | 8/16 |
| Híbrido SenseNova + Liquid antes do novo ajuste | 39/64 | 39/64 | 27/48 | 12/16 |

| Família | Qwen3.5-0.8B original | Híbrido SenseNova + Liquid antes do novo ajuste |
|---|---:|---:|
| addition | 9/12 | 9/12 |
| subtraction | 10/12 | 10/12 |
| multiplication | 7/12 | 8/12 |
| python | 0/12 | 0/12 |
| general_control | 8/16 | 12/16 |

Comparação pareada de conteúdo, original → checkpoint final: 6 melhora(s), 1 regressão(ões). Teste binomial exato nos pares discordantes: p=0.1250. As perguntas compartilham templates; esse número é descritivo e não estabelece significância em capacidades gerais.

O teste final não escolheu pesos. O checkpoint foi congelado antes de observar essas respostas. Os resultados anteriores de 24 perguntas estão em PILOT_REPORT.md e não são comparáveis diretamente a este conjunto.

## O que foi aprendido por edição direta

- 96 exemplos sintéticos com respostas verificadas por código.
- 335 posições supervisionadas e 96 posições de preservação.
- 81 posições tinham o próximo token preferido diferente do alvo.
- A matriz existente `layers.31.mlp.down_proj.weight` recebe um delta obtido por regressão ridge fechada.
- Fatores de posto 32 comprimem o checkpoint; são multiplicados e escritos na matriz densa ao carregar. Não há adaptador adicional na inferência.
- Correções conjuntas, correções de dígitos e controle só de parada foram definidos antes das avaliações.

## Arquivo das candidatas

NLL de resposta da base híbrida ativa: 1.186612.
NLL dos textos de preservação: 3.183027.

| Candidata | Família | Ridge | Força | NLL resposta | NLL preservação | Valores BF16 alterados | Validação conteúdo |
|---|---|---:|---:|---:|---:|---:|---|
| candidate_01 | joint | 0.1 | 0.5 | 1.120153 | 3.182440 | 1854801 | Não elegível |
| candidate_02 | joint | 0.1 | 1.0 | 1.077597 | 3.183940 | 2488648 | 9/24 |
| candidate_03 | digits | 0.1 | 0.5 | 1.120251 | 3.182263 | 1849364 | Não elegível |
| candidate_04 | digits | 1.0 | 1.0 | 1.106884 | 3.181214 | 1072961 | 9/24 |
| candidate_05 | stop_only | 0.1 | 0.5 | 1.184631 | 3.181601 | 108075 | Não elegível |

O controle `stop_only` nunca pode ser promovido. Para promoção é necessário reduzir a NLL de resposta, preservar a NLL das âncoras e aumentar o conteúdo correto na validação sem reduzir o formato exato. Todos os motivos e hashes estão em `lab_rsi/archive.json`.

## As duas partes da arquitetura continuam presentes

- SenseNova: topologia de 32 camadas físicas, 56 execuções, mHC de duas vias e segunda visita ativa com ganho 0,05.
- Liquid/LFM3: convolução de sete posições com coeficientes históricos aprendidos não nulos e atenção local de 256 tokens em três camadas.
- Todas as novas candidatas passaram pela mesma verificação de arquitetura. Nenhuma desliga essas partes para melhorar a métrica.
- O corpo continua com dimensões/pesos Qwen. Não são os pesos do SenseNova-Loop-9B nem o LFM3 completo. Roteadores mHC permanecem na inicialização; oito camadas inseridas têm saída neutra neste perfil.
- O nome nominal 0,8B vem da base. O híbrido ampliado carrega aproximadamente 1,02B parâmetros, incluindo visão não avaliada aqui.

## Protocolo, limites e reprodução

Greedy sem thinking, até 12 tokens de resposta, cache, BF16/FP32, 4 threads CPU por máquina. Até quatro prompts de comprimento idêntico por lote, sem padding, com a mesma organização nos modelos. O híbrido executa mais camadas que o original; o orçamento de computação é maior. No GitHub, cada modelo usa as mesmas duas partições e a mesma organização de lotes; o hardware físico entre runners pode variar.

| Modelo | Parâmetros carregados | Tempo amortizado de geração, 64 perguntas | Respostas no limite de 12 tokens |
|---|---:|---:|---:|
| Qwen3.5-0.8B original | 852,985,920 | 151.0 s | 1 |
| Híbrido SenseNova + Liquid antes do novo ajuste | 1,020,252,592 | 357.1 s | 2 |

Benchmark customizado pequeno e principalmente na distribuição do currículo. Não avalia visão, contexto longo ou inteligência geral. Uma diferença pequena pode ser ruído, formato ou especialização. Não há afirmação de que o modelo passou a compreender sua arquitetura.

Princípios públicos dos laboratórios e referências: [LAB_METHODS.md](LAB_METHODS.md). Procedimento completo: [lab_rsi/PROTOCOL.md](lab_rsi/PROTOCOL.md).

Estado final: concluído, salvo e parado. Não existe processo permanente de treino depois desta execução.

## Respostas e correções completas

| ID | Esperado | Original | Híbrido antes do ajuste | Final |
|---|---|---|---|---|
| heldout_addition_10 | 93 | 93 | 93 | 93 |
| heldout_multiplication_02 | 108 | 108 | 108 | 108 |
| heldout_python_10 | 243 | 139 | 130 | 130 |
| heldout_python_11 | 130 | 14 | 14 | 14 |
| heldout_python_01 | 251 | 100 | 100 | 100 |
| heldout_subtraction_06 | 34 | 34 | 34 | 34 |
| heldout_multiplication_08 | 66 | 66 | 66 | 66 |
| heldout_python_02 | 81 | 100 | 100 | 100 |
| heldout_multiplication_07 | 121 | 121 | 121 | 121 |
| heldout_python_03 | 130 | 110 | 110 | 110 |
| heldout_python_06 | 50 | 10 | 10 | 10 |
| heldout_multiplication_10 | 56 | 56 | 56 | 56 |
| heldout_addition_07 | 135 | 135 | 135 | 135 |
| heldout_multiplication_01 | 32 | 16 | 4 * 8 = 32 | 4 * 8 = 32 |
| heldout_python_04 | 121 | 124 | 121212121212 | 121212121212 |
| heldout_addition_04 | 173 | 173 | 173 | 173 |
| heldout_subtraction_03 | 125 | 125 | 125 | 125 |
| heldout_subtraction_09 | 3 | 13 | 13 | 13 |
| heldout_addition_03 | 116 | 116 | 116 | 116 |
| heldout_multiplication_05 | 36 | 12 * 3 = 36 | 12 * 3 = 36 | 12 * 3 = 36 |
| heldout_python_07 | 171 | 110 | 110 | 110 |
| heldout_subtraction_04 | 17 | 17 | 17 | 17 |
| heldout_python_00 | 194 | 100 | 100 | 100 |
| heldout_multiplication_09 | 96 | 8 * 12 = 96 | 8 * 12 = 96 | 8 * 12 = 96 |
| heldout_addition_08 | 136 | 136 | 136 | 136 |
| heldout_subtraction_11 | 136 | 136 | 136 | 136 |
| heldout_addition_09 | 129 | 229 | 21 + 108 = 129 | 21 + 108 = 129 |
| heldout_subtraction_08 | 51 | 51 | 151 | 151 |
| heldout_addition_01 | 229 | 129 | 138 | 138 |
| heldout_subtraction_07 | 118 | 118 | 118 | 118 |
| heldout_subtraction_00 | 23 | 23 | 23 | 23 |
| heldout_addition_11 | 170 | 170 | 170 | 170 |
| heldout_python_09 | 194 | 100 | 100 | 100 |
| heldout_multiplication_00 | 24 | 24 | 24 | 24 |
| heldout_subtraction_10 | 46 | 46 | 46 | 46 |
| heldout_python_08 | 50 | 10 | 100 | 100 |
| heldout_python_05 | 74 | 100 | 100 | 100 |
| heldout_multiplication_03 | 30 | 10 | 30 | 30 |
| heldout_multiplication_11 | 285 | 345 | 345 | 345 |
| heldout_subtraction_01 | 108 | 108 | 108 | 108 |
| heldout_subtraction_02 | 39 | 19 | 39 | 39 |
| heldout_multiplication_06 | 112 | 112 | 112 | 112 |
| heldout_multiplication_04 | 30 | 30 | 30 | 30 |
| heldout_addition_02 | 138 | 138 | 138 | 138 |
| heldout_addition_00 | 173 | 173 | 173 | 173 |
| heldout_subtraction_05 | 17 | 17 | 17 | 17 |
| heldout_addition_05 | 50 | 40 | 40 | 40 |
| heldout_addition_06 | 134 | 134 | 134 | 134 |
| heldout_control_00 | Ag | Ag | Ag | Ag |
| heldout_control_01 | Pb | Pb | Pb | Pb |
| heldout_control_02 | Saturn | Uranus | Saturn | Saturn |
| heldout_control_03 | Mercúrio | Júpiter | Júpiter | Júpiter |
| heldout_control_04 | full | full | full | full |
| heldout_control_05 | estreito |  curto. | curto | curto |
| heldout_control_06 | taught | teach | taught | taught |
| heldout_control_07 | animais | animais | animais | animais |
| heldout_control_08 | ohm | Ohm (Ω) | Ohm | Ohm |
| heldout_control_09 | coração | Coração. | Coração. | Coração. |
| heldout_control_10 | Africa | Africa | Africa | Africa |
| heldout_control_11 | Buenos Aires | Buenos Aires. / </think> /  / Buenos Aires | Buenos Aires. | Buenos Aires. |
| heldout_control_12 | oxygen | Oxygen | Oxygen | Oxygen |
| heldout_control_13 | abelha | PEQUENO | Gato | Gato |
| heldout_control_14 | pentagon | pentagon | pentagon | pentagon |
| heldout_control_15 | espanhol | Español | Español | Español |
