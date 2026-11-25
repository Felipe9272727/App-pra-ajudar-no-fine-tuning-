# Liquid Sense 046 no Termux

Terminal Rust compilado do código desta versão para Android ARM64. Use Termux num Android 9 ou posterior. O arquivo `liquid-sense-termux` fica na pasta privada do Termux e os pesos podem ficar em Downloads.

Depois de extrair o pacote na pasta privada do Termux e conceder acesso aos Downloads com `termux-setup-storage`, execute:

```sh
chmod +x liquid-sense-termux
./liquid-sense-termux "$HOME/storage/downloads/LiquidSense-Gemma-045.lsmix" readout.lscal
```

O executável confere o SHA-256 do checkpoint 045 inteiro e da correção 046 uma vez na abertura. `/think` alterna raciocínio, `/clear` limpa o contexto e `/exit` fecha. A sessão começa com raciocínio explícito desativado. Sem o arquivo `.lsmix`, `python baixar-modelo.py LiquidSense-Gemma-045.lsmix` baixa diretamente os 2,65 GB dos pesos verificados. O script usa o pacote `python` do Termux. [Checkpoint 045](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/releases/tag/liquid-sense-gemma045)

Para compilar no Termux, instale `rust clang` e use o código desta versão.

```sh
cargo build --locked --release --jobs 2 --manifest-path fusion043/native/Cargo.toml --bin termux046
```

Os termos aplicáveis acompanham a derivação em `Notice.txt` e `licenses/`.
