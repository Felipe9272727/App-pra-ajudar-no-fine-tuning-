# Liquid Sense — velocidade e raciocínio017/018/019

Etapa concluída em12/11/2026. Principal geral e APK0.1.0preservados. Prévia rápida020entregue separadamente.
O novo treino NÃO foi promovido. Não há worker de modelo em segundo plano.
O seletor “1.0Base / Especializada” está registrado para depois do trabalho de
pesquisa, em speed017/MODEL_SELECTOR_BACKLOG.md.

## Velocidade medida, mesmos pesos

No protótipo Rust, reorganizamos as reduções DeltaNet para percorrer a memória
sem alterar a ordem FP32 por saída; guardamos gates constantes de roteadores
com matriz zero; reutilizamos somente prefixos de tokens/cache exatamente
compatíveis; e evitamos multiplicações por16matrizes BF16 comprovadamente nulas.
Todas as32camadas físicas e56execuções continuam atualizando seus estados.
Nenhum peso foi quantizado, apagado, alterado ou substituído por Qwen puro.

Doze pares fixos no servidorx86, quatro threads, sem readout do vocabulário:
2.2482→1.9326segundos por16tokens,
**1.1633x de throughput (+16.33%)**, ou
14.04%menos tempo. IC95%da diferença
[0.2381,0.3931]s; teste emparelhado de sinais
bilateral p=0.00048828. Todos os12pares foram incluídos.
A primeira versão017teve1,0623x na replicação confirmatória; não multiplicar
esse fator pelo019, que já inclui todas as otimizações contra a referência.

Oito testes técnicos passaram no019. Dezesseis tokens de traço completo tiveram
912saídas de estágio,896slots de cache e3.973.120logits idênticos bit a bit.
Três conversas produziram os mesmos26tokens/textos/términos. Na observação017
de segunda mensagem, preparação6,04→2,68s, com22tokens de prefixo reutilizados.
Isso é evidência no servidor; não é resultado no Snapdragon, do aplicativo
completo ou prova universal de ausência de diferenças em todo input/ARM.

Os fontes estão em speed019/runtime; relatórios em speed017/REPORT.md e
speed019/REPORT.md. As etapas017/019foram validadas no servidor. Depois, o estágio020compilou
e assinou uma nova préviaARM64com esses caminhos habilitados; o aplicativo
anterior permanece separado e preservado.
Ao aprender saídas hoje nulas, um checkpoint futuro deixa automaticamente de
ser elegível para esses atalhos; seu desempenho precisará ser medido novamente.

## Piloto de ensino conjunto, sem melhoria aceita

Oito atualizações supervisionadas do principal GERAL, explicações verificadas
mais respostas corretas somente nos alvos de treino; ambas as visitas do
Loop/mHC e operadores temporais no mesmo grafo.329tensores/2.675.888valores
elegíveis,224tensores/1.245.166valores efetivamente modificados.269tensores
com gradientes não nulos em cada passo;370congelados, incluindo153de visão,
idênticos;699hashes conferidos por restauração fria.

| Modelo | Controles gerais | Código thinking256 (2 tarefas) | Diagnóstico thinking1024 (1 tarefa) |
|---|---:|---:|---:|
| Qwen original |10/12|0/2|0/1|
| Liquid geral anterior |10/12|0/2|0/1|
| Novo treino018 |10/12|0/2|0/1|

Os códigos são exemplos ENSINADOS, não teste inédito. Todos esgotaram1.024tokens
no diagnóstico sem fechar pensamento e entregar uma resposta final. Os12textos
de controle permaneceram iguais aos do pai; os digests thinking256mudaram sem
produzir ganho de tarefa. O diagnóstico posterior1024não reabre a seleção.
Nenhuma validação reservada foi consumida. Nenhum resultado de benchmark
completo, ganho geral de inteligência ou superioridade contra4B foi medido.

A auditoria confirmou16saídas zeradas/congeladas em oito camadas neutras:
46.137.344valores. Elas bloqueiam o gradiente de60tensores anteriores; as contagens
por família coincidem com todos os oito logs. O próximo treino precisará abrir
essas saídas junto aos controladores, com replay/retencão geral. Isso é um limite
deste escopo, não causa exclusiva provada das falhas. O desenho de próximo
treino (incluindo alternativa de baixo posto) está em reasoning018/NEXT_TRAINING_DESIGN.md;
não foi executado como outro experimento.

Checkpoint experimental preservado: reasoning018/checkpoints/candidate.pt.gz,
SHA256 f25aac86011be54f5025f24be391a1f7076a7d4e9de234e05f4ead20ecf729ab.
Principal selecionado: rsi100/checkpoints/best.pt,
SHA25646f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8.
Restauração, falha/correção do auditor e recuperação após reconexão estão
registradas em reasoning018/REPORT.md; nenhuma atualização foi repetida.

## Pesquisa fornecida e projeto próximo de100M

A pesquisa CCORE/DSpine foi relida e o READMEoficial DSpine reconsultado.
O drafter público de2B não é compatível com nosso modelo e seu ganho GPU não
se transfere automaticamente ao celular. O runtime atual verifica tokens de
forma serial; precisa de verificação em bloco e rollback correto dos estados
antes de aproveitar um drafter mantendo o resultado do modelo principal.

Foi implementada a contagem auditável de uma variante textual com a mesma
organização32/56, mHC2, conv7/window256, largura256 e FFN1024:
**94.832.240parâmetros**, incluindo os embeddings compartilhados de248.320tokens.
É projeto dimensional, não pesos100M treinados nem promessa de qualidade igual.
Fontes, custos e limites: speed017/RESEARCH_REVIEW.md e parameter_budget.py.

Todos os estudos antigos, pesos e relatórios foram preservados. A busca RSI100
continua pausada. Artefatos e hashes finais são conferidos no recibo de publicação;
a evidência de velocidade é separada da rejeição do novo checkpoint.

## Entrega Android020 — prévia rápida0.1.1

Download: https://gofile.io/d/j7WqfPBY (~1,61GB, modelo geral integrado).
Instala como “Liquid Sense Rápido”, dev.liquidsense.chat.fast, ao lado da versão
anterior. Mostra tempo de preparação e tokens/s. Ainda sem seletor de modelos.
Usa o MESMO principal geral;018não foi integrado nem promovido.

APK SHA2563a8eab346270899706671c04bf900f0061fc713b798baf768c079063fa793bef,
1.613.898.825bytes. Assinatura/zipalign16KB/ELFARM64eJNI/atividade/classes
verificados. Todas as assets idênticas aoAPKoriginal, sem permissão INTERNET.
MD5/tamanho retornados peloGofile coincidem com o arquivo local e a página
respondeHTTP200. Não houve teste físico de telefone ou nova estimativa de
velocidade noSnapdragon. Fontes, manifest e recibo: android_fast020/README.md.
A chave privada nova ficou preservada localmente fora do repositório.
