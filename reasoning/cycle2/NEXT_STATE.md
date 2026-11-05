# Ponto de retomada após este ciclo concluído

Nenhuma fase pendente nem processo de modelo ativo. Consulte status.json,
selection.json e ERROR_ANALYSIS_REPORT.md na raiz. Não repetir 006/007 nem
as gerações 512/1024: todas têm resultado salvo. A busca automática de 100
continua pausada em 31 rejeições e não é o próximo passo.

O checkpoint híbrido selecionado continua best.pt, hash 46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8.
Os tensores exatos de 006 e 007, inclusive controle inverso, foram preservados.
Nenhuma edição foi validada para promoção.

A questão de pesquisa ainda aberta é o controle de conclusão: nas duas
questões de matemática observadas, o híbrido chega ao cálculo, mas passa a
repetir reverificações e instruções ausentes do prompt até 1024 tokens.
O original conclui ambas; o híbrido não. Diferenciar os fluxos mHC por si só
não mudou os acertos. Mais texto de pensamento não é o objetivo da próxima
intervenção; é necessário entregar respostas corretas com retenção.

Antes de outra edição, capturar os estados reais de decodificação na transição
para essa repetição e construir uma hipótese própria com controle e protocolo.
Não há um conjunto estabelecido de "pesos de pensamento". Não foi fixada nem
executada uma hipótese 008. Não fornecer token de substituição correto nem
soluções ao modelo. Não afirmar causa única pela magnitude de uma ativação.

thinking_trace.pt guarda IDs exatos, normas e estados FP16 apenas dos primeiros
64 e últimos 16 passos da geração 512, não todos os estados intermediários em
precisão plena. Não inventar estados faltantes nem tratar um replay com outro
regime de cache como equivalente sem verificação.

Os 16 problemas de desenvolvimento, os 24 da validação 004, o piloto público 36
e os 3 deste diagnóstico estão observados. As 8 tarefas RSI100 de validação
não foram executadas: nenhum candidato novo passou desenvolvimento. Só
consumi-las após congelar uma candidata elegível e o protocolo. Não selecionar
pesos pelo resultado final ou renomear um empate como generalização.

O modo de chat --thinking é opcional e experimental; não virou padrão nem
altera os pesos. A identidade Liquid Sense continua configuração explícita
com crédito à base Qwen, fora das avaliações cruas.
