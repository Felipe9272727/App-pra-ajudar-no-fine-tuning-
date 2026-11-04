# V3 NCM — EXPERIMENTO: resultados reais

A V3 não superou o Qwen de referência neste conjunto. Não promover como melhoria geral.

## Comparação em 47 perguntas novas

| Modelo | Acerto exato | Conteúdo | Tempo médio por resposta | Parâmetros carregados |
|---|---:|---:|---:|---:|
| Qwen: tensores reconstruídos | 23/47 | 23/47 | 0.437 s | 852,985,920 |
| Pai V2 candidata 2: SenseNova + Liquid | 22/47 | 22/47 | 1.340 s | 1,020,252,592 |
| V3 NCM adaptado — EXPERIMENTO | 0/47 | 0/47 | 2.059 s | 1,021,116,466 |

Todos os resultados são de geração real; respostas incorretas ou vazias foram conservadas. O conjunto é customizado e pequeno, com aritmética, saída de Python e transformação de strings. Não é uma medida de capacidade geral de conversa ou de inteligência.

A V3 produziu 20 respostas vazias em 47 casos. O codec sozinho reconstruiu as respostas de treino, mas o gerador condicionado não reproduziu essa capacidade na geração livre.

## Por família e distribuição

| Família | Qwen reconstruído | Pai V2 | V3 |
|---|---:|---:|---:|
| addition | 5/8 | 5/8 | 0/8 |
| lowercase | 4/4 | 4/4 | 0/4 |
| multiplication | 5/7 | 6/7 | 0/7 |
| python | 0/8 | 0/8 | 0/8 |
| reverse | 1/4 | 0/4 | 0/4 |
| sort | 0/4 | 0/4 | 0/4 |
| subtraction | 5/8 | 5/8 | 0/8 |
| uppercase | 3/4 | 2/4 | 0/4 |
| id | 11/23 | 10/23 | 0/23 |
| ood | 12/24 | 12/24 | 0/24 |

## Seleção antes do teste

| Candidata de cabeça NCM | Ridge | Desenvolvimento: acertos | Acurácia de bytes |
|---|---:|---:|---:|
| head_00 | 0.1 | 0/16 | 0.1481 |
| head_01 | 1.0 | 0/16 | 0.0370 |
| head_02 | 10.0 | 0/16 | 0.0185 |

Cabeça selecionada: **head_00**, congelada em `frozen.json` antes do teste.
O teste não escolhe pesos e não promove a V3. O pai é a candidata 2 ainda experimental da V2.

## O que esta V3 efetivamente contém

- Backbone SenseNova/Liquid ativo: 32 camadas físicas, 56 execuções, mHC de duas vias, ganho da segunda visita 0,05, convolução de sete posições e SWA256.
- Autoencoder linear de bytes aprendido: PCA no encoder, codebooks RVQ do código oficial NCM aprendidos por k-means e decoder por ridge.
- Quatro níveis de códigos: 1, 2, 4 e 8 posições. Cada nível prevê todos os seus códigos em uma passagem do híbrido.
- Matrizes de previsão de códigos aprendidas por solução fechada em 128 exemplos, com 10% de corrupção dos conceitos anteriores no treino.
- Zero backward passes. Não há calculadora, gabarito ou modelo externo na inferência da V3; não há fallback autoregressivo escondido.
- Limite: oito bytes de resposta. O modelo oficial NCM usa um VQ-VAE e um gerador treinados de outra forma; esta é uma adaptação estrutural e não sua reprodução completa.

## Limites da referência e da comparação

O download grande do upstream não ficou disponível neste ambiente. Recuperamos o port v1 salvo e sem treino, invertendo as escalas de saída, todas potências de dois, para reconstruir os 24 conjuntos de tensores Qwen. As cópias duplicadas coincidem bit a bit. O arquivo safetensors resultante tem hash diferente do upstream.

Uma sonda histórica teve NLL 0.412920; a referência recuperada teve 0.443179.
Não atribuímos essa diferença automaticamente ao hardware ou ao formato. A referência é identificada como reconstruída; esta limitação impede tratar a execução como uma reprodução byte a byte do checkpoint oficial. Todas as variantes foram medidas novamente no mesmo ambiente.

