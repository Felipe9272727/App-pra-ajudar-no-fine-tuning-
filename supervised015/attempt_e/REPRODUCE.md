# E — continuação com término de treino corrigido

O modelo e o EOS de inferência248044 permanecem os mesmos do protocolo comparativo.
Somente os8 rótulos finais de treino foram reparados:248046(im_end) ->248044(endoftext).
Programas de referência, enunciados e testes não foram alterados. Veja
../eos_mismatch_001.json e terminal_label_repair.json. Os estados de D antecedem
a emissão do último token, então permanecem válidos para o novo alvo.

Inferência de E carrega principal -> B -> C -> E. Use TODAS as partes dos manifests
B/checkpoints/final, C/checkpoints/final e E/checkpoints/candidate. E é a matriz
BF16 inteira da última projeção MLP, com hash do tensor pai C e do resultado.
D não é aplicado na inferência E; seus estados FP32/otimizador e cache são usados
somente para reproduzir a continuação de treino. Todas as versões foram preservadas.
O nome interno load_d do helper compartilhado é histórico; em restore.py desta
pasta ele lê o manifest E, validando o pai C. Não chame configure_loops/e.apply
após os patches, pois isso apagaria pesos já aprendidos.

Use dependências/modelos de base e ambiente sem credenciais descritos em
../attempt_b/REPRODUCE.md. Exemplo de inferência SEM forçamento de tokens:

```sh
env -i PATH=/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin:/usr/bin:/bin HOME=/tmp PYTHONPATH=/home/agent/.local/lib/python3.12/site-packages LS_CPU_THREADS=4 OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 HF_HUB_OFFLINE=1 python supervised015/attempt_e/infer.py --prompt 'Write a Python function that reverses a list.'
```

A pergunta de exemplo não é uma medição registrada. Para auditoria dos pesos
salvos, use o mesmo prefixo env com audit_checkpoint.py. Conferem-se todos546
hashes de texto, todos699tensores finitos e a visão153inalterada. A inferência
continua BF16; o master FP32 da matriz só pertence ao treino.

checkpoints/training_state é um torch ZIP em partes com master/AdamW/RNG. Pode
ser reconstruído, sem sobrescrever arquivos, com ../attempt_d/restore_archive.py.
O cache de treino original está em ../attempt_d/training_cache; sua integridade
é checada antes de aplicar as8 substituições do mapeamento de rótulos. O cache
original de D não foi alterado nem descartado. Replays forçados não contam como
resultados; somente *_specialist.json da avaliação comum fornecem pontuações.

E esgota os6passos restantes do limite original12 da etapa de projeção final.
train.py recusa sobrescrever tentativas já iniciadas. Não apague logs para repetir;
use outra saída/cópia de trabalho e mantenha os pais exatos. O checkpoint principal
geral segue separado: este é um especialista em8problemas ensinados, com regressões
declaradas e nenhuma alegação de superar4B ou modelos gerais maiores.
