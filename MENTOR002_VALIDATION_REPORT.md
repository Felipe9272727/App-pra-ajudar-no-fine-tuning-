# Liquid Sense 0.8B LOOP — retomada e validação independente

A base nominal é Qwen3.5-0.8B; o híbrido preservado carrega 1.020.252.592 parâmetros. Loop/mHC e operadores inspirados em Liquid permaneceram ativos. Zero gradientes, otimizadores ou fine-tuning.

## Recuperação

O commit 45b5152 preservou somente a triagem da hipótese 002 (pai 2/5, aleatório 2/5, candidata 5/5). O checkpoint final e o resultado completo não foram encontrados nas branches e artefatos acessíveis do GitHub. Foram preservados 31 descartes antigos, a rejeição da hipótese 001 e a V3 NCM como experimento não promovido. Não se reiniciou a busca automática.

A reconstrução usa a dose já fixada de 0,012 e as ativações do próprio modelo na geração real. Altera somente model.language_model.layers.31.mlp.down_proj.weight (1024×3584, BF16): subtrai um produto externo de posto 1 residualizado contra as 54 ativações anteriores, na direção negativa do token produzido incorretamente (` len`, id 2343). Nenhuma substituição correta foi fornecida.

O pai teve todos os textos e acertos de desenvolvimento reproduzidos. A reconstrução altera 2.025.354 valores; o registro antigo indicava 2.029.223. Portanto, não se afirma igualdade bit a bit com pesos que não foram salvos. O arquivo avaliado tem SHA256 8fd291019b20f7d327e775c05a30f5b991395718040e4ad2fe52ed986ff748ef.

## Desenvolvimento observado (recuperação, não generalização)

| Modelo | Tarefas completas | Casos | Controles | NLL âncora |
|---|---:|---:|---:|---:|
| parent | 11/16 | 69/81 | 4/4 | 3.183729251 |
| candidate | 12/16 | 72/81 | 4/4 | 3.178572655 |

## Validação independente congelada

| Modelo | Tarefas | Casos | Fora da família de sobreposição | Próximas à hipótese | Controles estritos | Limite de tokens |
|---|---:|---:|---:|---:|---:|---:|
| original | 5/24 | 71/192 | 5/20 | 0/4 | 6/12 | 5 |
| parent | 7/24 | 85/192 | 7/20 | 0/4 | 6/12 | 3 |
| candidate | 7/24 | 78/192 | 7/20 | 0/4 | 6/12 | 4 |

Candidata versus pai: 0 tarefas ganhas, 0 perdidas; 5 casos ganhos, 12 perdidos. McNemar exato bilateral por tarefa: p=1. Diferença de pass@1: 0.00 pontos percentuais; IC bootstrap empírico 95%: [0.00, 0.00].

Controles perdidos: []; ganhos: []. NLL nova: pai 3.046095580, candidata 3.034530461.

Candidata versus Qwen original: 2 tarefas ganhas e 0 perdidas; 18 casos ganhos e 11 perdidos. Diferenças herdadas da arquitetura não são atribuídas à edição.

Controles estritos versus original, por identidade (totais iguais podem ocultar trocas de acertos): {"parent": {"strict_losses": ["v4_plural", "v4_clock"], "strict_gains": ["v4_en_pt", "v4_geo"]}, "candidate": {"strict_losses": ["v4_plural", "v4_clock"], "strict_gains": ["v4_en_pt", "v4_geo"]}}. O ganho estrito da tradução v4_en_pt reflete dois sinônimos semanticamente válidos e não deve ser interpretado como melhora real de tradução.

Quatro tarefas repetidas por variante tiveram textos e acertos idênticos. Como a geração é gulosa, essas repetições verificam estabilidade, sem criar novas amostras independentes. A comparação usa o mesmo contexto, limite, tokenizer, BF16, kernels eager, cache, seed e quatro threads. Os híbridos têm 32 camadas físicas, 56 execuções de camada por passo e aproximadamente 1,02B parâmetros; o Qwen original usa suas 24 camadas e aproximadamente 0,87B parâmetros. A comparação com o original não equaliza FLOPs ou latência; a comparação pai/candidata mantém a mesma arquitetura e computação. Casos, gabaritos e implementações de referência ficaram fora das entradas do modelo. Os hashes e o protocolo foram publicados antes das saídas desta validação.

## Escopo matemático da preservação

Antes do arredondamento BF16, o efeito em uma nova ativação h é ΔW h = -0,012 ||W|| u (vᵀ h). A residualização restringe o efeito apenas nas 54 ativações anteriores da própria resposta usada na edição; a regularização torna essa proteção aproximada. O arredondamento BF16 acrescenta outro resíduo. Contextos novos fora desse conjunto podem mudar, e uma troca de token na decodificação gulosa pode alterar todo o programa seguinte. As regressões observadas são compatíveis com esse alcance limitado, sem identificar uma causa neural exclusiva de programação.

## Decisão

A generalização não foi confirmada pelos critérios registrados. Manter o checkpoint pai como melhor versão; preservar a candidata reconstruída e os resultados como experimento, sem promoção.

Critérios: {"development_gates": true, "no_fresh_case_loss": false, "no_fresh_control_loss": true, "far_task_gain": false, "paired_task_p_le_0_05": false, "new_anchor_preserved": true}.

Limites: suíte customizada pequena, criada pelo mesmo assistente que conhece a hipótese; não é auditoria cega. O controle de tradução contém um falso negativo conhecido: “Necessitamos de água limpa” é semanticamente válido, mas não consta dos aliases congelados. Os escores automáticos e o gabarito não foram alterados; uma mudança entre sinônimos válidos não demonstra ganho linguístico. Ausência de regressão nestes controles não prova preservação geral. Não é possível garantir novidade perante o pré-treino. Ganhos próximos ao problema editado podem ser especialização. Casos de uma mesma tarefa não são 192 observações independentes. Um IC bootstrap degenerado com todos os deltas zero não prova equivalência. Os conjuntos antigos reservados permaneceram fechados. Novas edições exigirão outro teste ainda não observado.

Detalhes e saídas completas: mentor/recovery_004/ e mentor/validation_004/. Estado final: avaliação concluída, nenhum processo de pesquisa prometido em segundo plano.
