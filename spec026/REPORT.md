# Spec026 — pequenos modelos híbridos criados do zero

Experimento concluído. O Liquid Sense principal e o APK continuam com os pesos anteriores.

Os dois filhos receberam pesos aleatórios novos, sem copiar tensores do professor. Compartilham o tokenizer/vocabulário; preservam 32 camadas físicas, 56 visitas, loop 4–27 duas vezes, mHC de dois fluxos, mistura GatedDeltaNet/atenção e conv7. São versões de texto com larguras menores da arquitetura experimental do projeto, sem reivindicar reprodução oficial dos modelos SenseNova ou Liquid AI.

Treino: 192 conversas, 13.644 rótulos únicos, três épocas, 40.932 exposições a tokens e 162 atualizações por tamanho. Adafactor, parâmetros mestres FP32, cálculo BF16/recorrência FP32. As 24 sequências reais do professor (498 tokens de saída) são exemplos de comportamento e não gabaritos verificados. Os checkpoints FP32 inicial/final, estado do otimizador e versões BF16 para inferência estão preservados.

| Modelo | Parâmetros | Tensores alterados | NLL inicial | NLL online da última época |
|---|---:|---:|---:|---:|
| small | 17,818,400 | 546/546 | 12.427 | 2.922 |
| large | 94,832,240 | 546/546 | 12.488 | 0.671 |

A NLL acima é de treino e não mede generalização. O embedding compartilhado ocupa cerca de 89% do filho menor e 67% do maior: compatibilidade direta com o vocabulário do professor tem custo relevante neste tamanho.

| Modelo | Programas corretos /8 | Casos /43 | Geral /8 |
|---|---:|---:|---:|
| original | 4 | 30 | 7 |
| target | 4 | 29 | 7 |
| small_initial | 0 | 0 | 0 |
| small_trained | 0 | 0 | 0 |
| large_initial | 0 | 0 | 0 |
| large_trained | 0 | 4 | 0 |

Os testes novos usam os mesmos prompts, greedy e limites: 96 tokens para código e 32 para geral. Nenhuma solução é entregue no prompt. São testes pequenos próprios, sem comparação com grandes modelos públicos.

| Rascunhador | Verificação | Propostas aceitas | Razão de velocidade¹ | Tokens finais iguais | p pareado² |
|---|---|---:|---:|---|---:|
| small | serial | 14/460 (3.04%) | 0.159× | True | 0.03125 |
| large | serial | 12/396 (3.03%) | 0.158× | True | 0.03125 |

A via de verificação em bloco falhou na igualdade de tokens em duas das 16 comparações (um mesmo prompt com ambos os filhos, no último token). Ambos usaram o fallback `serial` previsto no protocolo. Essa via verifica sequencialmente e não demonstra aceleração por verificação paralela. A aceleração equivalente em bloco permanece NÃO VALIDADA.

¹ Tempo total sem especulação / tempo total com especulação. Abaixo de 1× significa mais lento. Seis pares fixos por filho, ordem ABBA, três prefixes, orçamento de 32 tokens. Modelos residentes: tokenização, prefill, rascunhos, verificações, snapshots, rollback, correções e decodificação incluídos; carga dos pesos separada. Tempos de CPU x86, quota de dois CPUs e quatro threads; não são medições do Snapdragon ou do APK.

² Teste de inversão de sinais dos seis pares, bilateral, descritivo neste piloto curto. Resultados de diferenças numéricas nos tokens tornam a via inelegível como aceleração equivalente.

A verificação em bloco usa recorrência temporal sequencial nos estados em cache; rejeições restauram todos os 56 estados e repetem o prefixo aceito. As sondas de paridade e os testes sintéticos não provam equivalência universal. A capacidade individual dos filhos é medida separadamente da aceitação pelo professor.

A conferência posterior reproduziu a divergência no prompt S026S/5. No último passo, com o mesmo histórico de tokens, a diferença máxima nos logits foi 0,21875, e a margem entre os dois maiores logits da referência era 0,125. Os dois fallbacks sequenciais coincidiram com a referência nesse mesmo prompt, com diferença de logits zero nos prefixos comparados. Isso isola uma diferença entre caminhos de execução, sem identificar a primeira operação responsável ou provar que a causa seja somente arredondamento. Veja [reports/block_diagnostic.json](reports/block_diagnostic.json).

A auditoria dos erros encontrou zero funções analisáveis nos oito programas do menor; o maior repetiu exatamente o mesmo programa nos oito pedidos. O menor começou as oito respostas gerais com `def`; o maior fez isso em quatro. A baixa perda de treino não se converteu em seguir novas instruções. Não houve ablação de arquitetura/dados/objetivo para atribuir uma causa única. Veja [reports/failure_analysis.json](reports/failure_analysis.json).

Este piloto não estabelece o menor tamanho útil, inteligência geral ou velocidade após pré-treino amplo. Há apenas uma semente por tamanho e os kernels usados são as referências PyTorch de CPU. Uma continuação precisa de muito mais dados de pré-treino/distilação e novos testes reservados, sem reutilizar estes resultados para ajustar e reavaliar no mesmo conjunto.

Fontes e protocolo: [PROTOCOL.md](PROTOCOL.md), [config.json](config.json), [frozen.json](frozen.json). Resultados brutos: [reports/](reports/), [logs/](logs/). Pesos e metadados: [checkpoints/](checkpoints/). O alvo continua identificado pelo SHA256 `46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8`.
