# Aprendizagem supervisionada do loop — estudo 013

Usei soluções corretas na aprendizagem, conforme a nova orientação do usuário. O teste de programação recebeu apenas os enunciados, sem soluções, casos de teste ou feedback. Este relatório compara saídas reais; o ajuste interno, sozinho, não comprova ganho de capacidade.

## O que foi implementado

Foram criados 200 problemas parametrizados em 20 famílias: 120 para ensino, 40 para validação e 40 para teste final. Todos os programas de referência passaram nos 4.000 casos executados no sandbox. A divisão é por família; não há AST de solução idêntica entre conjuntos. São apenas 20 famílias customizadas, com variantes correlacionadas, não 200 algoritmos independentes.

Os 120 programas de ensino forneceram 4472 tokens de solução/EOS. Foram amostradas 2862 decisões, das quais 452 tinham um token previsto diferente do token correto. Os programas foram escritos pelo pesquisador e verificados por oráculos executáveis; não houve API professora externa nem custo de API registrado.

Dois adaptadores de posto 16 foram ajustados por PCA e regressão ridge, sem gradientes, backward, otimizador ou SFT/LoRA. Um usa a diferença entre as duas passagens; o outro também usa um filtro causal de sete posições. Ambos atuam somente na saída da segunda visita da camada física 27. A direção-alvo vem dos embeddings do token correto e do token produzido. Transportá-la para esse ponto aproxima as quatro camadas restantes por uma identidade: essa é uma hipótese local e pode estar errada.

O modelo mantém 32 camadas físicas, 56 execuções, mHC de duas vias e os operadores DeltaNet e janelas locais anteriores. Os 699 tensores do pai não foram alterados; os novos parâmetros são 32.768 e 49.152, respectivamente. Os pesos dos roteadores e convoluções anteriores não foram treinados neste piloto. O filtro novo é uma adaptação temporal inspirada em Liquid, não uma reprodução integral da arquitetura Liquid AI.

## Comparação por geração livre

A triagem congelada contém oito problemas novos de quatro famílias da validação. Ela já está observada e não pode ser reapresentada como teste final. Todas as variantes usaram os mesmos enunciados, tokenizer, limite de 160 tokens, geração gulosa, seed 0, thinking desativado, cache, kernels eager e quatro threads. Pai e candidatas compartilham a mesma profundidade; o Qwen original executa 24 camadas, portanto não há igualdade de FLOPs.

| Modelo | Tarefas completas | Casos corretos | Controles | NLL de linguagem |
|---|---:|---:|---:|---:|
| Qwen original | 0/8 | 36/160 | 10/12 | 3.186716 |
| Liquid Sense anterior | 0/8 | 43/160 | 10/12 | 3.183729 |
| Adaptador de loop | 0/8 | 39/160 | 10/12 | 3.184345 |
| Adaptador de loop + temporal | 0/8 | 43/160 | 10/12 | 3.183684 |

| Modelo | Tempo total de geração (s) | Tokens gerados | Tokens/s agregados | Respostas no limite |
|---|---:|---:|---:|---:|
| Qwen original | 90.08 | 779 | 8.65 | 2 |
| Liquid Sense anterior | 205.84 | 673 | 3.27 | 0 |
| Adaptador de loop | 193.72 | 620 | 3.20 | 0 |
| Adaptador de loop + temporal | 215.13 | 673 | 3.13 | 0 |

São tempos de geração serial desta execução, sem carregamento de pesos ou sandbox. O comprimento de resposta varia entre modelos; não é um benchmark isolado de kernels, TTFT, energia ou throughput concorrente. Nenhum teste de aceleração especulativa foi realizado.

Os controles incluem quatro questões anteriores e oito questões novas de linguagem e raciocínio. As 12 âncoras de NLL são antigas e servem apenas à retenção. Os gabaritos e o extrator de código permaneceram iguais. Código com sintaxe inválida ou variável não definida foi contado como erro, sem reparo automático.

