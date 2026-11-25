# Sessão Gemma 046

O ponto de partida é o checkpoint 045 publicado. Os 510.000.128 parâmetros de origem Gemma, a Base Liquid Sense e os IDs do tokenizer ficam preservados. O 045 interrompeu código no meio ao atingir o limite de tokens e repetiu análise quando esperávamos a resposta final. A sessão testa uma correção treinada na saída do loop e uma redistribuição controlada da contribuição dos 19 blocos nas duas passagens.

## Calibração

`corpus.py` congela treino, validação da calibração, triagem e teste final. O ajuste usa funções curtas, raciocínio curto, linguagem e exemplos de retenção. A supervisão entra somente na coleta de contextos de calibração. A triagem e a avaliação final entregam apenas a pergunta aos modelos. Os arquivos com gabaritos são lidos pelo avaliador após a geração.

A correção de saída tem posto 48. A base encontra direções nas ativações de treino. O ajuste por Adam, em 160 atualizações, modifica 49.152 coeficientes da projeção de volta e usa exemplos de retenção para limitar o desvio de respostas. O ponto de parada é escolhido pela validação da calibração e pela divergência nas âncoras. A distribuição sobre os 24 tokens candidatos serve para ajuste e diagnóstico.

O candidato `readout` preserva os ganhos do 045 no loop. O candidato `balanced` usa a mesma correção da saída e redistribui os ganhos por bloco e passagem com as magnitudes observadas no treino. A normalização mantém o orçamento quadrático de perturbação estimado na calibração. A segunda passagem recebe um pequeno peso adicional. Todas as 38 visitas Gemma continuam executando.

## Decisão

A triagem usa seis tarefas inéditas para os dois candidatos. Um candidato somente é elegível se mantiver pelo menos o número de tarefas, casos de código e controles do 045. Entre elegíveis, priorizamos tarefas, casos de código, controles e, em empate, o candidato que preserva os ganhos originais. Se ambos falharem, o melhor continua apenas como auditoria experimental. O teste final usa 12 tarefas e compara o candidato congelado com o 045 e a Base 0.6.5.

Um candidato fica elegível para seguimento quando passa a triagem, preserva os controles e o total do 045 na avaliação final e melhora o total ou os casos de código, mantendo a pontuação de código. O 045 publicado permanece disponível. Uma eventual melhora fica registrada como resultado deste teste, com o tamanho da amostra e as regressões por tarefa.