O Qwen e o pai geram até oito tokens BPE; a V3 usa quatro níveis, um prefill e 15 consultas de byte, com todos os gabaritos cabendo nas duas formas. Computação e unidades de saída não são iguais. Os tempos são medidos junto da qualidade, sem extrapolar os ganhos do artigo NCM em H100.

## Respostas completas

| ID | Esperado | Qwen reconstruído | Pai V2 | V3 |
|---|---|---|---|---|
| heldout_sort_00 | bddei | ebdeid | ebdeid | ddd |
| heldout_multiplication_04 | 272 | 272 | 272 | q |
| heldout_subtraction_05 | 219 | 219 | 219 |  |
| heldout_python_07 | 875 | 155 | 19900000 | 11 |
| heldout_reverse_02 | kruv | kruv | krcrvv |  |
| heldout_addition_02 | 80 | 180 | 180 | 11 |
| heldout_python_01 | 83 | 100 | 140 | 1 |
| heldout_subtraction_06 | 497 | 135 | 147 |  |
| heldout_lowercase_00 | fge | fge | fge |  |
| heldout_lowercase_01 | ecb | ecb | ecb |  |
| heldout_python_03 | 106 | 100 | 100 | 1 |
| heldout_addition_05 | 923 | 923 | 923 | 1 |
| heldout_multiplication_06 | 247 | 207 | 247 | 8 |
| heldout_lowercase_03 | mrkz | mrkz | mrkz |  |
| heldout_reverse_03 | wtpo | wtoop | wtoptw |  |
| heldout_uppercase_03 | YMM | YMMY | YMMYMMYMMYMM | q |
| heldout_addition_01 | 95 | 195 | 195 | 11 |
| heldout_addition_04 | 556 | 556 | 556 | 88 |
| heldout_multiplication_02 | 49 | 49 | 49 |  |
| heldout_subtraction_01 | 42 | 22 | 22 | q8 |
| heldout_multiplication_07 | 238 | 238 | 238 |  |
| heldout_lowercase_02 | qqzzq | qqzzq | qqzzq |  |
| heldout_python_05 | 586 | 150 | 1441 /  | 11 |
| heldout_python_02 | 81 | 100 | 100 |  |
| heldout_subtraction_07 | 190 | 190 | 190 | 1 |
| heldout_subtraction_00 | 21 | 21 | 21 | 11 |
| heldout_sort_01 | dehhi | dhieh | dhieh | ddd |
| heldout_uppercase_00 | DHGFH | DHGFH | DHGFHFH | CqC |
| heldout_subtraction_04 | 181 | 181 | 181 |  |
| heldout_subtraction_03 | 129 | 129 | 129 | 11 |
| heldout_multiplication_01 | 45 | 45 | 45 | 4 |
| heldout_sort_03 | nsss | snss | ssns |  |
| heldout_addition_06 | 563 | 563 | 563 |  |
| heldout_subtraction_02 | 32 | 22 | 22 | 22 |
| heldout_python_04 | 0 | 144 | 144 | 11 |
| heldout_reverse_01 | ideec | iicdeecce | iicdeecce |  |
| heldout_uppercase_01 | BJIID | BJIID | BJIID |  |
| heldout_python_06 | 578 | 144 | 144 | 1 |
| heldout_uppercase_02 | WSLZS | WSLZS | WSLZS |  |
| heldout_addition_00 | 112 | 112 | 112 | 11 |
| heldout_sort_02 | lvx | xlv | xlv |  |
| heldout_multiplication_05 | 182 | 172 | 198 |  |
| heldout_multiplication_00 | 48 | 48 | 48 | 4 |
| heldout_python_00 | 75 | 14 | 145 |  |
| heldout_reverse_00 | dce | dcecd | dcececd | dd |
| heldout_addition_07 | 517 | 1517 | 1517 | 88 |
| heldout_addition_03 | 137 | 137 | 137 | 11 |

Os JSONs preservam tempos, traços dos níveis NCM, perguntas, gabaritos e hashes. Estado final: EXPERIMENTO concluído e salvo, sem promoção automática ou processo permanente de treino.
