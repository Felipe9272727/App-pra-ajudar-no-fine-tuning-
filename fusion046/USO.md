# Liquid Sense × Gemma 046

Pacote incremental experimental para Linux x86-64. O arquivo `readout.lscal` aplica a correção de saída que passou na avaliação, mantendo os 19 blocos e os 510.000.128 pesos Gemma do 045. O pacote usa o mesmo checkpoint 045 que você já pode ter baixado. [Checkpoint 045](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/releases/tag/liquid-sense-gemma045)

Extraia o ZIP e, na pasta extraída, execute a pergunta com o arquivo `.lsmix` original.

```sh
chmod +x run.sh liquid-sense-046
./run.sh /caminho/LiquidSense-Gemma-045.lsmix "Escreva uma função Python que conte vogais."
```

Os termos e avisos sobre os pesos derivados acompanham o pacote em `Notice.txt` e `licenses/`.
