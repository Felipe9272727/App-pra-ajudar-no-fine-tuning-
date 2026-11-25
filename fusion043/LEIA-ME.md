# Liquid Sense × Gemma 045

Checkpoint experimental de **1.432.151.216 parâmetros**. São **919.659.696** da Base Liquid Sense derivada do Qwen, **510.000.128** copiados da Gemma 3 1B IT e **2.491.392** nas projeções e embeddings híbridos. Os 19 blocos Gemma incluem atenção, MLP e normalizações. Eles executam nas duas passagens do loop, com cache causal separado por visita. O tokenizer preserva os 248.070 IDs da Base e inclui 129 peças novas da Gemma.

## Baixar e executar

Baixe `LiquidSense-Gemma-045.zip.part01`, `LiquidSense-Gemma-045.zip.part02` e `SHA256SUMS` na mesma pasta. O pacote inclui um executável para Linux x86-64. O arquivo `.lsmix` contém os pesos dos dois modelos e o tokenizer.

```bash
sha256sum --ignore-missing -c SHA256SUMS
cat LiquidSense-Gemma-045.zip.part01 LiquidSense-Gemma-045.zip.part02 > LiquidSense-Gemma-045.zip
sha256sum -c SHA256SUMS
unzip LiquidSense-Gemma-045.zip -d liquid-sense-gemma-045
cd liquid-sense-gemma-045
chmod +x liquid-sense-hybrid
./liquid-sense-hybrid pack LiquidSense-Gemma-045.lsmix ask "Escreva uma função Python que conte vogais."
```

## Avaliação

`resultado.json` contém as respostas e as notas da Base, do tokenizer híbrido sozinho e da fusão. Os programas e respostas de referência ficam fora do processo de geração. Os tempos medem geração em CPU no mesmo ambiente.

Os termos aplicáveis acompanham os pesos em `licenses/GEMMA-TERMS.md` e `Notice.txt`. [Gemma Terms of Use](https://gemma.ai/resources/terms/)
