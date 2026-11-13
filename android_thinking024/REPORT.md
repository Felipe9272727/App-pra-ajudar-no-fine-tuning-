# Tools0.4: correção do chat e limites de inferência

Os pesos gerais foram preservados byte a byte. Esta é uma atualização de
software/inferência, sem treino, fine-tuning ou nova promoção de checkpoint.

A captura recebida mostra um cartão de busca e uma falha genérica de chamada.
Não contém a pergunta nem a geração bruta, portanto não permite afirmar a causa
exata. A revisão encontrou thinking desabilitado,256tokens por etapa e um teto
nativo de2048tokens de contexto. Uma chamada cortada pelo limite é uma causa
possível; também existem erros de formato produzidos pelo próprio modelo.

## O que mudou

Normal permite2048tokens de resposta. Profundo experimental permite1024para
raciocínio e2048para resposta; Extenso experimental,2048e4096. O contexto tem
teto16384incluindo entrada e geração reservada. As cotas são máximos, sem
obrigação de consumir tudo. O loop continua com32camadas físicas/56visitas;
não foram adicionadas passagens nem alterados pesos nesta atualização.

O agente executa apenas chamadas completas, com uma tentativa de reparo no modo
Normal. Mantém resultados reais e diagnóstico local antes de fazer o parse.
Bloqueia repetição de chamada idêntica já bem-sucedida. Oferece Continuação e
cópia voluntária do diagnóstico. Não culpa a pergunta por erros de formato.
Saída composta só por marcadores de thinking é resposta incompleta, com reparo
limitado. Se Python terminar sem stdout, informa isso ao modelo e ao usuário;
não fabrica um valor de retorno de uma expressão.

Uma compilação024intermediária introduziu um erro na condição de parada e deixou
passar im_end. O teste o detectou; a regra geral023foi restaurada:248044ou248046
encerram. A exceção histórica da Especializada permanece. Essa compilação
intermediária e seus testes foram arquivados e não foi distribuída.

## Comparação real: mesmo cálculo e mesmos pesos

Entrada: “Responda somente o número: quanto é17vezes19?” A resposta esperada323
existe somente no avaliador, não no prompt. Inferência greedy,4threads; nenhum
modelo auxiliar fornece a solução durante a geração.

| Condição | Resultado | Tokens gerados |
|---|---|---:|
| App023Normal, limite256 |323, correto |3|
|024thinking32/resposta64 |repetição, incorreto |96|
|024Profundo1024/resposta2048 |repetiu marcadores, sem resposta |3072|

O teste Profundo gastou58,47s de prefill e870,19s de decode no host. Não são
medições do celular. O fechamento de thinking foi forçado pelo orçamento e
registrado; nenhuma resposta foi inserida. A falha não foi promovida a ganho.
**Normal permanece padrão; modos longos são escolhas experimentais.**

O teste longo teve474tokens de entrada+3074IDs gerados, incluindo2controles.
O motor passou do antigo teto2048sem falhar. O teto16384não foi integralmente
estressado. Um fixture de entrada longa foi preparado, mas não executado:
o teste longo já verificou a travessia do limite anterior. A correção final de
im_end não altera essa sequência: nela não há248044nem248046.

## Ferramentas: separar execução de verificação

Na pergunta “Use Python para conferir quanto é18vezes23e diga o resultado”, o
modelo produziu apenas a expressão18*23, sem print. O intérprete real executou
com exit0e stdout vazio. O modelo respondeu414, que é aritmeticamente correto,
mas **não conta como número verificado pela ferramenta**. A execução com o
aviso genérico de stdout vazio também foi preservada e não contou como sucesso
de verificação: ele novamente respondeu414sem observar esse valor no stdout.
Isso é uma limitação de uso de ferramentas do checkpoint atual.

O teste separado `explicit_python_abi` fornece uma instrução explícita para
executar `print(18 * 23)`. Ele verifica a integração de entrada/saída, não mede
a habilidade de descobrir um programa nem é um benchmark de programação.
Seu resultado final está em `reports/comparison.json` e nos logs correspondentes.
Não confundir esse teste de integração com aprendizado ou transferência.

A consulta JavaHTTPSreal a math.cos retornou a documentação oficial e verificou
a âncora no HTML recebido. O primeiro teste do host, sem configurar o proxy
requerido por este ambiente, falhou por conexão recusada; foi registrado. Com
o proxy do host e TLS normal, passou. Nenhum ajuste de proxy foi colocado no APK.

Passaram16testes Rust e27testes de parser/agente. Estes últimos usam respostas
simuladas para verificar truncamento, reparo, duplicatas e preservação de dados;
não são pontuação de capacidade. O template oficial foi conferido em8casos,
com as limitações de cada verificação explícitas no relatório.

## Distribuição e preservação

O APK tem applicationIDdev.liquidsense.chat.tools,versionCode2e o mesmo
certificado do0.3, mantendo suas conversas. Pesos gerais integrados; seleção
opcional da Especializada015Econtinua pelo app especialista já instalado.
A variante geral continua com packSHA-256
6c774a434438add704b1993b8e013493fb95bc9802c4d9b30227832115c07288.
Nenhum overlay rejeitado022/023foi incluído.

Assinatura oficial, alinhamento de16KiB,CRC, biblioteca final/DEX e hash do pack
foram verificados. O manifesto do APK e o recibo público de upload registram
tamanho e hashes. Não houve execução desta versão0.4no telefone físico.

O APK0.3continua byte a byte recuperável por fragmentos+pesos imutáveis, com
SHA-256completo reconstruído antes de retirar somente a cópia temporária de
build. O download antigo continua registrado. Experimentos, checkpoints e
resultados negativos não foram apagados. As4perguntas seladas023permanecem
sem consulta. Não foram reiniciados loops de RSI.

O teste explícito de I/O terminou com sucesso: Python retornou stdout414\n e
o modelo respondeu “A saída observada é: **414**”. A aritmética não foi fornecida
como resultado; o teste forneceu o programa a executar. Não pontuamos isso como
solução independente de problema de programação.

Download verificado: [LiquidSense-0.4.0-thinking-preview.apk](https://gofile.io/d/hmAohFD5).
SHA-256 do APK: `6cb9927dca809c901947aed2c4ebd577d421de87e338f06c2714ea21a0f091db`.
