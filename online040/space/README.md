---
title: Liquid Sense GPU Prototype
emoji: 💧
colorFrom: purple
colorTo: blue
sdk: gradio
sdk_version: 6.32.0
python_version: '3.12'
app_file: app.py
license: apache-2.0
---

Liquid Sense Base em ZeroGPU, com os mesmos pesos BF16 do APK e os mesmos limites de geração do app. O perfil Extenso oferece até 2.048 tokens de raciocínio e 4.096 de resposta em um contexto total de 16.384 tokens.

O chat funciona no navegador. A partir da versão 0.6.4, selecione **Base 1.0 · GPU** no Android para se conectar diretamente a este Space. A geração acontece em etapas e pode parar quando a cota do Hugging Face terminar. Este Space aceita conversas em texto.

O modelo experimental tem 32 camadas, 56 visitas às camadas e 546 tensores verificados. O pacote BF16 vem do APK publicado, com a mesma arquitetura derivada do Qwen.
