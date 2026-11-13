# Loop025 — fine-tuning específico do loop

**Concluído: três épocas, 24 atualizações, sem promoção.**
[Relatório e comparação](REPORT.md) · [Resultados brutos agregados](summary.json)
· [Seleção e regressões por caso](selection.json) · [Protocolo pré-registrado](PROTOCOL.md).

Treino supervisionado direto de 292 tensores / 48,34 milhões de valores do bloco
repetido: ganhos de visita, mHC, componentes temporais e normas, mais 16 matrizes
de saída antes zeradas. Ambas as visitas participaram da retropropagação.
Dados: 8 programas e 8 respostas gerais, repetidos por 3 épocas. É um piloto
CPU, sem adição de parâmetros e sem treinamento em larga escala.

Todas as épocas pioraram as tarefas novas de programação neste teste. A terceira
acertou 12/12 controles curtos, contra 10/12 do pai, mas caiu de 22/36 para 3/36
casos de programação e de 1/4 para 0/4 tarefas completas. O principal geral e o
APK 0.4 continuam selecionados. Os quatro problemas e quatro controles finais
novos ficaram sem consulta porque nenhuma época passou pela validação.

## Reprodução e recuperação

- `train.py`: executa o treino congelado; recusa reinício cego. `--resume` exige
  arquivo rolling exato e restaura pesos, otimizador/RNG e diário do último passo.
- `checkpoints/epoch01`, `epoch02`, `epoch03`: partes gzip/torch com todos os
  valores selecionados e estados de treino. Cada manifesto verifica cada parte
  e o SHA da sequência completa. Não são safetensors monolíticos independentes.
- `loop_runtime.load_variant('epoch1')`: restaura o pai imutável, aplica o overlay
  APÓS o loader legado e confere todos os 699 hashes. Requer as dependências e
  pesos-base já existentes neste projeto. Nunca aplique o loader legado depois.
- `evaluate.py`: comparação pareada original/pai/épocas; resultados completos são
  ignorados, sem novas gerações. O juiz existente e seus gabaritos não mudaram.
- `run_comparison.py`: fases seriais, seleção congelada e ablação da contribuição
  da segunda passagem mantendo todas as 56 chamadas. Sem trabalhadores ao final.
- `frozen_before_selector_fix.json`: fontes/dados usados no treino e avaliação.
  O manifesto atual registra só a correção de leitura de vetores ausentes em
  falhas com pontuação zero. `selector_recovery.json` documenta o ocorrido.
- `prior_apk024`: cópia deduplicada e exata do APK 0.4 assinado, com prova SHA
  anterior à retirada da cópia redundante de build. Veja comando de restauração
  em seu manifesto; os safetensors de apoio permanecem protegidos.

O desbloqueio de gradientes foi demonstrado, mas não um ganho de inteligência.
Há limitações de dados, arredondamento BF16 e normalização dos ganhos descritas
no relatório. Não usar os checkpoints experimentais como melhoria validada.
