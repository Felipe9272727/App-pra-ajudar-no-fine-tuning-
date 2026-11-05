# Métrica contra 4B e rastreio integral de tensores nos erros — diagnóstico 011

A análise foi concluída sobre o **Liquid Sense preservado**, não sobre os
candidatos nativos rejeitados. O checkpoint continua com SHA256
`46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8`.
Todos os 699 hashes de parâmetros permaneceram idênticos antes/depois do
rastreio e das intervenções de ativação. Nenhum peso foi editado, nenhum
gradiente/backward/otimizador foi usado, nenhum candidato foi promovido.
Nenhuma solução correta ou token-alvo do avaliador entrou no contexto.

## Métrica concreta de objetivo

**Delta4B_pp = 100 × [pass@1(Liquid Sense) − pass@1(Qwen3.5-4B)].**

Cada problema vale um acerto somente quando uma única resposta passa todos
os seus casos fixos. Casos parciais são uma medida secundária. Por exemplo,
aumentar casos corretos mantendo o mesmo número de problemas resolvidos não
melhora a métrica principal. O objetivo exige Delta4B positivo, com limite
inferior do intervalo de bootstrap pareado de 95% acima de zero, teste pareado
unilateral exato com p<0,05, ao menos 100 problemas novos congelados antes das
saídas, checkpoint congelado e retenção dos controles gerais/de linguagem.
As reamostragens são de problemas inteiros, não de casos correlacionados.
O bootstrap estatístico não modifica parâmetros do modelo.

O conjunto público de referência definido é uma nova seleção LiveCodeBench,
com IDs, enunciados, gabaritos, orçamento, modo thinking e avaliador fixados
antes das saídas. A seleção final ainda não foi executada. A comparação deve
usar os mesmos problemas, contexto, precisão, orçamento de geração, amostragem
e avaliador; custos do loop e recursos de execução devem ser informados
separadamente. A conclusão seria superioridade de programação nesse protocolo,
não aumento geral de inteligência.

**Estado numérico atual:** 11/16
problemas completos (68.75%) e
69/81 casos
(85.19%) no
**desenvolvimento interno já observado**. Esses números não são LiveCodeBench
nem validação independente. **Delta4B está não medido (`null`)**, porque a
referência de 4B não foi executada; seu resultado não foi inventado nem tomado
de tabela de fornecedor com outro protocolo.

Referência fixada: `Qwen/Qwen3.5-4B`, revisão `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`.
Seus arquivos de pesos somam 9,319,737,856 bytes; hashes
dos dois shards e cinco arquivos auxiliares foram registrados. O ambiente
local tem 8 GiB de RAM e tinha cerca de 2,1 GB de disco livre. Não foi feito
download de 9,32 GB, troca para uma quantização diferente, uso de API paga ou
ativação de runner maior. `diagnostic011/evaluate_4b.py` está implementado
para executar uma referência pareada de desenvolvimento numa máquina que já
tenha esse snapshot, verificando hashes e igualdade dos tokens de entrada.
Ele não marca desenvolvimento como teste inédito.

