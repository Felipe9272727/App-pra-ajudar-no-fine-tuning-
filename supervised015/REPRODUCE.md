# Estado final do estudo015

Leia SUPERVISED_TEXT_REPORT.md na raiz, final_summary.json, selection.json e
artifact_verification.json. O especialista é attempt_e; o principal geral segue
rsi100/checkpoints/best.pt, sem alteração. Nenhum modelo está sendo treinado ou
avaliado entre turnos.

Use attempt_e/REPRODUCE.md para carregar a cadeia principal->B->C->E. B/C são
snapshots XOR completos de texto; E é a matriz BF16 final contra C. Todos os
bits são verificados por hashes. D permanece salvo para reproduzir sua rejeição
e a continuação com reparo de rótulos, mas não é aplicado na inferência E.

Não execute novamente fases completas. Os scripts de avaliação retomam somente
IDs ausentes e verificam fontes/weights. Treinadores recusam saídas existentes.
A tentativa A foi interrompida sem snapshot; B/C/D/E e seus estados estão salvos.
O checkpoint E atingiu8/8 nos oito exemplos ensinados, não no HumanEval completo.
MBPP0/8 e controles6/12 são regressões/limites explícitos, sem promoção geral.

O reparo de terminal é auditado em eos_mismatch_001.json/data_integrity.json:
os programas, enunciados/gabaritos oficiais são byte a byte idênticos ao014.
Somente8rótulos terminais de treino foram alinhados ao EOS nativo já usado.
Não altere o gabarito para melhorar pontuações, nem confunda replay forçado com
avaliação. Os resultados finais vêm apenas da geração normal sem respostas.
