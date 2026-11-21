Atualização para o Liquid Sense 0.6.5. Instale o atualizador por cima do anterior, abra e toque em **Atualizar para 0.6.5**. Confirme no Android. O atualizador aproveita os pesos da 0.6.4 instalada e preserva as conversas.

O motor local processa o contexto em blocos de quatro tokens. Na medição em ARM64, a mediana até o primeiro token passou de **1,61 s para 1,03 s** na Base e de **1,70 s para 1,12 s** no Loop 029 época 2, com estados e logits equivalentes bit a bit para a entrada testada. A vazão depois do primeiro token ficou próxima da anterior. A velocidade no Snapdragon ainda depende do aparelho e da conversa.

Em perguntas diretas de identidade no modo GPU, o app apresenta o **Liquid Sense** e explica sua origem no Qwen3.5 usando os dados oficiais do projeto. Essa apresentação funciona sem reservar GPU.
