# Treino018 — concluído, sem promoção

Foram feitas oito atualizações supervisionadas a partir do principal GERAL,
com soluções e explicações verificadas somente nos alvos de treino. As duas
visitas do Loop/mHC e os operadores temporais participaram da mesma retropropagação.
Dos329tensores/2.675.888valores elegíveis, mudaram224tensores/1.245.166valores;
269tensores tiveram gradientes não nulos em cada atualização. Os370tensores
congelados, incluindo153de visão, ficaram idênticos. Não foram treinados todos
os pesos nem um suposto conjunto exclusivo de pensamento.

| Modelo | Controles gerais | Código thinking256 | Diagnóstico thinking1024 | Tokens no diagnóstico1024 |
|---|---:|---:|---:|---:|
| Qwen original | 10/12 | 0/2 | 0/1 | 1024 |
| Liquid geral preservado | 10/12 | 0/2 | 0/1 | 1024 |
| Novo treino018 | 10/12 | 0/2 | 0/1 | 1024 |

Os12textos dos controles ficaram exatamente iguais aos do pai. Os dois
digests da geração thinking256mudaram, mas nenhuma resposta final foi
entregue: alteração de texto não se converteu em ganho de tarefa.

Os dois problemas de código são exemplos ENSINADOS do conjunto013, não validação
inédita. Controles são os mesmos12já observados, com greedy/64tokens/semthinking;
os dez acertos anteriores foram preservados. Código usa greedy, seed0, quatro
threads, prefixo thinking habilitado e gabaritos/testes fora da entrada.
A extensão1024é um único problema observado e foi registrada depois da triagem;
não reabre a seleção. Cada primeiro prefixo256de uma execução estendida teve
seu digest conferido contra o resultado256salvo. Não confundir comprimento,
atividade ou tempo com melhora. Os tempos individuais são descritivos.

A candidata falhou no requisito de ganho estrito de tarefas completas. Ela
foi preservada como experimento, sem substituir o principal. Nenhuma validação
reservada013/016/RSI100foi consumida. Não há evidência de ganho geral de
inteligência ou de desempenho contra4B.

A auditoria verificou16matrizes de saída BF16 numericamente zeradas em oito
camadas neutras,46.137.344valores. Como ficaram congeladas,60tensores anteriores
a essas saídas não podiam afetar a perda: dL/dx=WᵀdL/dy=0 quando W=0. Contagens
por família coincidem com todos os oito logs. Isso limita este escopo de treino;
não prova causa exclusiva das falhas, inclusive observadas no Qwen original.
O ganho médio da segunda visita foi0.050000001→0.049942045;
não é reforço demonstrado nem benefício de raciocínio. NEXT_TRAINING_DESIGN.md
custa um futuro treino das saídas; não foi executado como outro ensaio.

Os pesos foram salvos antes de uma asserção do auditor exigir desligar
requires_grad. A correção recuperou os699hashes por carregamento frio, sem
repetir atualizações. Código inicial/corrigido, logs, checkpoint e otimizador
estão preservados. Uma reconexão do ambiente interrompeu a primeira execução
1024sem resultado; somente fases sem resultado final foram retomadas, com
progresso64tokens e comparação de prefixo. OOMkill observado=0.

Principal selecionado: rsi100/checkpoints/best.pt,
SHA256 46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8.
Novo arquivo experimental: checkpoints/candidate.pt.gz,
SHA256 f25aac86011be54f5025f24be391a1f7076a7d4e9de234e05f4ead20ecf729ab (5337685bytes).
Restauração exata: reasoning018.restore.load_candidate. Não aplicar o loader
legado novamente depois do overlay: ele apagaria parte da adaptação.
