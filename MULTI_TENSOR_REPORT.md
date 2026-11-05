# Liquid Sense — edições distribuídas 008 e 009

Concluído. Foram construídas e avaliadas duas candidatas com alterações
coordenadas em vários pontos da rede. **Nenhuma acrescentou acertos na triagem;
o checkpoint híbrido anterior continua selecionado.**

A base nominal é Qwen3.5-0.8B; o híbrido tem aproximadamente 1,02B parâmetros.
Loop/mHC, duas passagens/56 execuções e os componentes inspirados na Liquid
permaneceram ativos. Não houve expansão adicional da arquitetura neste estudo.

## Comparação medida

Mesmos sete problemas de programação, 36 casos, perguntas e gabaritos intactos,
geração gulosa com 160 tokens, cache, BF16/eager e quatro threads. Nenhuma
solução correta foi fornecida nas entradas. São problemas de desenvolvimento
já observados, não um teste novo de generalização.

| Variante | Tensores alterados | Valores alterados | Tarefas completas | Casos corretos |
|---|---:|---:|---:|---:|
| Híbrido pai preservado | referência | referência | 3/7 | 27/36 |
| 008 — ganhos distribuídos | 40 | 32.281 | 3/7 | 27/36 |
| 009 — quatro matrizes MLP | 4 | 4.994.722 | 3/7 | 27/36 |

Os controles inversos também fizeram 27/36, com zero ganhos/perdas contra o
pai. Cada candidata mudou o texto de uma resposta, sem alterar os acertos.
O Qwen original, na comparação previamente concluída com o mesmo protocolo,
fez 27/36 e 5/7 tarefas completas nesse recorte. Igualdade em casos parciais
não equivale a igual competência para resolver programas completos.

## 008: correção conjunta de ganhos em 20 camadas

Foram elegíveis os 48 vetores `input_layernorm.weight` e
`post_attention_layernorm.weight` das 24 camadas não neutras. As ativações
foram medidas nos mesmos 19 inputs sem rótulos: 12 textos comuns novos e sete
enunciados. O original só executou forward nesses inputs; não gerou programas
corretos para ensinar ao híbrido. Também foram capturadas novas estatísticas
durante sete gerações reais do pai, reproduzindo exatamente os textos salvos.

A correção foi calculada pela diferença dos segundos momentos por canal,
com amortecimento e limite de intensidade fixados antes dos resultados.
O ganho Qwen é `1+w`; a escrita respeitou essa parametrização e o BF16.
Coordenadas com mudança de ganho efetivo superior a 3% foram revertidas.
Os 40 tensores efetivamente modificados abrangem 20 camadas; os outros oito
elegíveis ficaram intactos. Todas as correções foram aplicadas juntas.

A distância média quadrática dos log-momentos caiu de 0,00196863 para
0,00161895, aproximadamente 17,8%. O controle inverso aumentou para 0,00239145.
Isso confirma o efeito sobre a distribuição interna, mas **não houve ganho
de programação**. A candidata foi rejeitada antes dos testes completos.

## 009: correção vetorial de quatro projeções MLP

Alterou diretamente as matrizes BF16 [1024,3584]:

- `model.language_model.layers.5.mlp.down_proj.weight`
- `model.language_model.layers.13.mlp.down_proj.weight`
- `model.language_model.layers.25.mlp.down_proj.weight`
- `model.language_model.layers.31.mlp.down_proj.weight`

As camadas 5/13 apresentavam desvios relevantes na medição anterior; 25 veio
do contraste de ativações de erros contra controles; 31 é o último estágio MLP.
A candidata partiu do pai intacto e não acumulou a edição 008 rejeitada.

Foram coletados vetores reais de entrada/saída desses módulos, em até 12 posições
fixas por input, nos mesmos 19 textos/enunciados. O original não recebeu nem
gerou soluções para a calibração. A regressão fechada usou somente diferenças
de vetores internos nas entradas, sem tokens-alvo, gradientes ou otimizador.

Os alvos foram `longest_run` e `overlap_count`, onde a referência original já
tinha mais acertos na comparação existente. Os outros cinco enunciados e
12 textos comuns forneceram 204 estados como restrições de preservação.
Esse direcionamento foi registrado antes de construir qualquer candidata 009;
o pré-registro inicial e seus hashes também estão preservados.

A projeção por SVD e a solução ridge produziram uma correção para cada matriz,
com amortecimento 0,25 e limite de norma relativo 0,002. O controle inverso usou
as mesmas correções com sinais trocados. Os quatro pesos foram alterados juntos.
O arredondamento e a interação entre camadas impedem tratar a preservação
linear ideal como garantia de preservação das respostas; por isso há gates.

A edição modificou 4.994.722 valores, mas continuou em 27/36, sem novo caso
correto e sem caso correto perdido na triagem. Também foi rejeitada.

## Limites e decisão

As candidatas falharam no requisito de ganho em programação. Portanto, não
avançaram aos 16 problemas completos, à NLL/controles gerais nem à validação
reservada. Não há uma nova alegação de preservação geral para essas candidatas.
As oito tarefas de validação RSI100 continuam sem execução nesta continuação.

Os resultados não mostram aumento de inteligência. Mostram que alterações
reais, inclusive em quase cinco milhões de valores de quatro matrizes, podem
mudar os estados internos sem corrigir as decisões erradas observadas.
O checkpoint selecionado permanece `rsi100/checkpoints/best.pt`, SHA256
`46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8`.

Não houve fine-tuning convencional, backward, busca aleatória de parâmetros,
modificação de gabaritos ou promoção por uma métrica interna. Os 46 testes
técnicos passaram. Foram preservados 22 novos artefatos de tensores, incluindo
pesos exatos das candidatas, controles e ativações; os pesos originais e os
checkpoints anteriores mantêm seus hashes. Nenhum processo de modelo ficou ativo.

- [Resumo de comparação](reasoning/multi009/summary.json) e
  [integridade dos artefatos](reasoning/multi009/integrity.json).
- [Protocolo 008](reasoning/multi008/PROTOCOL.md),
  [decisão 008](reasoning/multi008/trial_008.json),
  [seleção 008](reasoning/multi008/selection.json).
- [Protocolo 009](reasoning/multi009/PROTOCOL.md),
  [decisão 009](reasoning/multi009/trial_009.json),
  [seleção 009](reasoning/multi009/selection.json).
- [Manifesto das quatro matrizes candidatas](reasoning/multi009/patch_target.json)
  e [controle inverso](reasoning/multi009/patch_inverse_control.json).

A próxima questão de pesquisa é intervir nos estados reais no instante da
decisão errada durante a decodificação, além da calibração sobre enunciados.
Nenhuma nova hipótese nem execução automática foi iniciada para essa etapa.
