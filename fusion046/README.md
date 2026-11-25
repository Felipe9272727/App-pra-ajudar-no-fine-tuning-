# Liquid Sense × Gemma 046

Os arquivos em `checkpoints/` são correções incrementais para o checkpoint 045 publicado. Cada uma preserva os 510.000.128 parâmetros Gemma, a Base Liquid Sense e o tokenizer híbrido. O carregador verifica o SHA-256 do 045 inteiro e da correção antes do uso. [Checkpoint 045](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/releases/tag/liquid-sense-gemma045)

Com o arquivo `LiquidSense-Gemma-045.lsmix` extraído, compile o motor da sessão e carregue a variante congelada em `selection.json`.

```bash
cargo build --locked --release --manifest-path fusion043/native/Cargo.toml --bin hybrid044
variant="$(jq -er '.variant' fusion046/selection.json)"
patch="fusion046/checkpoints/$variant.lscal"
expected="$(jq -er --arg name "$variant" '.candidates[$name].sha256' fusion046/selection.json)"
fusion043/native/target/release/hybrid044 calibrated /caminho/LiquidSense-Gemma-045.lsmix "$patch" "$expected" ask "Escreva uma função Python que conte vogais."
```

`PROTOCOL.md` descreve o método. `reports/` guarda a validação do ajuste e os resultados de geração. Os termos de uso e avisos acompanham o modelo em `fusion043/licenses/`.