Adaptador de loop versus pai: 0 tarefas ganhas, 0 perdidas; 0 casos ganhos e 4 perdidos. Textos alterados: 1. NLL nos mesmos 24 exemplos de ensino: 0.499763 → 0.489478. O MSE do alvo local caiu 25.73%; isso mede ajuste ao sinal de ensino, não acerto em problemas novos.

Adaptador de loop + temporal versus pai: 0 tarefas ganhas, 0 perdidas; 0 casos ganhos e 0 perdidos. Textos alterados: 0. NLL nos mesmos 24 exemplos de ensino: 0.499763 → 0.489277. O MSE do alvo local caiu 26.07%; isso mede ajuste ao sinal de ensino, não acerto em problemas novos.

## Auditoria do avaliador

A política AST histórica rejeita qualquer identificador que comece com sublinhado, inclusive o nome local `_`, válido em Python. Dois programas de brinquedo semanticamente equivalentes confirmaram esse viés: o que usa `item` passou 3/3, e o que usa `_` foi rejeitado antes da execução. A auditoria está em review013/harness_audit.json. Nenhum programa do modelo foi reparado, nenhuma resposta foi renomeada e nenhum gabarito, escore primário ou critério de seleção mudou.

Em window_ranges_0, a candidata de loop recebeu ContractError por `_`, enquanto o pai passava quatro entradas curtas antes de alcançar um K indefinido. A candidata também usa a amplitude global da lista em lugar de amplitudes das janelas, um erro algorítmico real. Não interpretamos a diferença desses quatro casos como medida direta de perda de inteligência. Não há ganho de tarefa completa que justifique promoção.

Uma versão futura do avaliador deve tratar construções Python válidas de forma adequada e declarar todas as restrições antes de congelar novos testes. Este conjunto já foi observado e não pode voltar a ser chamado de teste inédito após uma correção.

## Decisão e limites

Decisão registrada: `complete_both_rejected_screen`. Checkpoint principal preservado: `rsi100/checkpoints/best.pt`, SHA256 `46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8`. As candidatas, seus estados de construção e as saídas foram preservados como experimentos.

A geração é determinística; repetir a mesma resposta não cria novas amostras independentes. A comparação pareada, p-valor por tarefa e bootstrap por família estão em review013/comparison.json. Há apenas quatro famílias na triagem; intervalos degenerados não provam equivalência. O conjunto foi criado pelo mesmo pesquisador que propôs a edição, sem auditoria cega externa. Não se pode garantir novidade perante o pré-treino ou generalização ampla.

Alterar estados ou usar duas passagens não demonstra revisão semântica de erros. O adaptador aprendeu uma aproximação de correção de tokens em prefixos corretos; isso não elimina a diferença entre esses prefixos e os erros que ele próprio gera. Não foi adicionada terceira passagem neste estudo: o protocolo exige ganho na segunda antes de ampliar o custo. Não foi feita comparação executada com 4B ou implementado DSpine.

Ver STATUS_RECUPERACAO.md, PLANO_DSPINE.md e review013/PROTOCOL.md. A retomada segura está em review013/resume_study.py e review013/REPRODUCE.md; ela verifica os checkpoints e não repete fases concluídas. Não há processo permanente.

Depois de todas as inferências, o agregador original encontrou a ausência de case_passed nas rejeições antecipadas de sintaxe/AST. finalize.py consolidou os mesmos escores zero por uma regra explícita, sem repetir inferência ou alterar saídas. As fontes congeladas continuam preservadas; logs e recovery.json registram os dois problemas operacionais.

Nenhuma variante do modelo avaliou os 40 problemas finais ou os outros 32 problemas de validação após a falha da triagem. As referências desses problemas foram verificadas no sandbox, mas não foram usadas no ensino. Os conjuntos antigos reservados também continuam fechados.
