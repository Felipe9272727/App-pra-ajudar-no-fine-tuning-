# Reprodução e retomada

Leia primeiro status.json, selection.json, PROTOCOL.md, frozen.json e os logs.
Não lance outra execução se existir worker anterior. As fontes congeladas são
as usadas na medição; não as edite para reinterpretar saídas já observadas.

`run_study.py` registra a execução inicial e inclui construção dos pesos.
**Não o use para reiniciar um estudo com checkpoints existentes.** Para uma
interrupção, use `python review013/resume_study.py` no ambiente documentado:
ele confere os hashes dos pesos, conserva fases concluídas e retoma só as
ausentes. O consolidado corrigido está em finalize.py: uma rejeição de sintaxe
ou AST antes da execução vale zero em cada escore, mas não é uma execução
observada de cada caso. Os JSONs brutos e o avaliador congelado são preservados.
Um estudo rejeitado e concluído gera somente uma mensagem, sem
carregar modelo ou sobrescrever candidatos. Antes de um primeiro estudo,
data.py gera os 200 problemas e verifica todas as referências no sandbox;
teach.py capture coleta os exemplos de ensino, retomando só arquivos ausentes.

O ambiente usado tem Python3.12.14, torch2.15.0+cpu, transformers5.22.1 e
safetensors0.8.0. Execuções de modelo usam quatro threads e ambiente sem
credenciais, com HF_HUB_OFFLINE=1. O original e o port híbrido anteriores
precisam estar restaurados conforme o projeto; os pequenos .pt novos são
**sobreposições dependentes do pai**, não modelos completos independentes.

`python review013/restore_states.py` recompõe/verifica os120 arquivos de
features/targets de ensino a partir de archives/manifest.json e seus chunks,
sem sobrescrever observações divergentes. São os valores efetivamente usados
na regressão, não uma promessa de guardar todos os estados do backbone.
Os arquivos originais locais ficam preservados em states/, fora do Git.

`python review013/verify_artifacts.py` confere congelamento, resultados,
pontuações e checkpoints, sem inferência. `harness_audit.py` é somente uma
auditoria da restrição histórica ao nome `_`; não repara saídas ou muda scores.

Para inspeção experimental, review_runtime.load_variant('loop'/'joint')
carrega o pai e instala a candidata rejeitada. O padrão selecionado continua
'parent'. Nunca substitua best.pt pelo arquivo do adaptador: os formatos são
diferentes. Este estudo não habilita pesquisa automática em segundo plano.
