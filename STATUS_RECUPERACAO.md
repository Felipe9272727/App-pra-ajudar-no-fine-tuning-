# Recuperação verificada — 11/11/2026

Repositório: Felipe9272727/App-pra-ajudar-no-fine-tuning-. A branch anterior
`codex/liquid-sense-review-loop-20261105` ainda apontava para
`0a70bfbd0a877c6e4793cc24742116581b0428a2`, conclusão do estudo012.
Só existiam diretórios vazios de013; nenhum processo de pesquisa estava ativo.
O trabalho atual está em `codex/liquid-sense-supervised-review-20261111`.

O checkpoint principal continua `rsi100/checkpoints/best.pt`, SHA256
`46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8`.
Ele referencia os pesos preservados do port híbrido e uma sobreposição; não é
um arquivo monolítico autossuficiente. Base nominal Qwen3.5-0.8B, híbrido com
1.020.252.592 parâmetros únicos carregados,32camadas físicas/56execuções,
mHC2, convoluções DeltaNet7 e janela local256 em três camadas.
É uma arquitetura inspirada em Loop/Liquid, não a implementação integral LFM3.
Há oito camadas inseridas neutras e roteadores mHC constantes no pai.

A segunda edição guiada por ativações já foi investigada e encerrada:
o salvamento original final não foi encontrado, então houve reconstrução
documentada, sem alegar identidade bit a bit. O arquivo reconstruído está em
`mentor/checkpoints/negative_002_recovered.pt`, SHA256
`8fd291019b20f7d327e775c05a30f5b991395718040e4ad2fe52ed986ff748ef`.
Alterava apenas down_proj da camada31 por edição de posto1. Reproduziu
11->12tarefas e69->72/81casos no desenvolvimento, mas na validação independente
ficou em78/192casos contra85/192do pai, ambos7/24tarefas: rejeitado.
Ver MENTOR002_VALIDATION_REPORT.md e mentor/validation_004/selection.json.

Também estão concluídos:31rodadas RSI rejeitadas, V3NCM arquivada, estudos003
a012 sem promoção. O012 mostrou influência do loop em texto, mas nenhum ganho
de casos ao comparar a segunda saída real com sua substituição pela primeira.
Não há motivo para repetir essas execuções ou retomar100loops.

Nova autorização do usuário em11/11: fornecer soluções corretas para ENSINO.
O013 implementa dados executáveis separados por família e pequenos adaptadores
supervisionados dentro do loop, por álgebra, sem gradientes/otimizadores.
Respostas corretas continuam excluídas das entradas de avaliação.
Os resultados deste estudo ficam em EXPERIMENTOS_CAPACIDADE.md e review013/.
