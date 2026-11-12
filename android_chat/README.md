# Liquid Sense Android — prévia offline

Chat de texto com **motor de inferência em Rust** e interface nativa Android
(Java para a Activity e os componentes do sistema). O modelo acompanha o APK;
não há API externa nem permissão de internet. Histórico salvo no aparelho,
seleção/cópia de texto, nova conversa, geração progressiva e botão **Parar**.

Preparado para **ARM64, Android 9+, Snapdragon 7s Gen 2 e 16 GB de RAM**. A versão
BF16 ocupa aproximadamente **1,61 GB de download**. Reserve cerca de 4 GB para
baixar e instalar. A velocidade depende da CPU; a execução usa quatro threads.
Contexto limitado a 2048 tokens e respostas de até 192 tokens na interface.

O download público será registrado em `reports/publication_receipt.json` após
a compilação e publicação da prévia. O workflow é
[liquid-sense-android.yml](../.github/workflows/liquid-sense-android.yml).

## Modelo incluído

- Checkpoint geral preservado: `rsi100/checkpoints/best.pt`, SHA256
  `46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8`.
- Todos os **546 tensores de texto / 919.659.696 valores** são preservados sem
  quantização: BF16 continua BF16 e os auxiliares FP32 continuam FP32. A tabela
  guarda os nomes, formas e hashes de cada tensor. Deduplicação e zeros positivos
  são representações reversíveis; sinais de zero negativos são preservados.
- Mantém **32 camadas físicas, 56 execuções, duas visitas 4–27, mHC de dois fluxos,
  caches independentes por visita, convolução causal de tamanho 7 e janelas 256**.
  O código implementa GatedDeltaNet, atenção com RoPE parcial e gate, normalizações,
  MLPs, Sinkhorn e os ganhos de visita salvos. Não substitui por Qwen comum.
- A visão e os pesos MTP não usados no chat não são incluídos no pacote de texto.
  Os arquivos originais completos e todos os experimentos antigos continuam intactos.
- A candidata 016 não foi promovida. Este app não anuncia melhoria dos pesos,
  inteligência geral, superioridade a 4B ou equivalência ao modelo Liquid AI oficial.

A identidade do chat usa a configuração já existente em `model_identity.json`,
com crédito ao desenvolvedor independente e à base Qwen. Não é uma identidade
aprendida por este empacotamento.

## Verificações

`reports/pack_verification.json` verifica os bytes de todos os tensores contra
`reports/source_tensors.json`. O pack BF16 final tem 1.599.290.240 bytes e SHA256
`6c774a434438add704b1993b8e013493fb95bc9802c4d9b30227832115c07288`.

O tokenizer e a renderização de uma conversa conferiram exatamente com Python
(121 tokens no fixture). Testes independentes cobrem produtos BF16/Q8,
arredondamento, separação dos caches e desempate greedy pelo primeiro token,
como `torch.argmax`. Uma geração real produziu a função `soma(a, b)` completa;
a sintaxe foi analisada sem executar o código gerado fora do sandbox.

O port usa prefill sequencial com cache, em contraste com o prefill em lote do
avaliador PyTorch. Há diferenças de acumulação e operações BF16 entre runtimes:
na auditoria de dois tokens instrumentados, a distância L2 relativa final foi
aproximadamente 3,6% e 4,7%, com os mesmos argmax. Isso não demonstra equivalência
bit a bit das respostas nem ganho de capacidade. Comparações dos 12 controles
antigos ficam em `reports/mobile_fidelity.json`; nenhum teste reservado novo
foi aberto. A correção de sinais de zero do exportador e a regra de desempate
estão documentadas em relatórios separados, sem mudanças nos gabaritos.

O APK é assinado e passa em `apksigner verify` e `zipalign`. A biblioteca ARM64
usa segmentos ELF com alinhamento de 16 KB. **Ainda não foi executado em Android
físico ou emulador**; a primeira prévia é entregue para teste no aparelho.

## Compilação

O workflow contém a sequência integral e fixa Rust 1.90.0, dependências em
`native/Cargo.lock`, PyTorch 2.15.0+cpu e as versões de `requirements.txt`. Os assets
públicos são baixados da revisão Qwen fixada e conferidos por hash. O modelo só
é carregado em subprocesso offline sem credenciais. Não há treino ou acesso a
soluções de validação.

As ferramentas principais são:

```sh
python android_chat/tools/export_model.py --out /tmp/ls-model --modes bf16 --reference
python android_chat/tools/verify_pack.py /tmp/ls-model/bf16.lsp --expected android_chat/reports/source_tensors.json --out /tmp/ls-pack-check.json
cargo +1.90.0 test --locked --release --lib --manifest-path android_chat/native/Cargo.toml
python android_chat/tools/fetch_android_tools.py --out /tmp/ls-sdk
```

Após configurar o linker Android, compilar `aarch64-linux-android` e apontar o
`--target` para o diretório Cargo de saída, `tools/build_apk.py` empacota todos
os assets dentro do APK. O modelo é mapeado diretamente do APK instalado; não
é copiado novamente nem baixado na primeira abertura.

A assinatura desta prévia usa certificado novo por compilação. Recompilar pode
exigir desinstalar a versão anterior, o que remove seu histórico privado. Chaves
de assinatura não são publicadas. Licenças e avisos acompanham código e APK.
