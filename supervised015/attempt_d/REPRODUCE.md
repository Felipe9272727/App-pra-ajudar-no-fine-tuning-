# Especialista D: cadeia exata e inferência sem respostas

Leia PROTOCOL.md e o relatório final. Os546 tensores de texto já foram treinados
em B/C. D refina apenas a matriz existente da última projeção MLP31, mantendo
as outras698 matrizes/vetores de parâmetros exatamente iguais a C.

O carregador restore.load_d executa principal -> B -> C -> patch D. Precisa de
TODAS as partes B/checkpoints/final, C/checkpoints/final e D/checkpoints/candidate,
mais os respectivos manifests. D é uma matriz BF16 bruta dividida em partes,
com hash do pai C, hash por parte e do tensor final. Não aplique D direto ao
principal. Não chame make_native/configure_loops/e.apply depois dos patches.
As dependências públicas originais e env sem credenciais estão em
../attempt_b/REPRODUCE.md. O principal permanece selecionado separadamente.

Inferência real, sem LogitsProcessor de treino:

```sh
env -i PATH=/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin:/usr/bin:/bin HOME=/tmp PYTHONPATH=/home/agent/.local/lib/python3.12/site-packages LS_CPU_THREADS=4 OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 HF_HUB_OFFLINE=1 python supervised015/attempt_d/infer.py --prompt 'Write a Python function that reverses a list.'
```

O coletor de TREINO usa um processador que força os tokens canônicos depois de
registrar os logits originais. Serve apenas para obter ativações sob prefixos
corretos no mesmo caminho nativo com cache. Esses programas forçados NÃO são
avaliados nem contados como resultados. A avaliação fria independente do script
train.py usa geração gulosa comum, sem respostas e sem processador de forçamento.
Toda pontuação publicada deve vir dos arquivos *_specialist.json dessa avaliação.

training_cache/ contém os estados x/r/h, tokens originais e decisões do coletor.
checkpoints/training_state/ contém master FP32 da única matriz/otimizador/RNG.
Ambos são arquivos torch ZIP divididos em partes com hashes. Reconstrua apenas
quando necessário, por exemplo:

```sh
python supervised015/attempt_d/restore_archive.py supervised015/attempt_d/training_cache /tmp/liquid-sense-d-cache.pt
```

Não sobrescreve arquivos existentes. O modelo de inferência usa somente BF16;
o master FP32 temporário do treino não muda a arquitetura de inferência.
O teste test_margin.py compara o subgradiente do concorrente ativo com autograd
sobre o vocabulário completo em um problema sintético, sem usar pesos reais.
audit_checkpoint.py verifica a cadeia salva, todos699 tensores finitos, todos546
hashes de texto, os outros545 textos iguais a C e a visão inalterada na cadeia.

train.py recusa repetir se passos/snapshot já existem. O limite é12atualizações
da matriz e1% de deslocamento Frobenius do master. A margem no treino não é uma
pontuação de programação; geração real e testes oficiais selecionados decidem.
Nenhum especialista é promovido como melhor modelo geral com estes alvos ensinados.
