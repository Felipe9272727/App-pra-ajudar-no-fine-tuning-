# Recuperação técnica na exportação da primeira época

As48atualizações SFT terminaram e foram salvas em `rolling_sft.pt`, juntamente
com AdamW, cópias mestras, RNG, contadores e diário. A exportação parou ANTES de
criar qualquer checkpoint de época ou observar uma saída de validação. Não houve
OOM. O processo foi encerrado e o coordenador parou, sem reiniciar sozinho.

A projeção por bisseção verificava `(B@A)*s` e depois armazenava `B*s`. Em FP32,
`(B*s)@A` pode arredondar de forma diferente; a posterior conversão BF16 fez uma
norma ultrapassar o limite predefinido. A correção verifica exatamente a expressão
que será armazenada e fundida, preservando o teto original,24iterações e todos os
hiperparâmetros. Não escolhe escala por acertos em benchmark.

O checkpoint `recovery_step48` preserva o estado exato antes da exportação falha.
A restauração comparou2581tensores, incluindo estados do otimizador/RNG. Uma
verificação sem carregar o modelo completo reconstruiu as150matrizes base e
conferiu todos os hashes com a auditoria inicial. Os zeros negativos produzidos
pelo `beta=0` da receita também foram preservados na reconstrução, em vez de
substituí-los por zeros positivos. Isso é identidade de bytes, não ganho medido.

O teste reproduziu uma violação na expressão antiga; todas as150matrizes passaram
com a expressão corrigida. O contrato de avaliação voltou a passar. Os arquivos
anteriores e logs de falhas técnicas permanecem em `export_fix/`. Os congelamentos
iniciais não foram reescritos: `source_revision.json` registra os hashes antes e
depois APENAS de core.py e inference.py. Os demais arquivos continuam exatos.

A continuação usa `run_clean.py train --resume`: pula as48atualizações concluídas,
exporta a primeira época com a projeção corrigida e executa apenas49..96. Os dados,
as recompensas, o cronograma de aprendizagem, os testes, os budgets e os gates
continuam iguais. Os tempos de cada perna do diário são descritivos; o contador
`seconds` reinicia na retomada e não é um benchmark de velocidade. Nenhuma nova
contagem de épocas ou resultados fictícios é atribuída à recuperação.
