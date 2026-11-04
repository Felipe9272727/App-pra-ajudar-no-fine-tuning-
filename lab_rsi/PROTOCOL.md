# RSI ciclo 2: edição direta iterativa

Fonte preservada: piloto em `86e3f6b22a7e809e23883bd982e54523225c0478`.
A V3 está arquivada na branch do experimento. Ela não é o modelo pai.

O assistente controla um ciclo limitado de três etapas. Não é RSI autônomo.
Nenhum gradiente, backward ou otimizador de gradiente será usado.
As três etapas alteram diretamente a matriz BF16 existente
`layers.31.mlp.down_proj.weight`, guardada integralmente em checkpoints.
A base ativa mantém loop/mHC SenseNova e operadores inspirados em Liquid.
Não são os modelos SenseNova/LFM3 completos. O nome nominal 0,8B vem do Qwen;
o híbrido ampliado carrega aproximadamente 1,02B parâmetros, visão incluída.

## Dados e regra definida antes da execução

Semente 926110402: 224 adaptação, 24 desenvolvimento, 32 validação e 80 teste.
Exclusão das perguntas anteriores em `history/`, `v2_adaptation/` e `rsi/`.
Todos os splits são distintos. Perguntas sintéticas compartilham templates;
essa avaliação mede tarefas restritas, não inteligência geral.
Há 12 textos de preservação genérica; não são perguntas de teste.
As respostas de transformação de strings respeitam a caixa das letras.

A cada etapa, o modelo atualizado fornece os logits nos prefixos corretos.
Corrigir somente o primeiro próximo token errado (inclusive EOS), preservando
os tokens anteriores corretos e posições nos textos genéricos. A diferença de
embeddings de saída fornece a direção aproximada via RMSNorm, sem autograd.
Resolver ridge fechado com lambda 0,05, margem 1,5, cap 0,10 no residual,
cap 0,02 da norma da matriz por etapa e 0,04 cumulativo. Âncoras pesam quatro.
A aritmética BF16 pode arredondar o limite ligeiramente.
As features anteriores à última MLP são independentes da matriz editada;
replay exige igualdade bit a bit com o modelo completo na criação do cache.
Não há cache de features na geração usada para decidir promoção.

Cada etapa parte da anterior, mesmo quando ela não passa em desenvolvimento.
Os três snapshots são preservados. Essa trajetória e o orçamento são fixos.
Elegível: mais respostas exatas que a base nas 24 questões de desenvolvimento,
e NLL dos textos genéricos no máximo 110% da base. As duas melhores elegíveis
por acerto exato (NLL desempata) seguem à validação de geração completa.
Promoção: estritamente mais acertos exatos e nenhum declínio agregado nos
controles não numéricos da validação. Priorizar validação exata, depois
desenvolvimento exato e NLL para desempatar. Se nenhuma passar, manter a base.
Não escolher com teste final. Congelar e salvar a escolha antes de abri-lo.

## Execução e persistência

Workflow `.github/workflows/liquid-sense-rsi-cycle2.yml`, uma execução finita.
CPU pública padrão Ubuntu, quatro threads, no máximo quatro avaliações
simultâneas, sem runners pagos. Pesos originais têm revisão e SHA256 fixos;
a referência original não usa reconstrução da V3.
Greedy sem thinking, até 12 tokens, BF16/FP32, dois shards iguais por modelo.
Original, híbrido anterior e, se promovida, candidata sob o mesmo protocolo.
O híbrido consome mais computação que o original.

Após cada decisão, salvar pesos e estado em commit GitHub sem force push.
Alteração concorrente de fonte aborta o salvamento; artefatos ficam disponíveis
por três dias e checkpoints já commitados permanecem no Git.
Ao fim, salvar todos os resultados e parar. Não repetir o teste para seleção.
