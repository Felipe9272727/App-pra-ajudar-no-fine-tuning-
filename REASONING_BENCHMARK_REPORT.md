# Liquid Sense — pesos, profundidade de loop e benchmarks públicos

Continuação de 2026-11-05 a partir do pai preservado. A hipótese 002 anterior continuou arquivada. Não foram usados gradientes, otimizadores ou soluções de referência nas entradas de programação.

## Ativações e intervenções diretas

Na geração real, o contraste entre erros e tarefas corretas selecionou as camadas 25, 27 e 26. Foram preservados estados de tokens, coordenadas mais ativas e deriva entre visitas. Essas associações não identificam neurônios exclusivos de pensamento.

| Hipótese | Intervenção | Resultado |
|---|---|---|
| 003 | Pesos de visita [0,95;0,05]→[0,925;0,075] nas três camadas selecionadas | Descartada: sem ganho na triagem |
| 004 | Edição negativa de posto 1 na MLP final; dose 0,006; preservação de 137 ativações | Descartada: não passou nos critérios completos; NLL das âncoras aumentou |
| 005 | Terceira visita seletiva: 80 execuções de camada, com cache independente | Descartada: sem ganho na triagem |

A edição 004 fez 69→70 casos de desenvolvimento, com 1 ganhos e 0 perdas por identidade de caso. Controles: 4→4/4. NLL de linguagem: 3.183729251→3.189104915. A piora da NLL violou o gate predefinido; não foi escondida nem compensada pelo acerto de programação. NLL é uma medida auxiliar e não equivale a uma avaliação completa de fluência.

A terceira visita foi tratada como um experimento de computação adicional. Seus pesos e os do grupo de controle ficaram arquivados; mais visitas ou texto de raciocínio não demonstram melhor raciocínio. O teste técnico de cache passou em duas, três e quatro visitas (56/80/104 execuções).

## Comparação externa independente

Fontes: [LFM3 oficial](https://huggingface.co/LiquidAI/LFM3-1.7B), que publica LiveCodeBench v6 e IFEval; [LFM2.5-Thinking oficial](https://www.liquid.ai/blog/lfm2-5-1-2b-thinking-on-device-reasoning-under-1gb), que publica GSM8K. Os conjuntos locais são subconjuntos fixados antes das saídas; não reproduzem os protocolos completos do fornecedor.

| Subconjunto | Modelo | Acertos completos | Casos | Truncamentos |
|---|---|---:|---:|---:|
| LiveCodeBench-v6-subset | original | 1/8 | 16/128 | 2 |
| LiveCodeBench-v6-subset | liquid | 2/8 | 32/128 | 1 |
| GSM8K-zero-shot-subset | original | 1/16 | 1/16 | 5 |
| GSM8K-zero-shot-subset | liquid | 1/16 | 1/16 | 4 |
| IFEval-filtered-subset | original | 8/12 | 8/12 | 6 |
| IFEval-filtered-subset | liquid | 8/12 | 8/12 | 9 |

LiveCodeBench: oito problemas fáceis de stdin/stdout do incremento test6 da release_v6, sem os exemplos de entrada/saída no prompt, com até 16 casos privados originais por problema; comparação de stdout normalizada em espaços. GSM8K: 16 questões zero-shot, sem raciocínios de referência. IFEval: 12 instruções filtradas, com verificadores oficiais estritos e flexíveis preservados. O executor de código restringe construções e identificadores Python além de isolar o processo; falhas de contrato, execução, resposta e truncamento são mantidas nas saídas. Estas restrições e amostras impedem comparação direta com percentuais de leaderboard.

Mesmas entradas, contexto, tokenizer, BF16/eager, cache, seed 0 e quatro threads. Limites de saída: 384/64/192 tokens por família. Identidade e prompts de marca ficam fora das avaliações. O híbrido ampliado tem aproximadamente 1,02B parâmetros e maior custo interno que o Qwen original de aproximadamente 0,87B; isto não é uma comparação com FLOPs iguais. Intervalos Wilson e comparações pareadas por tarefa estão em summary.json. As amostras são pequenas e convenientes, com viés de seleção documentado; não estabelecem superioridade geral ou ausência de contaminação pelo pré-treino.

## Seleção e identidade

Seleção: {"selected": "parent", "checkpoint": "rsi100/checkpoints/best.pt", "checkpoint_sha256": "46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8", "patch": null, "checkpoint_promoted": false, "reason": "Neither authored edit passed development gates; keep unchanged hybrid"}.

O chat e o perfil apresentam Liquid Sense como um projeto independente conduzido por um desenvolvedor, com origem no Qwen e adaptações inspiradas em SenseNova/Liquid. O crédito ao projeto não apaga a origem da base pré-treinada. A identidade é uma configuração de aplicação; não foi atribuída a aprendizado de pesos nem somada aos resultados de capacidade. O teste real está em reasoning/identity_probe.json.

Pesos anteriores, candidatas, ativações, hipóteses, fontes e decisões permanecem no GitHub. Os resultados destes benchmarks não serão usados para ajustar outra candidata neste ciclo. Execução encerrada ao término do relatório; nenhum serviço local contínuo é prometido.
