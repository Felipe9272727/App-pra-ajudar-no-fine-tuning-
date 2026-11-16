# Session037 — reparar a instalação sem repetir o reparo dos pesos/arquivo

O novo relatório físico confirma que o reparador036funcionou até a preparação:
32de235blocos foram recuperados (268435456bytes,256MiB). O ZIP completo, CRC/SHA
do APK e sua releitura passaram no Xiaomi. Os erros seguintes pertencem ao
cliente de instalação: `write failed: EBADF`, sessão abandonada e nenhum pacote
preparado. Não há evidência de nova corrupção do APK já conferido.

## Erro identificado no nosso código

036incluía `out.close()` explicitamente dentro de `try(OutputStream out=...)` e
fazia `session.commit()` antes de sair desse escopo. O fechamento automático
chamava `close()` uma segunda vez. O FileBridgeOutputStream do Android15envia
um comando no descritor em cada `close()`; o segundo pode escrever no descritor
já fechado e gerar EBADF. O catch então chamava abandonSession mesmo após o
commit, produzindo falhas posteriores. `reports/AOSP_FileBridge_excerpt.txt`
preserva o trecho da implementação oficial, com a fonte identificada.

O teste036cobriu leitura, reparo HTTPS, extração e validação. Ele não executou a
instalação final por Session; por isso esse erro não foi detectado anteriormente.
O relatório físico fornecido orientou esta correção. Nenhuma falha é atribuída
à escolha de arquivo pelo usuário, ao ZArchiver ou ao modelo.

## Mudança037

- Escopos separados: Session externa e streams internos. A saída recebe fsync
  e fecha exatamente uma vez, antes do commit. Não há fechamento explícito
  duplicado. `session.getNames()` precisa conter base.apk; a releitura via
  `session.openRead()` precisa ter1967560403bytes e SHA4735be85…ade0e10.
- Só abandona sessões que falharam antes de tentar commit. Depois de uma tentativa
  de commit, mantém a sessão e aguarda o recibo, inclusive quando o retorno é
  incerto. Cada callback carrega seu ID; recibos legados/antigos não alteram o
  estado da sessão atual. Estados de UI sem sessão existente são reconciliados
  sem apagar cache nem dados do app principal.
- Mesmo pacote e certificado do reparador. Versão0.3/code3preserva verified.apk,
  flag valid036 e relatório. Não muda pesos, app principal0.6.3, pacote ou
  arquitetura. Nenhum novo reparo, ZIP ou download grande é necessário se o cache
  reparado continuar presente. A abertura informa que o APK está preservado.

## Uso após entrega

Instale0.3por cima do reparador anterior, sem desinstalar ou limpar dados. Abra e
toque diretamente no botão3. Não escolha o ZIP novamente nem repita o botão2.
Aguarde a entrega e a conferência dentro da sessão; confirme a instalação normal
do Android. Se falhar, botão4copia os novos resultados037no final do relatório.
O cache de vários GB deve ser mantido até a instalação terminar. Não precisa
baixar ou treinar o modelo novamente.

## Verificação

O CI037reproduz primeiro o erro036com o APK completo e exato; depois atualiza o
helper mantendo o cache e um marcador de dados. O teste separado invoca o método
de instalação de produção, confere o arquivo dentro da sessão, usa a confirmação
normal de instalação na UI do Android e exige STATUS_SUCCESS e pacote/version7
instalado. Também tenta abrir o chat instalado. Root é usado apenas no emulador
para preparar a fixture no cache, nunca exigido no aparelho do usuário.

Não repete o reparo já concluído nem avaliações neurais. Instrumentação não é
incluída no APK de produção. Só publica o APK pequeno se o resultado final do
instalador passar. Resultado do Xiaomi continua pendente; veja status.json e
reports/Android15para o estado real da execução. Todos os releases, checkpoints,
fontes e relatórios anteriores são preservados. Chaves e senhas são privadas.
