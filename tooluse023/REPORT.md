# Estudo023 e prévia Android com ferramentas

A nova edição de pesos foi rejeitada: a base geral fez2/4 e a candidata1/4 no
screen de ferramentas já observado. A candidata calculou MDC quando o pedido
era MMC: chamou math.gcd(84,198), executou de verdade, recebeu6 e o chamou de
MMC. O pai entregava2772. É uma regressão de conceito/programação, não execução
simulada. Sem aprovação no screen, os quatro problemas novos permaneceram
fechados e não se executaram as etapas posteriores de preservação/validação.
O principal geral best.pt e a especialista015E continuam intactos.

| Protocolo de pesquisa, PyTorch CPU | Final correta com ferramenta real |
|---|---:|
| Qwen original,022 |3/4|
| Especialista015E,022 |0/4|
| Adaptador022 sobre015E |0/4|
| Base geral preservada,023 |2/4|
| Edição023 sobre a base geral |1/4|

São quatro problemas próprios. Não estabelecem superioridade geral. As buscas
ao vivo diferiram: o original recebeu documentação relevante do Brave; o geral
recebeu fallback Yahoo com páginas sem relação numa consulta formulada de outro
modo. A comparação da parte web está confundida por formulação/provedor/dados
externos. O original também acrescentou descrição falsa de heappush, embora
passasse o critério automático de citar uma URL retornada. A regressão numérica
MDC/MMC usa Python determinístico e permanece uma falha inequívoca da candidata.

023 coletou631estados durante geração real com cache, forçando rótulos SOMENTE
no ensino. A reconstrução da última MLP coincidiu com100%dos argmax nativos;
diferença máxima de hidden.0625. Isso valida o cache de ensino, não631respostas
corretas. Posto32na última down_proj,147456valores fatorados,32768treinados,
32atualizações AdamW. Os demais698tensores ficaram inalterados, incluindo os
controladores Loop/mHC e operadores temporais, que continuaram executados.
Não foi treino conjunto novo dessas famílias nem aprendizado de profundidade.

A norma FP32da projeção subestimou o limite; antes de qualquer inferência da
candidata, auditoria FP64 e projeção determinística impuseram o mesmo limite
flutuante1%, sem novos gradientes ou seleção por resultado. Originais e pesos
projetados foram preservados. A matriz projetada mudou2.236.588valores BF16,
SHAf115abb22c7f30856d368f720f1cbad76fdb4cdee69fa3801f705bd865f65289.
A diferença do peso após arredondamento BF16 foi1,005412%, registrada à parte
da restrição sobre o fator flutuante. Os fatores podem ser absorvidos no peso;
não se anuncia um modelo de1,2Bpor esse mecanismo. Nenhuma edição023vai ao APK.

O APK0.3.0Tools é uma integração de software sobre a base geral preservada:
busca real, Python local limitado e etapa de conferir a observação/concluir.
Esse controle do aplicativo é separado do loop neural de56visitas/32camadas.
Não representa aumento comprovado de inteligência ou pensamento aprendido.
O Qwen original já tem capacidade de emitir chamadas estruturadas; o aplicativo
é quem fornece as ferramentas e devolve resultados reais.

O app usa uma instalação separada dev.liquidsense.chat.tools e incorpora os
pesos gerais. Trocar modelo aparece abaixo do cabeçalho. Há WebePython, Base
geral offline e Especialista015Eoffline. Esta última usa os assets públicos do
app especialista0.2instalado (versão>=3), com botão para instalar/atualizar quando
necessário. Seus dados privados não são lidos e seus históricos são mantidos.
O pacote geral SHA6c774a434438add704b1993b8e013493fb95bc9802c4d9b30227832115c07288
é idêntico ao anterior, com546tensores de texto. Sem sidecar rejeitado.

Busca: HTTPS real Brave/Yahoo, títulos/URLs/trechos e hashes. Como o fallback
trouxe páginas irrelevantes para APIs Python, o app também consulta documentação
oficial para símbolos pontuados: deriva módulo/símbolo da consulta, baixa HTML
real e exige a âncora exata. É busca genérica por stdlib, sem respostas de teste
armazenadas. Provas JavaHTTPS em math.sin e json.loads passaram, incluindo hash
do documento e trecho real. Consultas gerais continuam nos buscadores públicos.
Só consultas saem para a web; inferência e Python são locais.

Python: MicroPython1.26.1,subconjuntoPython3com math/json e f-strings,16MiBde heap,
limites de saída/instruções/pilha/tempo, serviço Android em UIDisolado, sem API
exportada, arquivos/rede/pacotes externos. Não é CPython de desktop/NumPy.
Testes passaram para contas, JSON, falhas e limites, estado limpo após falhas,
stdout comNUL e rejeição deNUL no programa. O primeiro teste do app encontrou
f-string desativada: preservou-se a falha, habilitou-se a sintaxe e verificou-se
o mesmo programa válido no executor, sem nova geração/alteração de resposta.

Na prova nova RustLinux+C, o modelo gerou código, executou e entregou3311para
soma dos quadrados1..21. A busca math.sqrt também foi executada, mas o provedor
trouxe páginas genéricas de matemática; o modelo reconheceu que não tinha a
informação específica e não citou uma fonte, falhando o critério final. Total
1/2nesta prova, diferente do0/2inicial com o interpretador anterior. A melhoria
do componente de documentação foi verificada depois em JavaHTTPS; não se
reescreveu o score antigo nem se atribuiu isso aos pesos.

Rust ARM64, recursos Android, Java/DEX,JNI e16KiBELF compilaram. Oito testes Rust,
três templates iguais aoHF, onze testes Java e provas dos executores passaram.
Assinatura oficial Android/CRC/zipalign e hashes do pacote foram verificados.
Modelo, otimizadores, matrizes, caches, logs e builds anteriores têm cópias
verificadas. Chaves privadas/tokens não fazem parte do repositório ou APK.
Não houve execução física no Snapdragon; trata-se de uma prévia para teste.
