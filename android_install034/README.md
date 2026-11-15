# Verificador de instalação034 — causa no aparelho ainda pendente

A0.6.3 também foi recusada no aparelho físico. O Android15 emulado aceitou tanto
0.6.2quanto0.6.3; esse teste não reproduziu a falha. Nenhuma causa específica foi
confirmada. Não foi reconstruído outro APK de2GB sem evidência.

[Baixar verificador separado — 20,9KB](https://gofile.io/d/IqxirO9A).
Pacote `dev.liquidsense.installcheck`, versão0.1, Android9/API28ou superior.
SHA256: `3181345443e30e0663fdd54ce42109327a8c12f8c5d654a4055f11513f06fa41`.
Exatos20890bytes; fonte Java nativa, sem modelos nem bibliotecas nativas.

1. Instale e abra **Liquid Sense · Verificador**.
2. Toque em **Escolher o APK0.6.3já baixado**, selecione o arquivo em Downloads
   e aguarde a leitura completa. Não é necessário baixar os pesos novamente.
3. Se a integridade corresponder, toque em **Tentar atualizar e capturar o erro**.
   Permita instalações pelo verificador na tela normal do Android se solicitado,
   volte e toque novamente. Confirme a instalação quando o Android perguntar.
   Se necessário, volte ao verificador e use **Confirmar instalação no Android**.
4. Volte ao verificador, toque em **Copiar relatório** e cole na conversa.
   Se a integridade não corresponder, copie o relatório sem instalar.

O relatório inclui versão do Android, fabricante/modelo, ABIs, bytes e SHA256 do
arquivo escolhido, versão e certificado do app instalado e do APK, comparação
entre certificados e possível downgrade. A sessão PackageInstaller registra
STATUS, LEGACY_STATUS e mensagem real do sistema, quando o sistema os fornece.
Não ignora verificações do Android. Não remove o app existente nem suas conversas.
Uma atualização pode funcionar por esse caminho; isso ainda não foi demonstrado
no aparelho físico. O resultado do aparelho é necessário para identificar a falha.

Sem permissão INTERNET, sem acesso aos dados de chats, sem identificadores únicos
do aparelho e sem envio automático. Somente o APK escolhido é lido. Uma cópia
verificada de aproximadamente2GBfica temporariamente no cache deste verificador;
a sessão de instalação também precisa de espaço. O original em Downloads é
preservado. O relatório é local; somente o usuário decide copiá-lo/compartilhá-lo.

A instalação e abertura do verificador passaram no emulador Android 15/API 35
(run43749143251, job132918977825); screenshot e logs preservados.
Veja `status.json` e `reports/Android15/` para resultado; isso não valida o fluxo
completo de seleção/atualização no aparelho físico. Não há alterações nos pesos,
loop, UI ou dados do app principal. Versões anteriores continuam preservadas.

## Reprodução

`build.py` usa aapt2,javac via java,D8,ZIP novo,zipalign e apksigner v1/v2/v3.
Ferramentas Android e chave privada são fornecidas por ambiente/arquivos privados;
nenhuma chave, senha ou token de upload é publicada. A recuperação byte a byte
independe da reprodução da assinatura: `artifacts/diagnostic.apk.bin` contém o APK
assinado exato (renomear para `.apk`). O build verifica CRC,alinhamento,assinatura
e ausência da permissão INTERNET. Relatórios públicos omitem segredos.
