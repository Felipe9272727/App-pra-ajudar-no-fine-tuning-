# Liquid Sense 042 · comparação com a 0.6.5

A janela circular preservou os tokens nos **39 de 39 casos** da comparação. Portas por token, cache híbrido e a combinação empataram em acertos com a 0.6.5. As portas fixas acertaram mais um item e passaram três testes unitários de uma tarefa de código. É um sinal pequeno que ficou no experimento. A versão publicada e seus pesos foram preservados. [Protocolo](PROTOCOL.md) · [Execução em ARM64](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/actions/runs/45521834827)

| Avaliação | 0.6.5 | Janela | Portas fixas | Portas por token | Cache híbrido | Combinação |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| AIME25 (amostra) | 0/6 | 0/6 | 0/6 | 0/6 | 0/6 | 0/6 |
| GPQA-Diamond | 0/6 | 0/6 | 0/6 | 0/6 | 0/6 | 0/6 |
| MMLU-Pro | 0/6 | 0/6 | **1/6** | 0/6 | 0/6 | 0/6 |
| IFBench estrito | 1/6 | 1/6 | 1/6 | 1/6 | 1/6 | 1/6 |
| AA-LCR recortado | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 |
| Código029 · tarefas completas | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 |
| Controles029 | 4/8 | 4/8 | 4/8 | 4/8 | 4/8 | 4/8 |
| Controle de recuperação | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 |
| **Total** | **5/39** | **5/39** | **6/39** | **5/39** | **5/39** | **5/39** |

Os três testes unitários ganhos pelas portas fixas vieram de `sliding_max` (3/5). A versão de referência ficou em 0/20 casos de código no total. As portas fixas passaram 3/20. Houve zero erros de inferência nos 234 pedidos da bateria. A combinação gerou 2.155 tokens contra 2.175 da referência, com o mesmo número de acertos. O tempo total das variantes ficou entre 1.079 e 1.085 segundos somados por pedido. A referência acertou 0,277 itens por minuto, as portas fixas 0,333 e a combinação 0,277. A contagem de acertos, o tempo e o orçamento são descritivos para esta amostra. [Resultados por grupo](reports/comparison.json) · [Totais](reports/totals.json) · [Respostas brutas e correções](reports/arm64-evidence.zip)

## Memória e equivalência

Na Base e na época 2, a janela preservou os 248.320 logits e o estado que ainda podia ser consultado ao cruzar a posição 256. Aos 272 tokens houve **384 KiB a menos de K/V** em cada checkpoint testado. Para uma sessão de 4.096 e 16.384 tokens, a projeção é de 90 e 378 MiB, respectivamente, sobre os vetores brutos de K/V das seis visitas locais. O teste também confirmou a equivalência ao reutilizar a janela salva. A referência e a janela tiveram a mesma quantidade de tokens na bateria e tempos próximos. As medições foram em Linux. [Base](reports/window-base.json) · [Época 2](reports/window-epoch02.json)

O cache híbrido e as portas por token passaram na comparação de causalidade entre o processamento em blocos e o processamento token a token nos dois checkpoints. A política híbrida alterou 5 das 39 gerações frente à 0.6.5. Os dois itens de AA-LCR usam trechos fixos idênticos nas duas versões, pois a menor entrada original dessa revisão tem 71.691 tokens nos metadados. O teste não determina a qualidade com a entrada completa. [Protocolo](PROTOCOL.md) · [AA-LCR](https://huggingface.co/datasets/ArtificialAnalysis/AA-LCR/tree/bdae010bbce259820c0e34c1d7cce210d966fb75)

## AIME25 completo

No x86-64, a 0.6.5 e a combinada terminaram os 30 itens, cada uma com **0/30**. Ambas atingiram o limite em todos os itens com 48 tokens de raciocínio e 24 de resposta. A combinada alterou 17 sequências. Após uma interrupção da sessão local, os primeiros 12 resultados da variante combinada foram conferidos e os 18 restantes foram executados com a mesma configuração. [Resultado por item](reports/aime25-full-x86_64.json) · [Registro da retomada](reports/aime25-execution.txt)

As configurações das portas são reproduzíveis pelo motor do experimento, com pesos da Base congelados. A janela fica disponível como variante para adoção no motor. As portas e o cache híbrido seguem experimentais. [Configurações](data) · [Calibração das portas](reports/selected_calibration.json)
