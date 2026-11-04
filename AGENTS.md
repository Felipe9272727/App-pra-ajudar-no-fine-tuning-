# Retomada do experimento

- No novo piloto, leia primeiro `lab_rsi/status.json`, `lab_rsi/archive.json`
  (quando existir) e `lab_rsi/frozen.json` (quando existir). O primeiro piloto
  em `rsi/` é histórico e não autoriza desligar partes da arquitetura atual.
- Requisito do usuário: manter SenseNova loop/mHC e os componentes Liquid
  ativos em todas as novas candidatas. Use `lab_rsi/common.py:architecture_check`.
- O nome atual é `liquid sense 0.8 b LOOP`; informe que a base nominal é 0,8B
  e o híbrido ampliado tem aproximadamente 1,02B parâmetros carregados.

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
- O fluxo GitHub está em `.github/workflows/liquid-sense-benchmark.yml`.
  Use somente runners padrão públicos, até quatro máquinas de avaliação,
  quatro threads por máquina. Não habilitar cobrança ou runners maiores.
- Leia os jobs/artifacts antes de retomar um fluxo incerto. Depois de congelar
  e observar o teste, não reabra a seleção com esse mesmo teste.
