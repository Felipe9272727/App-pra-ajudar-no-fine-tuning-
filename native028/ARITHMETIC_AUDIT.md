# Auditoria exploratória da aritmética, depois da seleção fixa

Motivo: o treino usa a soma da saída BF16 com fatores de baixo posto; a avaliação
principal usa as matrizes já fundidas em BF16. Esses cálculos não são idênticos
por arredondamento. A regressão nas primeiras respostas de SFT é observada antes
deste registro. Não atribuir a regressão exclusivamente à aprendizagem ou à fusão
sem investigar a diferença. A auditoria não participa da seleção ou promoção.

Depois de terminar todos os passos do protocolo028 e fechar os workers, carregar
SFTfinal e policyfinal, um de cada vez, na forma aditiva usada no treino. Restaurar
os mesmos576tensores de fatores/controladores, congelar todos os pesos, desligar
backward e usar os mesmos dois PRIMEIROS problemas de código da validação,
sem thinking e com128tokens. Não gerar novamente as respostas fundidas: comparar
com os registros já completos. Não retreinar nem buscar doses diferentes.

Guardar IDs de tokens, casos, texto, hashes da construção e coincidência com as
respostas fundidas. São novos probes de uma forma numérica diferente, em tarefas
já observadas: não são outra validação independente. Dois probes não explicam
todas as falhas nem autorizam substituir os gates. O teste final permanece
fechado se nenhuma candidata tiver passado o protocolo principal.
