# Liquid Sense — diagnóstico de erros e edições 006/007

Estado deste registro: pesquisa de pesos concluída sem promoção; extensão
pareada de raciocínio para 1.024 tokens ainda em execução. Os resultados
abaixo sobre pesos já estão concluídos. Não há execução permanente entre turnos.

O checkpoint selecionado continua sendo
[`rsi100/checkpoints/best.pt`](rsi100/checkpoints/best.pt), SHA256
`46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8`.
A base nominal é Qwen3.5-0.8B; o híbrido carrega 1.020.252.592 parâmetros.
Loop/mHC e operadores inspirados na Liquid permanecem presentes e ativos.
O bloco central tem duas passagens, com 56 execuções de camadas, incluindo
as oito camadas inseridas que ainda são neutras.

## O que explica os resultados baixos medidos

Há erros de lógica que terminam normalmente: devolver a direção original em
vez da oposta e imprimir a soma quando o enunciado pede seu quadrado.
Há também erros de formato, programas repetidos, repetição numérica e cortes
antes da conclusão. Não são todos o mesmo problema.

No piloto público anterior, o híbrido atingiu o limite em 4/16 respostas de
matemática, 1/8 de programação e 9/12 de instruções. O modo de raciocínio
estava desligado; os limites eram 64, 384 e 192 tokens, respectivamente.
Alguns textos cortados ainda satisfazem o verificador formal do IFEval; isso
não demonstra que a resposta inteira tenha boa qualidade semântica.

O avaliador de programas também rejeitava variáveis Python comuns como `_`
e não expunha `iter`/`next`. Uma versão separada corrigiu essas restrições e
reavaliou os mesmos programas, sem nova geração nem alteração do gabarito.
O resultado continuou Qwen 1/8 e híbrido 2/8: as restrições não explicavam
esses totais baixos. O avaliador e os resultados primários ficaram intactos.

Outra limitação foi comprovada: os 48 tensores de entrada dos roteadores mHC
estão zerados e seus pares de ganhos de saída são iguais. Durante as seis
gerações diagnósticas do híbrido, as 201.312 chamadas medidas apresentaram
diferença zero entre os dois fluxos de entrada. Os fluxos operavam em igualdade,
sem roteamento dependente da entrada. Isso limita o benefício esperado do mHC;
não estabelece, isoladamente, a causa de cada resposta errada.

## Comparação direta nos mesmos 16 problemas de desenvolvimento

Quatro threads, BF16 com roteadores FP32, atenção eager, cache, geração gulosa,
raciocínio desligado, 160 tokens para código e 32 para os controles. Mesmo
tokenizador, prompts, testes e condições para todos. Não são problemas inéditos.

| Variante | Tarefas completas | Casos corretos | Controles | NLL de linguagem |
|---|---:|---:|---:|---:|
| Qwen original | 12/16 | 66/81 | 4/4 | 3,186716 |
| Híbrido pai preservado | 11/16 | 69/81 | 4/4 | 3,183729 |
| Edição 006, experimental | 11/16 | 70/81 | 4/4 | 3,185466 |

O pai ganha sete casos e perde quatro contra o original; também resolve uma
tarefa completa a menos. Entre as diferenças estão `overlap_count` (Qwen5/5,
pai2/5) e `longest_run` (5/5 contra4/5). Há ganhos em outros problemas.
Portanto, o total de casos maior não demonstra superioridade geral do híbrido.

## Edição 006: proteção de linguagem no ajuste negativo

Alterou diretamente
`model.language_model.layers.31.mlp.down_proj.weight`, BF16, [1024,3584].
Usou o estado real de decodificação antes do próprio token errado `[k`
(ID6521, posição35) no problema de rotação. Nenhum substituto correto foi
fornecido. A direção foi residualizada por SVD contra 137 estados de código
e 149 estados de textos comuns; dose relativa fixada em0,006, sem gradientes.

Foram alterados 1.858.254 valores BF16. O ajuste ganhou um caso de rotação,
sem perder casos corretos medidos, mas não ganhou tarefa completa. A NLL piorou
0,001736522 contra o pai, ultrapassando a tolerância de1e-6 pré-registrada.
Foi rejeitado pelo critério conservador de preservação.

A proteção ideal não sobrevive integralmente ao arredondamento: a norma máxima
da perturbação nos estados protegidos foi de aproximadamente0,0000099 antes
da conversão e0,01032 depois. O erro de arredondamento corresponde a21,7% da
norma da edição ideal. Proteger uma subdireção não garante preservar o modelo.
As âncoras usadas nessa proteção são desenvolvimento, não validação independente.

