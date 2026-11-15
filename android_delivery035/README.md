## Entrega concluída

## APK 0.6.3 — download recuperado e verificado

O arquivo escolhido no Xiaomi tinha o tamanho esperado, mas SHA256 diferente.
[Baixar ZIP verificado — 1,97 GB](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/releases/download/liquid-sense-0.6.3-verified035/LiquidSense-0.6.3-verificado.zip).
Extraia e abra o APK. Se recusado, confira o APK extraído com o verificador034 e
copie o relatório. Não desinstale o app anterior. O download público completo do
ZIP e o SHA256 do APK interno passaram; a instalação no Xiaomi continua pendente.
Mesmos app, assinatura e pesos. O ponto da alteração na cópia anterior não foi
identificado. [Relatório e evidências](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/tree/9e8871b5f4c7bdac9442c8e054001560dd52ce73/android_delivery035).

# Entrega035 — diferença de SHA256 confirmada no aparelho

O relatório físico do Xiaomi com Android 15 identificou um arquivo de
1.967.560.403 bytes, exatamente o tamanho esperado, com SHA256:
`8303e126b3af7d3f4cc95f218729a7cbb0e7193acb508745754122866f535203`.

O APK 0.6.3 assinado e preservado tem SHA256:
`4735be854079941188e5f918e82d7c21d5468a437efe1bf7f45e72c15ade0e10`.

Portanto, o arquivo escolhido não é idêntico ao publicado. O parser local também
retornou null. Isso confirma um problema de integridade/identidade dessa cópia,
sem localizar o ponto da alteração. Não houve tentativa de instalação por sessão
e ainda não temos STATUS/LEGACY_STATUS real. A mensagem de app não encontrado
refere-se somente ao pacote consultado; não prova remoção de apps ou conversas.

O upload original teve bytes e MD5 conferidos por metadados, mas não download
completo de retorno. A tentativa atual de consultar o Gofile retornou exigência
de conta premium e limite de requisições; não foi possível conferir seus bytes.
Não se afirma que o Gofile, o celular ou a rede tenham causado a alteração.

A execução035 recupera o APK exato do arquivo persistido e o envolve em um ZIP.
Não recompila app, não reassina, não muda versão ou pesos. Cada segmento recuperado
e o APK completo são conferidos pelo SHA preservado. Não é necessário repetir o
emulador: os bytes recuperados devem ser idênticos aos já instalados/testados.

Um prerelease separado no GitHub preserva releases anteriores. A publicação
inclui ZIP e SHA256SUMS; antes de anunciar conclusão exige dois downloads completos
com verificação do ZIP e APK interno: draft autenticado e link público anônimo.
`delivery_manifest.json` registra cada etapa concluída. Um workflow verde sozinho
não implica instalação no aparelho físico. Fonte e evidência do diagnóstico anterior
permanecem em android_install034. Veja status.json para estado desta execução.

Após entrega: baixar ZIP, extrair, abrir APK extraído. Se recusado, escolher o APK
extraído no verificador034, aguardar SHA e usar botão2quando liberado; compartilhar
relatório com erro real. Não desinstalar a versão anterior nem apagar conversas.
