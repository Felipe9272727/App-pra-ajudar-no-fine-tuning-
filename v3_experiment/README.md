# V3 NCM — EXPERIMENTO

Nome: **liquid sense 0.8 b LOOP V3 NCM — EXPERIMENTO**.
Esta branch não substitui nem promove o modelo da branch V2 em avaliação.

## O que foi implementado

Adaptação experimental do mecanismo central NCM para respostas curtas:
um autoencoder linear de bytes aprendido, quantização vetorial residual em
quatro escalas **1 → 2 → 4 → 8**, e previsão paralela dos códigos de cada
escala condicionada pelo híbrido Qwen/SenseNova/Liquid. A implementação de
quantização é a dos autores, vendorizada com licença MIT e revisão fixa.

O encoder usa PCA; os codebooks são aprendidos por k-means; o decoder de
bytes e as novas matrizes de previsão são aprendidos por regressão ridge
fechada. Não há autograd, backward ou otimizadores de gradiente. O backbone
herda os pesos da candidata 2 da V2, que ainda é uma candidata experimental.

Em cada nível, todos os códigos são previstos em uma passagem, sem receber
o gabarito. O próximo nível recebe somente a reconstrução dos códigos já
previstos. Não há calculadora, busca, professor externo ou fallback
autoregressivo escondido durante a avaliação da V3.

O backbone conserva 32 camadas, 56 execuções, mHC de duas vias, segunda visita
ativa, convolução de sete posições e janelas de atenção de 256 tokens.
As consultas mantêm a causalidade Qwen/GDN. Não são os blocos bidirecionais
do Transformer oficial NCM. O nome 0,8B vem da base; o híbrido já carregava
aproximadamente 1,02B parâmetros, além dos novos módulos deste experimento.

**Não é reprodução integral do NCM oficial:** não usamos seu Transformer
VQ-VAE treinado de ponta a ponta nem seus checkpoints. Esta V3 testa uma
adaptação estrutural, aprendida sem gradientes, com limite de oito bytes
de resposta. Não é um assistente geral NCM nem uma promessa de ganhos de
10–31×, que os autores mediram contra difusão em tarefas e hardware próprios.

## Dados e comparação

- 128 exemplos supervisionados: aritmética, saída de Python e operações de texto.
- 4096 sequências sintéticas adicionais para aprender o codec, sem perguntas de teste.
- 16 perguntas de desenvolvimento para escolher entre três regularizações fixas.
- 48 perguntas novas de teste, incluindo casos com operandos e letras fora da distribuição.
- Três variantes: Qwen original, híbrido pai da candidata 2, V3 com NCM adaptado.

Perguntas e respostas são fixadas antes de testar. Gabaritos são calculados
por código apenas na criação dos dados e na pontuação, nunca na inferência.
Maiúsculas/minúsculas são avaliadas corretamente nas operações textuais.
Relatamos acerto exato, conteúdo numérico, erros por família, latência,
reconstrução do codec e todas as respostas brutas, incluindo fracassos.

O Qwen e o pai geram até oito tokens BPE. A V3 gera até oito bytes em quatro
níveis, com um prefill e 15 consultas internas. Os orçamentos computacionais
não são iguais; todos os gabaritos cabem nos dois formatos. Velocidade só faz
sentido junto da qualidade. Não compare esses escores com os conjuntos antigos.

## Recuperação dos pesos de referência

O ambiente temporário anterior foi reiniciado e o download grande do upstream
não ficou disponível nesta execução. Recuperamos o port v1 salvo, sem treino,
e invertemos suas escalas de saída, todas potências de dois. Isso restaura
os 24 conjuntos de tensores do Qwen sem estimar pesos; as cópias duplicadas
são comparadas bit a bit. A serialização safetensors resultante possui hash
de arquivo diferente do original, portanto registramos essa distinção.
`original_recovery.json` e `reference_verification.json` documentam a
proveniência e a comparação com sondas funcionais já registradas do original.
Essas sondas apresentaram diferença de NLL em relação ao ambiente anterior;
não atribuímos a diferença automaticamente ao hardware ou ao formato do arquivo.
O relatório identifica a referência como Qwen com tensores reconstruídos e
registra a limitação. Todas as variantes são medidas novamente neste ambiente;
nenhum escore antigo é misturado ao novo benchmark.

## Reproduzir

Depois de preparar `upstream/` e `sensenova_port/` com os scripts da raiz:

```bash
python v3_experiment/make_data.py
python v3_experiment/train.py codec
python v3_experiment/train.py collect
python v3_experiment/train.py fit
python v3_experiment/evaluate.py develop
# A seleção fica congelada antes do teste:
python v3_experiment/evaluate.py heldout --variant qwen_original
python v3_experiment/evaluate.py heldout --variant v2_parent
python v3_experiment/evaluate.py heldout --variant v3_ncm
```

Não refaça a seleção após observar o teste. Os checkpoints incrementais,
receitas e hashes permitem carregar a V3 sem repetir o ajuste. A inferência
NCM é chamada por `NCMExperiment.generate(question)`, que não aceita gabarito.

## Fontes

- https://hazyresearch.stanford.edu/blog/2026-10-12-ncm
- https://arxiv.org/abs/2610.14162
- https://github.com/HazyResearch/ncm — revisão `c70274273f489abc73832b2b98584a8483b6b203`

`vendor/ncm/` conserva o quantizador e suas dependências locais. Só os imports
relativos foram ajustados. A arquitetura NCM pertence aos autores; esta
adaptação independente não é uma publicação oficial Hazy Research.
