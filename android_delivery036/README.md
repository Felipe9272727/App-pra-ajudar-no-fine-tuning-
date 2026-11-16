# Reparador publicado e teste Android aprovado

[Baixar reparador0.2 — 33KB](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/releases/download/liquid-sense-integrity036/LiquidSense-Reparador-0.2.apk). Atualiza o verificador034.
CI43796079215/job133065078317 passou: update034→036, leitura do ZIP com um byte
alterado, detecção de1/235blocos, recuperação HTTPS de8MiB, SHA completo do ZIP,
extração CRC/SHA do APK, releitura e reconhecimento pelo Android.
Download público do helper conferido; SHA256 4f2a774b6b1a4b3a13cbcbdc84014dcc1a49ce9be165e1c9a34c69cef13f85b7.
Ainda falta teste no Xiaomi e confirmação da instalação do app principal.

# Integridade036 — comparar o histórico e reparar o ZIP existente

O usuário confirmou que baixou exatamente o link fornecido. O relatório não
significa que escolheu outro arquivo. Ele mede os bytes entregues pela leitura
no aparelho. A origem da diferença ainda é desconhecida; não há evidência para
culpar usuário, ZArchiver, rede, memória ou armazenamento.

## O que acontecia antes e o que acontece agora

| Etapa | Evidência e mudanças |
| --- | --- |
| UI031, série0.6.0/0.6.1 | Screenshot do usuário mostra app aberto gerando respostas. Havia problemas de teclado, novos chats e toque. A versão exata entre0.6.0e0.6.1não aparece no screenshot. Os APKs já tinham aproximadamente1,97GB. |
|0.6.2, UI032 | Ajustes de interface/teclado/navegação/animações. Primeiro relato explícito de pacote inválido na instalação física. |
|0.6.3, Install033 | ZIP do APK reconstruído do zero, assinatura v1/v2/v3 e versão7. Mesmo pacote, certificado, Rust/Python e pesos. Tanto0.6.2como0.6.3instalaram no emulador Android15; falha física não reproduzida. |
| Diagnóstico034 | APK escolhido tem1967560403bytes, mas SHA8303e126…535203, diferente do assinado4735be85…ade0e10. Nenhuma sessão de instalação foi iniciada. |
| Entrega035 | Mesmo APK dentro de ZIP público no GitHub. Download de retorno completo e CRC/SHA passaram no CI. Usuário informa CRC inválido no ZArchiver. |
| Nova leitura física | ZIP tem1967561424bytes, mas SHAb7b6e7c7…de7ef79; esperado52966dcc…724f307. Confirma diferença nos bytes lidos, sem localizar sua origem. |
| Investigação036 | Novo download desse mesmo link bateu o SHA; teste nativo unzip e leitura Java ZipInputStream passaram no CRC. ZIP normal, sem ZIP64, duas entradas, menos de2GiB. |

`reports/version_comparison.json` compara as quatro versões. Base pack
6c774a43…7288, patch experimental0f19e758…7310e bibliotecas Rust/Python são
idênticos entre0.6.0e0.6.3. Não houve mudança de inteligência, loop ou pesos nessa
sequência. Os erros de instalação/extração acontecem antes da execução do modelo.
Uma versão que abriu antes não prova que uma nova transferência chegou intacta.
A confirmação de identidade depende dos hashes, não só do nome e tamanho.

## Reparador pequeno — sem outro download completo obrigatório

Atualiza o mesmo pacote do verificador034, com o mesmo certificado e versão2.
O app principal não muda. Escolha o ZIP035que já está em Downloads. O reparador:

1. Lê o arquivo escolhido para uma cópia privada e compara235blocos de8MiB com
   hashes embutidos no APK assinado. Registra SHA da leitura original e da cópia
   relida, além dos índices diferentes e do volume necessário.
2. O botão2mostra quantos blocos e MiB serão necessários antes de baixar. Após o
   toque, baixa somente os blocos diferentes via HTTPS Range do GitHub. Se todos
   estiverem diferentes, o volume pode se aproximar de2GB; não promete volume
   pequeno antes de conhecer o resultado no aparelho.
3. Exige HTTP206com Content-Range exato, tamanho e SHA de cada bloco; rejeita
   servidor que ignore o intervalo. Nunca aceita bytes incorretos nem TLS inválido.
4. Grava somente no cache privado e relê cada bloco. Exige SHA completo do ZIP.
   Extrai internamente, conferindo CRC, SHA e uma nova leitura do APK no disco.
5. Só então libera botão3: instalação pelo Android com confirmação normal e
   captura do status real. Nenhuma assinatura é ignorada. Botão4copia o relatório.

O original em Downloads é preservado. INTERNET é uma permissão nova, usada
apenas no botão2para recuperar o arquivo público fixo. Nenhum arquivo, conversa
ou relatório é enviado. Não lê chats nem desinstala apps. ZIP, APK e sessão de
instalação podem ocupar vários GB temporários no aparelho. Caches do reparador
podem ser removidos depois; não apague dados do app principal.

## Validação e limites

Treze testes locais verificam localização de um byte alterado, recuperação parcial,
respostas malformadas, arquivo truncado, excesso de dados, rejeição de destino HTTP ou
não autorizado e leitura CRC/SHA completa do ZIP pela API Java. `unzip -t` também
passou. A requisição Range pelo cliente Python respeitou os bytes esperados. O
probe Java HTTPS local recebeu connection-refused neste ambiente; está preservado,
sem ser apresentado como teste de rede aprovado.

O CI036testa atualização do helper034para036em Android15realmente emulado e
injeta um byte incorreto em uma cópia de teste do ZIP. Instrumentação separada
invoca os métodos de produção: leitura, comparação de blocos, requisição HTTPS,
reparo e extração/validação do APK. Não distribui instrumentação no reparador.
O teste usa root somente no emulador para preparar a fixture no cache; não requer
root no celular do usuário. Não testa toques no seletor de arquivos, instalação
final do app principal ou comportamento no Xiaomi. Veja reports/current_status.json
para resultado. A publicação do APK pequeno ocorre somente se o teste passar.

Fontes e testes preservados nesta branch. Artefatos `.apk.bin` são APKs exatos;
renomear para `.apk` recupera os bytes sem recompilar. Chaves e senhas não são
publicadas. O modelo e todos os releases anteriores permanecem preservados.
