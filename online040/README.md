# Liquid Sense 0.6.4 em GPU

Selecione **Base 1.0 · GPU** em **Trocar modelo** para conversar com o modelo no Hugging Face. O Android envia as mensagens dessa conversa diretamente ao Space e recebe o resultado em etapas. As conversas da GPU e das opções locais têm históricos separados. O modo GPU gera texto. Busca na web e Python continuam disponíveis nas opções locais compatíveis.

| Perfil | Raciocínio | Resposta | Contexto total |
| --- | ---: | ---: | ---: |
| Normal | 0 | 2.048 | 16.384 |
| Profundo | 1.024 | 2.048 | 16.384 |
| Extenso | 2.048 | 4.096 | 16.384 |

Cada perfil reserva espaço para a geração dentro da janela total. Ao alcançar o limite de contexto, o Space retira as mensagens mais antigas por turno. A fila e a cota do ZeroGPU podem encerrar uma conversa mais longa antes de atingir o teto. O seletor tem a opção **Configurar cota do Hugging Face**. Um token pessoal de leitura é opcional e fica criptografado no Android. O Space também funciona no navegador. [Liquid Sense em GPU](https://huggingface.co/spaces/Felipe0282829273/liquid-sense-gpu)

## Atualização da 0.6.3

Instale o **Atualizador GPU 0.4** por cima do Reparador. Abra, toque em atualizar e confirme na tela padrão do Android. O atualizador tem 6.300.204 bytes e reconstrói o APK 0.6.4 a partir dos pesos da 0.6.3 já instalada. Ele confere o APK original, os pesos e o APK reconstruído antes de iniciar a instalação. O pacote principal e seu certificado continuam os mesmos. O Android usa espaço temporário para a instalação de cerca de 2 GB.

[Baixar o Atualizador GPU 0.4](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/releases/download/liquid-sense-0.6.4-gpu040/LiquidSense-Atualizador-GPU-0.4.apk)

## Validação

- O endpoint em CUDA retomou a geração com a mesma conversa e produziu 600 tokens de raciocínio em duas etapas. O teste automatizado de limites atingiu 2.048 de raciocínio e 4.096 de resposta com um modelo de teste. [Execução em GPU](reports/live_gpu.json) · [Limites](reports/smoke_limits.json)
- Os checks do APK confirmaram a assinatura, o alinhamento, o CRC e a igualdade dos pesos e das bibliotecas locais com a 0.6.3. A etapa de instalação em Android 15 reconstruiu o APK completo e recebeu `STATUS_SUCCESS`. A primeira rodada de instrumentação preencheu o arquivo errado de preferências para testar o histórico. A rodada seguinte conferiu o histórico preservado e recebeu uma rejeição de cota anônima do Hugging Face. A primeira etapa do modo Normal passou a solicitar uma reserva menor, com continuação até o teto do perfil. [Build](reports/apk_manifest.json) · [Primeira execução Android](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/actions/runs/44919350641) · [Segunda execução Android](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/actions/runs/44919762085)
- No teste final, o Android 15 emulado instalou a atualização, preservou a conversa anterior, selecionou o modo GPU, exibiu o limite de cota anônima retornado pelo Hugging Face e voltou ao modo offline. O chat web e a API responderam em CUDA com autenticação na mesma revisão do Space. O download público foi conferido pelo SHA-256. A instalação no Xiaomi ainda será verificada no aparelho. [Teste Android](reports/Android15/gpu.txt) · [API GPU](reports/final_gpu.json) · [Chat web](reports/live_web.json) · [Entrega](reports/Android15/delivery.json)
