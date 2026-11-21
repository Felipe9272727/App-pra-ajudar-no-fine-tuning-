Atualização compacta do Liquid Sense 0.6.3 para 0.6.4. Abra o atualizador e confirme a atualização pelo Android. Ele reutiliza os pesos do APK 0.6.3 instalado, preservando as conversas e os modelos locais.

Em Trocar modelo, selecione **Base 1.0 · GPU** para usar o Space do Hugging Face diretamente. O histórico GPU fica separado. O modo GPU gera texto e está sujeito à fila e à cota do ZeroGPU. A configuração de cota aceita, opcionalmente, um token de leitura da conta do usuário, criptografado no aparelho.

Os três perfis online e locais usam até 16.384 tokens de contexto. Normal permite até 2.048 de resposta. Profundo permite 1.024 de raciocínio e 2.048 de resposta. Extenso permite 2.048 de raciocínio e 4.096 de resposta. O modelo pode encerrar mais cedo e a cota pode interromper uma resposta longa.
