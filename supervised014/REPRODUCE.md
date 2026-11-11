# Retomada sem repetir experimentos

Leia status.json, construction.json, teaching.json, frozen.json e os logs.
Confira os processos antes de iniciar um worker: nunca lance duas cópias.

teach.py preserva cada estado capturado. Se o checkpoint já existir, ele
confere o hash e retoma somente diagnósticos ausentes, sem refazer a edição.
Se teaching.json estiver completo, a chamada é um no-op. O formato do candidato
não substitui best.pt: core.load_variant('edited') carrega o pai e escreve
apenas a matriz salva. O pai continua em rsi100/checkpoints/best.pt, e a matriz
anterior está em checkpoints/parent_matrix.pt.

run_evaluation.py é serial e limitado. Fases completas são ignoradas; evaluate.py
retoma só IDs ausentes, verificando o congelamento e o checkpoint. Não altere
as fontes congeladas para reiniciar uma execução observada. Todos os modelos
recebem os mesmos enunciados, sem o campo solution/tests dos JSONs.

Use o ambiente Python/PyTorch/Transformers anterior do projeto e quatro threads:
LS_CPU_THREADS=4, OMP_NUM_THREADS=4, MKL_NUM_THREADS=4, HF_HUB_OFFLINE=1. Os
workers de inferência foram lançados com env -i, sem credenciais. Os pesos
originais/port híbrido precisam estar disponíveis conforme a recuperação.

restore.py verifica/restaura nove arquivos de ativações/alvos a partir dos
chunks e hashes, sem sobrescrever observações divergentes. archive.py mantém
os arquivos originais locais. Os dois .pt de matrizes estão salvos diretamente
no GitHub; a falha de resposta durante upload foi investigada por seus hashes,
e não levou a reconstrução ou repetição de qualquer cálculo do modelo.

summarize.py produz a comparação e seleção, sem inferência. O conjunto HumanEval
ensinado não serve de teste independente; os resultados MBPP não podem voltar
ao ajuste desta candidata. Nenhum processo permanente ou novo loop RSI é criado.
