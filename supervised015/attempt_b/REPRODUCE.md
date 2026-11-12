# Checkpoint especialista SFT015 B

Este checkpoint é separado do principal; foi treinado intencionalmente nos oito
problemas HumanEval listados em train.json. Não é um resultado limpo de HumanEval
nem uma medição de desempenho geral. Leia SUPERVISED_TEXT_REPORT.md na raiz.

Use o mesmo checkout e ambiente Python registrado nos logs. Dependências locais:
torch2.15.0+cpu, transformers5.22.1, Python3.12.14. Inferência BF16/eager/greedy,
quatro threads. Pesos originais e do híbrido são pré-requisitos: veja NOTICE,
sensenova_port/config.json e o carregador reasoning/runtime_helpers.py. O pai selecionado é
rsi100/checkpoints/best.pt, SHA256
46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8.
O arquivo híbrido base usado nesta execução, sensenova_port/model.safetensors, tem SHA256
14c3497c97c509515dd70d77e1baa50fda5f7ba1f3fbff8a0237d570ea4540c1.

checkpoints/final/manifest.json lista todas as partes partNNNN.bin, tamanhos,
hashes SHA256 por parte, hash do stream comprimido e hashes anterior/novo de
cada tensor. São XORs binários exatos, não deltas numéricos aproximados. Baixe
todas as partes do MESMO commit. O restaurador rejeita pai ou bytes divergentes.
A visão permanece no pai; as546 matrizes/vetores de texto são reconstruídas.
Carregue o pai PRIMEIRO e aplique o snapshot DEPOIS. Não chame make_native,
e.apply ou configure_loops após restaurar: isso apagaria parte dos novos pesos.

Exemplo de uso, a partir da raiz, com ambiente sem credenciais:

```sh
env -i PATH=/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin:/usr/bin:/bin HOME=/tmp PYTHONPATH=/home/agent/.local/lib/python3.12/site-packages LS_CPU_THREADS=4 OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 HF_HUB_OFFLINE=1 python supervised015/attempt_b/infer.py --prompt 'Write a Python function that reverses a list.'
```

Essa pergunta de exemplo não constitui uma avaliação registrada. A CLI não
executa o código gerado. Os testes registrados usam o executor isolado do014.
Ajuste apenas os caminhos do executável/site-packages se o ambiente for outro.

Para verificar integridade sem gerar novas respostas, use o mesmo prefixo env
acima com `python supervised015/attempt_b/audit_checkpoint.py`.
O script verifica todos os699 tensores finitos,546 hashes de texto,153 tensores
de visão idênticos, arquitetura e roteadores. Não execute paralelamente ao treino
nesta máquina de8GiB. Os hashes/artefatos publicados já registram essa auditoria.

Os scripts train.py e evaluate.py recusam sobrescrever/repetir resultados
concluídos. A avaliação retoma apenas IDs ainda ausentes; ao estar completa, não
repete inferência. Referências Qwen/pai foram reutilizadas do014, sem novos testes.
O resumo e a decisão podem ser reconstruídos sem modelo com summarize.py.

Uma repetição EXPLÍCITA do treino pode ser solicitada em diretório novo com o
mesmo prefixo env e `python supervised015/attempt_b/reproduce_training.py
--output-dir /tmp/liquid-sense-015-replay`. Esse comando não foi executado nesta
sessão; é uma ferramenta de reprodução opcional e não apaga o experimento salvo.
O estado do otimizador Adafactor e dos RNGs do treino concluído fica em
checkpoints/optimizer.pt; não há serviço persistente nem retomada automática.
A primeira tentativa A foi interrompida sem snapshot; seus logs permanecem.

O campo backward_passes=0 e o texto de inicialização da função histórica
code_rsi.runtime.check_architecture são constantes antigas de inferência, não
contadores de treino. training_complete.json/backward_passes e steps.jsonl
registram os backward reais; a avaliação especialista corrige esses metadados.

A semente fixa não garante repetição bit a bit entre versões ou máquinas. Os
hashes do snapshot salvo definem os pesos exatos usados na avaliação.

Em instalação nova, download_model.py recupera a revisão pública Qwen
2fc06364715b967f1860aea9cf38778875588b17, registrada em hf_model_info.json e
download_manifest.json. O arquivo de pesos original usado tem SHA256
04b1c301231dd422b8860db31311ab2721511346a32cb1e079c4c4e5f1fe4696.
build_sensenova_port.py reconstrói deterministicamente os valores do port base;
para respeitar quatro threads, chame seu main após torch.set_num_threads(4).
O download usa rede; o processo do modelo usa somente arquivos locais e HF
offline. Não baixe novamente os arquivos já presentes e íntegros.
Os cabeçalhos/ordem de metadados safetensors reconstruídos podem mudar o hash
do arquivo sem mudar pesos. Para um port reconstruído, os hashes por tensor do
pai/snapshot e a restauração exata são a verificação final dos valores usados.
