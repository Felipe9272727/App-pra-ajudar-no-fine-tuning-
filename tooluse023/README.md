# Liquid Sense · Web e Python — prévia0.3

**[Baixar APK no Gofile](https://gofile.io/d/fowGW6q4)** —1,62GB,
Android9+/ARM64, pacote separado `dev.liquidsense.chat.tools`.

O modelo geral já acompanha o APK e gera as respostas no aparelho. A busca
consulta a internet; o código Python roda localmente em serviço isolado.
O Qwen original já sabe emitir chamadas estruturadas. Esta integração fornece
execução real e observações; não demonstra ganho novo de inteligência nos pesos.

Toque em **Trocar modelo**, abaixo do cabeçalho:

- **Web e Python:** geral preservado, com ferramentas e etapa de conferência.
- **Especializada015E:** usa os pesos públicos do [app especialista0.2](https://gofile.io/d/iNjQRGpN)
  instalado/atualizado. O seletor detecta versão antiga e oferece o download.
- **1.0Base geral:** mesmo modelo geral integrado, em conversa offline.

O app novo preserva as instalações e os históricos anteriores. Cada opção tem
conversa separada. Especialista e Base são opções offline; Web e Python usa
o geral. A especialista é experimental:8/8programas ensinados no PyTorch,
7/8na portabilidade Rust e0/8transferência anterior. Não é HumanEval completo.

Python é um subconjunto Python3 em MicroPython1.26.1, com math/json/f-strings,
sem arquivos/rede/pacotes externos (não inclui NumPy/pip). Há limites de memória,
tempo,instruções,pilha e saída. Resultados/fontes reais aparecem na conversa.
Para APIs Python, o buscador pode verificar o símbolo diretamente no HTML
oficial; consultas gerais usam Brave/Yahoo. O modelo pode falhar ao pesquisar
ou concluir uma resposta: esta prévia exige conferência.

Os treinos022e023foram executados, salvos e rejeitados por regressões. **O APK
usa o melhor geral anterior, sem esses pesos rejeitados.** Loop/mHC e operadores
temporais continuam ativos:32camadas físicas,56visitas. Não são os modelos
oficiais completos SenseNova/Liquid. Não houve medição física no Snapdragon.

[Relatório, comparações e limitações](REPORT.md),
[protocolo de teste do app](APP_TEST_PROTOCOL.md),
[manifesto do APK](reports/apk_manifest.json),
[verificação do pacote](reports/package_verification.json),
[recibo público de entrega](reports/gofile_delivery.json).

APK SHA256:
`d8c649c9e06be632b7a411417d06a3a926911788764950a7d4ea2cf6956137f4`.
Assinatura Android/CRC/zipalign verificados; tamanho e MD5 coincidem com o
upload do Gofile. Não se repetiu o download remoto integral.
