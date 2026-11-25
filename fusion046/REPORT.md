# Sessão de aprimoramento 046

O 046 preserva a Base Liquid Sense, os 510.000.128 pesos Gemma, o tokenizer híbrido e as duas passagens do loop do 045. O treinamento acrescentou uma correção de saída de posto 48. Foram coletadas 561 posições em 47 exemplos e executadas 160 atualizações sobre 49.152 coeficientes. A validação escolheu o passo 10, que colocou o token correto em primeiro em 86 de 96 posições supervisionadas, ante 80 no 045, num conjunto de 24 opções por posição.

## Geração independente

| Modelo | Tarefas | Casos de código | Controles | Raciocínio | Tokens nos quatro problemas de código |
| --- | ---: | ---: | ---: | ---: | ---: |
| Base Liquid Sense 0.6.5 | 5/12 | 13/20 | 3/5 | 0/3 | 261 |
| Liquid Sense × Gemma 045 | 4/12 | 10/20 | 3/5 | 0/3 | 296 |
| Liquid Sense × Gemma 046 | 6/12 | 13/20 | 4/5 | 0/3 | 118 |

O 046 ganhou a tarefa de somar múltiplos e o plural de “pão”. Nenhuma das quatro tarefas acertadas pelo 045 mudou para erro. Os três testes de raciocínio continuaram falhando. A redução de 60% em tokens de código refere-se às quatro tarefas avaliadas. A sessão comparou a qualidade das respostas com o mesmo orçamento de geração. A latência de geração e a velocidade em Android ficam fora da comparação, pois as referências e o candidato usaram executores distintos.

Os dois candidatos empataram em 10/10 casos de código na triagem, contra 5/10 do 045. Em um caso suplementar, os três aceitaram palavras que só continham o prefixo no meio. Esse caso está arquivado à parte e o placar congelado da triagem foi preservado. O candidato com os ganhos originais do loop avançou conforme o protocolo.

O marcador do candidato foi congelado antes do teste final. A troca de ambiente descartou a saída temporária do candidato e a reprodução independente do mesmo SHA-256 repetiu o placar e a contagem de tokens. As referências foram recuperadas do primeiro CI. [Execução das referências](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/actions/runs/45533084902) · [Reprodução e pacote](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/actions/runs/45696383229)

O 046 foi preservado como candidato experimental aprovado neste teste. Os pesos e as publicações anteriores continuam acessíveis. [Pacote incremental Linux](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/releases/tag/liquid-sense-gemma046)
