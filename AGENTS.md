# Retomada do experimento

- Leia `rsi/status.json`, `rsi/pending.json`, `checkpoints/incumbent.json` e a
  última rodada antes de rodar inferência. Não repita rodada finalizada.
- O pedido atual é edição direta dos pesos com adaptação algébrica e feedback;
  não usar backpropagation/otimizadores de gradiente sem nova instrução do usuário.
- O assistente é o controlador. Sugestões reais do modelo devem ser preservadas
  como saíram; não inventar sugestões ou alegar autonomia que não ocorreu.
- Propostas são avaliadas em desenvolvimento. Não promover pesos por resultado
  do conjunto reservado. Depois que o teste reservado for observado, uma nova
  pesquisa precisa de outro teste final ainda não usado.
- Salve rodada, checkpoint incremental e estado no GitHub após cada decisão.
  Confirme o commit/ref antes de afirmar que foi salvo. Não usar force push.
- Compare sempre com o original sob o mesmo protocolo. Descreva as partes LFM3
  como inspiração compatível, não como o modelo Liquid completo.
- Campos `pending` e `status` devem refletir a execução real; não afirmar que um
  processo continua rodando depois de encerrado.
