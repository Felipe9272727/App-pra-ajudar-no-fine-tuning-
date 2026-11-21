# Liquid Sense 0.6.5

O motor Rust processa o contexto em blocos de quatro tokens. Cada produto matricial lê os pesos BF16 uma vez por bloco, acumulando cada produto escalar na mesma ordem que antes. Os estados recorrentes e os caches de atenção avançam token por token dentro de cada visita. O motor calcula as rotações posicionais uma vez por posição e percorre os valores da atenção em ordem contígua. A geração continua sendo autorregressiva.

## Medição com os pesos do Android

O comparativo usou os mesmos 20 tokens de entrada, 8 passos de decodificação e quatro execuções medidas por variante depois do aquecimento. A referência é o caminho sem as mudanças no mesmo binário de teste. Os tempos de primeiro token incluem toda a leitura da entrada e o primeiro cálculo de logits.

| CPU | Checkpoint | Primeiro token antes | Primeiro token depois | Decodificação de 8 tokens antes → depois |
| --- | --- | ---: | ---: | ---: |
| ARM64 Neoverse-N2 | Base | 1,613 s | 1,030 s | 0,729 → 0,743 s |
| ARM64 Neoverse-N2 | Loop 029, época 2 | 1,702 s | 1,120 s | 0,775 → 0,781 s |
| AMD EPYC x86-64 | Base | 1,938 s | 0,877 s | 0,886 → 0,849 s |
| AMD EPYC x86-64 | Loop 029, época 2 | 2,094 s | 1,048 s | 0,969 → 0,957 s |

A verificação bit a bit comparou os estados das 56 visitas, os 248.320 logits, os tokens gerados e os caches. A leitura em bloco também produziu os mesmos estados, logits e caches que a leitura token a token para os 20 tokens. O pacote BF16 e a edição treinada têm os mesmos SHA-256 do APK 0.6.4. Os dados não medem o Snapdragon 7s Gen 2. [Dados ARM64](reports/arm-prefill) · [Base x86-64](reports/base-x86_64.json) · [Época 2 x86-64](reports/epoch02-x86_64.json)

## Identidade do Liquid Sense

Para perguntas diretas de apresentação, o modo GPU do app e o chat web apresentam o Liquid Sense, dão crédito ao desenvolvedor independente e explicam a origem no Qwen3.5. Essa apresentação usa os dados oficiais do projeto e dispensa a cota do ZeroGPU. O chat web foi verificado ao vivo em acesso anônimo. [Teste público](reports/live_space_identity.json)
