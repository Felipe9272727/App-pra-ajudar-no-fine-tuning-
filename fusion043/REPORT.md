# Liquid Sense × Gemma 045

A versão 045 contém 19 blocos BF16 provenientes da Gemma 3 1B IT. Eles acrescentam 510.000.128 parâmetros aos 919.659.696 da Base Liquid Sense. O tokenizer compartilha os 248.070 IDs originais e acrescenta 129 peças. As projeções e os novos embeddings somam 2.491.392 parâmetros. O checkpoint tem 1.432.151.216 parâmetros carregados.

Foram mantidas as 56 visitas do Liquid Sense. Os blocos Gemma executam 38 vezes por token, com a atenção local ou global da camada de origem e cache independente por visita. As projeções foram alinhadas por embeddings compartilhados. Os blocos da Gemma e a Base ficaram congelados.

| Versão | Tarefas | Casos de código | Tempo em CPU |
| --- | ---: | ---: | ---: |
| Base 0.6.5 | 4/8 | 0/10 | 88,80 s |
| Tokenizer híbrido | 3/8 | 0/10 | 90,52 s |
| Gemma 045 | 4/8 | 5/10 | 176,53 s |

A fusão resolveu os cinco casos da tarefa de contar pares adjacentes negativos e falhou na cópia exata de um identificador que a Base acertou. Os dois testes de raciocínio falharam nas três variantes. O piloto registrou um ganho específico de programação e um empate no total. A versão foi publicada como experimental.

O CI passou nos 18 testes Rust, conferiu paridade exata de ativações em 12 tokens entre processamento em lote e token a token e executou o piloto a partir do arquivo `.lsmix` final. O ZIP passou na conferência de CRC. Os dois segmentos públicos retornaram HTTP 206 com os tamanhos esperados, e os SHA-256 do servidor coincidiram com os gerados no CI. [Execução no GitHub](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/actions/runs/45529006310)

Os dados do piloto estão em `reports/045-results.json`. As variantes 043 e 044 e a versão padrão 0.6.5 continuam preservadas. [Checkpoint e downloads](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/releases/tag/liquid-sense-gemma045)