Fontes primárias: [modelo Qwen4B](https://huggingface.co/Qwen/Qwen3.5-4B)
e [LiveCodeBench](https://livecodebench.github.io/).

## O que foi capturado de verdade

Cinco respostas erradas e duas corretas foram geradas novamente somente para
**nova instrumentação**, sem repetir seleção/edição de experimento anterior.
Todos os textos e bits de avaliação reproduziram exatamente os anteriores.
Mesmos prompts, greedy, thinking desativado, 160 tokens máximos, BF16 e quatro
threads. Houve **417 decisões autoregressivas**, com **813 slots de chamadas
de módulos por decisão**, distinguindo as duas visitas dos blocos
compartilhados: 339.021 observações de chamadas, cada uma com 12 estatísticas
de entrada/saída do último token de decisão. Não foram respostas antigas
forçadas no modelo durante a captura.

O TorchDispatch rastreou os **699 tensores únicos de parâmetros**. Foram
acessados **546 tanto nos erros quanto nos acertos**; os outros 153 são do
encoder visual, não usado nessas entradas. Nenhum parâmetro foi acessado
exclusivamente no grupo de erros desses sete exemplos. Embedding/head
compartilhados foram contados uma vez e suas utilizações foram registradas.
Assim, acesso a um peso não equivale a responsabilidade por uma falha.

Foram separados operadores matemáticos, views/metadados e transformações de
dtype/cópia. Esse é um rastreio de armazenamento bruto; cópias derivadas podem
mudar de armazenamento, portanto ele não pretende ser um grafo completo de
todas as dependências numéricas. Todos os pesos de convolução funcional são
contemplados mesmo quando `nn.Conv1d.forward` não é chamado; a associação ao
ancestral executado fica explícita. Normas gated incluem todos os heads do
último token, sem confundir o último head com o último token.

O escopo abrange todos os parâmetros nomeados, estatísticas de módulos a
cada passo e vetores completos do último token em **21 pontos registrados**
(três por resposta), nos dtypes reais. Inclui o início de cada trecho suspeito
dos cinco erros, confirmado depois contra os tokens realmente consumidos.
Os 417 IDs foram conferidos com as entradas seguintes do embedding e o EOS
único configurado. Não houve NaN/Inf nas ativações registradas.

Há 64 tensores zerados entre os acessados: os 16 projetores que neutralizam
as oito camadas adicionais e os 48 pesos de entrada dos roteadores mHC.
Eles continuam sendo lidos. As demais matrizes desses blocos podem produzir
ativações internas mesmo quando o projetor de saída neutraliza sua contribuição.
Isso é distinto de peso não acessado e distinto de prova de erro.

## Erros efetivamente observados

| Resposta | Casos corretos | Tokens | Leitura semântica do código próprio |
|---|---:|---:|---|
| prefix_sums | 2/5 | 32 | Repete a soma total para cada elemento, perdendo o estado de acumulação por posição. |
| overlap_count | 2/5 | 72 | O avanço após encontrar uma ocorrência pode saltar ocorrências sobrepostas. |
| run_lengths | 2/5 | 84 | Produz comprimentos locais unitários e não mantém a contagem completa de cada grupo. |
| rotate_right | 3/5 | 43 | O fatiamento gerado segue a direção oposta à solicitada em parte dos casos. |
| longest_run | 4/5 | 98 | O retorno pode ignorar a maior sequência quando ela termina no final da entrada. |

Os dois controles de programação, `sum_abs` e `binary_search`, mantiveram
10/10 casos. Todos os cinco erros terminaram por EOS antes do teto de 160
tokens. Com os mesmos pesos, contexto e geração gulosa, aumentar apenas esse
teto não mudaria essas saídas já encerradas. Isso não prova que outro modo
de raciocínio seria inútil; separa esses erros de truncamento da resposta.

## O que destacou na análise de todos os tensores

As maiores diferenças exploratórias de RMS do leitor entre os cinco erros e
os dois acertos apareceram nas projeções `linear_attn.in_proj_a.weight`:

| Camada física | RMS médio nos erros | RMS médio nos acertos | Diferença relativa |
|---|---:|---:|---:|
| 25 | 2.842111 | 2.427840 | 17.06% |
| 6 | 1.280037 | 1.107240 | 15.61% |
| 28 | 2.568515 | 2.234858 | 14.93% |

São os nomes completos
`model.language_model.layers.25.linear_attn.in_proj_a.weight`,
`model.language_model.layers.6.linear_attn.in_proj_a.weight` e
`model.language_model.layers.28.linear_attn.in_proj_a.weight`.
As camadas 25 e 6 pertencem ao loop; a 28 fica depois dele.
No DeltaNet, a projeção a participa de
`g = -exp(A_log) * softplus(a + dt_bias)`, controlando o decaimento da memória.
**RMS maior não implica, sozinho, maior esquecimento:** sinal, offsets e
valores por head importam. Esses são candidatos a investigação, não tensores
identificados como defeituosos ou pesos de inteligência.

A comparação dá o mesmo peso a cada resposta e preserva cada visita. Há
fortes fatores de confusão: problemas, vocabulário e comprimentos diferentes,
poucos exemplos e seleção dos maiores contrastes entre muitos tensores.
Nenhuma significância causal foi atribuída ao ranking.
Também foram calculados momentos de entrada por **todos os seus canais** e
proxies de energia linear usando todas as colunas de cada matriz compatível.
O proxy ignora covariâncias cruzadas e não é gradiente ou direção autorizada
de edição. A tabela integral contém todos os 699 parâmetros, inclusive os
não observados, com dtypes, formas, contagens de acesso e associação aos leitores.

## Teste adicional de influência local

Após registrar camadas/doses/protocolo e antes das novas saídas, foram feitas
**30 intervenções temporárias**: em cada um dos cinco contextos suspeitos,
escalar somente a última ativação a de uma das três camadas para 0,99 ou 1,01,
preservando o resto do contexto e as passagens do loop. Os prefixos eram
exclusivamente tokens do próprio aluno; nenhum alvo correto foi introduzido.
A mudança efetiva após BF16 foi registrada por visita.

Todas as intervenções alteraram os logits, com diferença absoluta máxima
**0.250000**. **Nenhuma das 30 mudou o
argmax** contra seu baseline de prefixo completo. Portanto há influência
numérica local, mas não evidência de correção do algoritmo ou ganho da métrica.
A experiência não testa acumulação ao longo de uma geração completa.
Não foi salvo peso modificado ou atribuído aumento de inteligência.

Houve uma distinção relevante: em `longest_run`, o baseline que recalcula
inteiramente o mesmo prefixo escolheu um token diferente do caminho original
com cache, antes de qualquer intervenção. Os outros quatro concordaram.
Isso foi separado do efeito das intervenções. Não foi contado como ganho;
a origem da diferença numérica não foi isolada. Pesquisas futuras precisam
comparar o mesmo caminho de inferência para não confundir essa variação com
melhoria de pesos. O rastreio autoregressivo principal continuou reproduzindo
exatamente todas as sete respostas antigas.

## Artefatos e retomada

Nove novos testes técnicos passaram, incluindo leitura funcional de convolução,
aliases, pesos zerados, casts, seleção de heads/tokens e recusa de métricas 4B
sem referência ou com protocolo diferente. Os dados de observação somam
216,106,259 bytes, preservados sem perda em
84,938,360 bytes e 11 partes, com hashes de arquivo e membros.

- `diagnostic011/metric.py`, `metric_definition.json`, `metric_current.json`:
  objetivo executável, critérios e valor não medido contra 4B.
- `all_tensors.csv` e `all_tensors.jsonl`: os 699 tensores analisados.
- `analysis.json`: cobertura, contrastes e proxies por uso/visita.
- `capture_*.json`, `capture_complete.json`, `token_integrity.json`: saídas,
  casos e evidência de captura real.
- `activation_archive.json`, `activation_archive/part_*.bin`:
  perfis numéricos completos, momentos por canal e snapshots.
- `python diagnostic011/restore_traces.py`: restaura e verifica os oito
  arquivos de observação. Não precisa gerar novamente respostas concluídas.
- `GATE_PROBE_PROTOCOL.md`, `gate_probe_frozen.json`, `gate_probe.json`:
  protocolo e todos os efeitos das intervenções sem edição de pesos.
- `evaluate_4b.py`, `reference_4b*.json`: executor offline e referência fixada.
- `frozen.json`, `runtime.json`, `artifact_integrity.json`, `status.json`:
  proveniência, ambiente, integridade e estado real.

Os oito testes RSI100 de validação independente permanecem sem uso. Não houve
nova avaliação geral/de linguagem, porque nenhum peso/candidato foi alterado;
os dois controles aqui são de programação. O checkpoint escolhido permanece
intacto. O diagnóstico não demonstrou superioridade sobre um modelo de 4B,
mas deixou a métrica definida e os dados necessários para hipóteses menores
e verificáveis. Não há pesquisa prometida em segundo plano ao encerrar.
