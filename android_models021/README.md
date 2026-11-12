# Liquid Sense0.2 — especialista015E integrada

Download: https://gofile.io/d/iNjQRGpN (~1,86GB, ARM64/Android9+).
SHA256cbbb380612e895bec91c56501e5f176e38702c786f8ad0ffaad2b104bb0ff126.

Este APK usa o checkpoint015E EXATO por padrão, com todos546tensores textuais
verificados contra os manifestosB/C/E. Não é a Base renomeada e não houve
novo treino/quantização. Preserva32camadas/56execuções,mHC2,conv7/window256,
incluindo os pesos/gains/roteadores aprendidos. PacoteBF16SHA256
840dcd740258147a244d3cde951f789f725ed4746f17de828a70e2b531cd0f70.

O resultado original foi8/8exemplosHumanEvalENSINADOS,0/8MBPPobservados e6/12
controles brutos, emPyTorch. Não é pontuação noHumanEvalcompleto. Na conferência
esta portaRust reproduziu7/8ensinados, com falha preservada emHumanEval/129;
controles brutos2/12. A exibição normal do app remove conteúdo anterior ao último
</think>, comportamento já existente, e acerta6/12controles. Essa exibição NÃO
substitui a avaliação bruta original. O8/8Python não foi reproduzido integralmente
noRust; diferenças de execução/prefill/aritmética ainda precisam de diagnóstico.
Nenhuma avaliação física noSnapdragon é alegada. Não ajustar pesos/gabaritos
para esconder a diferença; os pesos de015E estão conferidos bit a bit.

O seletor tem “Especializada · Experimental015E” (integrada/padrão) e “1.0Base ·
Geral”. Para evitar duplicar1,6GB, Base usa as assets públicas do app original
`dev.liquidsense.chat`, se instalado; se ausente, o app mostra link de instalação.
Não afirmar que ambos os pacotes estão dentro deste download. As conversas/cache
são separadas por modelo. Atualiza a préviaRápida (`dev.liquidsense.chat.fast`,
versionCode3) com o MESMO certificado, preservando o históricoBase anterior;
a chave legada de conversa também fica mantida. O app original continua separado.

E usa o template user-only/semthinking da avaliação original,320tokens eEOS248044;
Base conserva apresentação/192tokens. A UItrima a entrada como o templateHF.
O verificador inicial detectou retornoBatchEncoding/trim tratado errado antes
de escrever o modelo; a continuação reutilizou apenasUI/binários já concluídos.
Todos os20prefixos de teste coincidem com osIDsHuggingFace. A avaliação de porta
não inclui soluções/testes na entrada. Uma interrupção após7resultados retomou
somente os13restantes; a falha129não foi repetida para escolher um resultado.

AssinaturaV3/certificado anterior,CRC/layout4/16KB,ARM64/JNI/classe/seletor e todos
os546hashes de origem/exportação verificados. SemINTERNET nesta versão: busca
web/Python são o NOVO trabalho022, ainda não são funções desteAPK. Dados privados
(chave/senha/Gofiletoken) permanecem fora doGit. Upload: tamanho/MD5 conferidos,
páginaHTTP200. Os APKs/checkpoints/resultados anteriores foram preservados.

Empacotamento com pouco espaço: o modelo foi escrito direto noZIP_STORED alinhado.
O assinador validou todo prefixo de payload e guardou somente a cauda pequena de
assinatura, antes de editar o intermediário. FerramentasoficiaisAndroid validaram
o resultado. Source/templates, testes e recibos estão emtools/,native/,android/
e reports/. Nenhum novo checkpoint geral foi promovido.