O arquivo de atribuição apresenta contribuições lineares e coordenadas reais
alteradas. Esses valores omitem o residual e a RMSNorm final; não são a
probabilidade do token nem prova de um conjunto único de pesos culpados.

## Edição 007: separar os fluxos mHC

Hipótese separada, pré-registrada depois da rejeição006. Alterou somente dois
parâmetros FP32 de `model.language_model.layers.25.mhc_ffn.bias`, índices2/3,
para `[-log(17/15), +log(17/15)]`. A camada25 veio do contraste de ativações
de erros contra controles já medido, sem escolha por novos resultados.

Os ganhos tornam-se aproximadamente15/16 e17/16. A média dos multiplicadores
por passagem também coincide com o pai depois da conversão BF16; produtos,
somas e camadas seguintes ainda podem mudar o resultado. Um controle inverso
usou os sinais trocados, com a mesma intensidade, sem poder ser selecionado.
A proposta inicial de logits0,2 foi substituída por esse cálculo analítico
antes de qualquer construção ou geração007, sem feedback de acurácia.

Ambas as intervenções separaram os fluxos na camada26: diferença máxima
medida0,0546875. Ambas mantiveram25/31 casos da triagem, com zero ganhos e
zero perdas. A intervenção estrutural funcionou; o benefício de programação
não apareceu. Candidata rejeitada sem consumir o teste reservado.

## Raciocínio e orçamento de saída

Diagnóstico separado com duas questões GSM8K e um programa LiveCodeBench já
observados, sem identidade do chat e sem respostas nos prompts. Os dois modelos
foram testados com raciocínio ligado/desligado e512 tokens, sempre sem amostragem.
Isso evita confundir ativação do modo com uma mudança simultânea de temperatura.

Em512 tokens, o Qwen entregou uma resposta final correta no modo de raciocínio;
o híbrido não concluiu nenhuma das três. No problema do carro, o Qwen concluiu
em309 tokens; o híbrido calculou a quantidade correta, mas entrou em reverificações
de instruções e não concluiu até512. No problema de frações, o Qwen já tinha
o cálculo correto no texto, mas a resposta final foi cortada. Não contei esse
texto intermediário como uma resposta concluída.

Está sendo executada a extensão pré-registrada de *todas* as respostas de
raciocínio que atingiram o limite, nos dois modelos, para1.024 tokens. Saídas
já encerradas são reutilizadas; nas reexecuções, os primeiros512 tokens precisam
reproduzir exatamente o texto anterior. Não há seleção por acerto.

O [cartão oficial do Qwen na revisão usada](https://huggingface.co/Qwen/Qwen3.5-0.8B/blob/2fc06364715b967f1860aea9cf38778875588b17/README.md)
alerta sobre repetições sem término no modo de raciocínio do0.8B. Recomenda
orçamentos e amostragem diferentes deste piloto de CPU. Nossos resultados
não equivalem aos benchmarks oficiais nem medem o desempenho máximo possível.

## Preservação e evidências

Nenhuma edição nova foi promovida. Não houve backward, fine-tuning convencional,
otimizador, busca aleatória de pesos ou solução correta entregue à geração.
As 8 tarefas de validação RSI100 continuam sem execução neste ciclo, porque
nenhuma candidata passou pelos requisitos de desenvolvimento. Os benchmarks
públicos anteriores permanecem observados e não são um novo teste final.

- [Protocolos e estado](reasoning/cycle2/status.json),
  [edição006](reasoning/cycle2/PROTOCOL.md),
  [edição007](reasoning/cycle2/ROUTER007_PROTOCOL.md).
- [Decisão006](reasoning/cycle2/trial_006.json),
  [decisão007](reasoning/cycle2/trial_007.json),
  [seleção preservada](reasoning/cycle2/selection.json).
- [Atribuição e limites](reasoning/cycle2/attribution.json),
  [auditoria dos fluxos](reasoning/cycle2/router_runtime_audit.json),
  [auditoria do avaliador](reasoning/cycle2/judge_audit.json).

Os pesos exatos, direções e traços estão versionados em `reasoning/cycle2/`.
Verificações técnicas:41 testes passaram; os17 arquivos congelados do piloto
público anterior mantêm seus hashes. O modo experimental de raciocínio no chat
é configuração de inferência, sem alegação de melhoria aprendida nos pesos.
