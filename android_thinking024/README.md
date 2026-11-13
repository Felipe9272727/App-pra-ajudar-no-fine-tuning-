# Liquid Sense Tools 0.4 — limites e recuperação de ferramentas

[**Baixar APK 0.4 no Gofile**](https://gofile.io/d/hmAohFD5) — cerca de 1,62 GB,
ARM64 / Android 9+. Atualiza o Tools 0.3 mantendo as conversas.
[Resultados completos](REPORT.md) · [Comparação e logs](reports/comparison.json).

Atualização de software do app0.3, sem treinamento nem mudança de pesos.
O APK usa o mesmo pacote Android/certificado, com versionCode2, preservando
as conversas. A Base geral está integrada; a Especializada015E continua
opcional pelo app especialista instalado. Não é promoção de qualidade geral.

A captura do usuário mostra um cartão de busca seguido de erro genérico de
chamada inválida. Sem a pergunta e saída bruta originais, a causa exata não
pode ser reconstruída. O código0.3 tinha256tokens/etapa, thinking desabilitado
e um limite nativo de2048tokens de contexto, apesar de solicitar4096.

| Perfil | Raciocínio máximo | Resposta/chamada máxima |
|---|---:|---:|
| Normal, padrão preservado | sem trecho thinking explícito | 2048 |
| Profundo experimental | 1024 | 2048 |
| Extenso experimental | 2048 | 4096 |

Contexto máximo16384tokens, incluindo entrada, thinking e resposta reservada.
Até6etapas do modelo/4ferramentas reais por mensagem; saída agregada limitada
a16384tokens. Os números são tetos, não comprimentos mínimos. O modelo pode
terminar antes. Os perfis não treinam o modelo nem aumentam o número de loops.
Continuam32camadas físicas/56visitas, com mHC e operadores temporais híbridos.

A reserva de resposta é separada do thinking. Ao esgotar o orçamento de
raciocínio, o motor pode inserir apenas o fechamento de protocolo </think>,
registrando isso no diagnóstico. Não insere gabaritos. Mais tokens podem
causar mais demora e repetição; o modo longo não é uma melhoria validada.

Chamadas só são executadas após estrutura/argumentos completos e válidos.
Há uma tentativa de reparo de formato, sem executar código parcial. Resultados
reais já recebidos permanecem na conversa. Chamadas bem-sucedidas idênticas
não são repetidas. O chat oferece Continuar resposta e Copiar diagnóstico;
esses dados são locais, sem envio automático. Diagnósticos incluem texto da
conversa e saídas brutas: copiar é uma ação explícita do usuário.

## Verificação e reprodução

- `AgentTests.java`:27 verificações do parser/agente com respostas simuladas;
  esses testes não medem capacidade do modelo.
- Rust:16 testes; compilação ARM64 com alinhamento de16KiB.
- `verify_templates.py`:8comparações com template oficial HuggingFace;
  distingue a transcrição Python dos testes nativos compilados existentes.
- `NativeAgentSmoke.java`:modelo Rust real + mesmo agente Java + intérprete
  C MicroPython real no host; não equivale a execução no telefone.
- Saídas e comparações de inferência em `reports` e `logs`.
- `build_apk.py prepare`, depois `seal`:pesos gerais idênticos, assinatura e
  alinhamento verificados com ferramentas oficiais do Android.
- `deliver.py`:upload Gofile; tokens de conta convidados ficam fora do Git.

A cópia de build do APK0.3 pode ser substituída por arquivo deduplicado após
reconstrução SHA-256 byte a byte. A restauração está documentada em
`artifacts/prior_tools023/manifest.json`; os pesos imutáveis de apoio nunca
podem ser removidos. O download0.3 antigo continua preservado.

As compilações intermediárias024e seus resultados ficam preservados. O primeiro
smoke Python executou uma expressão sem print: houve execução real, mas stdout
vazio, portanto não foi considerado cálculo verificado. O agente agora devolve
um aviso genérico sobre esse comportamento do runtime, sem inserir resultados.
O smoke detectou também um marcador im_end vazando na implementação024inicial;
a regra de parada geral anterior foi restaurada antes de distribuir o APK.
