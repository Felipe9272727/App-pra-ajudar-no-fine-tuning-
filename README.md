# Liquid Sense 0.8B LOOP

Um projeto independente conduzido por um desenvolvedor, dedicado a investigar
programação e raciocínio por meio de alterações verificáveis nos pesos.
A base pré-treinada é **Qwen3.5-0.8B**; o híbrido com componentes inspirados em
**SenseNova Loop/mHC e Liquid AI** carrega aproximadamente **1,02B parâmetros**.

## Pesquisa mais recente — diagnóstico e edições 006/007

[Relatório e comparações](ERROR_ANALYSIS_REPORT.md),
[estado retomável](reasoning/cycle2/status.json) e
[seleção](reasoning/cycle2/selection.json).
O checkpoint híbrido pai continua selecionado; nenhuma nova edição foi promovida.

Na comparação dos mesmos 16 problemas de desenvolvimento, Qwen original
resolveu 12 tarefas e 66/81 casos; o híbrido preservado resolveu 11 tarefas
e 69/81 casos. Ambos fizeram 4/4 controles. A edição 006 ganhou um caso,
mas piorou a NLL de linguagem contra o pai e foi rejeitada. O resultado
mistura ganhos e perdas entre tarefas, sem superioridade geral demonstrada.

Também foi confirmado que os dois fluxos mHC permaneciam idênticos durante
as gerações medidas, com roteadores de entrada zerados. A edição 007 alterou
dois parâmetros FP32 para separar os fluxos, preservando a média dos ganhos.
A separação ocorreu, mas candidata e controle inverso mantiveram 25/31 casos
da triagem. Ambos os checkpoints experimentais estão preservados.

Há um modo de raciocínio nativo opcional, sem mudança nos pesos selecionados:

```bash
python liquid_sense_chat.py --thinking --max-new-tokens 1024 --message "Como você verifica uma solução?"
```

Esse modo é experimental e usa mais tokens. O diagnóstico de conclusão
está no relatório: até 1.024 tokens, Qwen concluiu 2/3 respostas corretas
e o híbrido 0/3, em três problemas já observados. Ele não virou o padrão
e não demonstra melhoria geral nem aprendizado novo.
O chat informa quando não obteve resposta final dentro do orçamento.

## Pesquisa anterior — 2026-11-05

A continuação usa ativações da geração real, hipóteses pré-registradas e
comparações com rollback. As hipóteses 003 e 005 reforçaram contribuições e
profundidade do loop, sem aumentar os acertos da triagem. A hipótese 004 ganhou
um caso de programação, mas piorou a NLL das âncoras e não foi promovida.
O checkpoint pai permanece selecionado. Não há alegação de maior inteligência.

- [Estado atual](reasoning/status.json) e [protocolo](reasoning/PROTOCOL.md).
- [Benchmarks oficiais de origem e subconjuntos locais](benchmarks/reasoning_20261105/README.md).
- [Decisões e seleção de pesos](reasoning/selection.json).
- [Validação anterior da hipótese 002](MENTOR002_VALIDATION_REPORT.md).

A apresentação do chat dá crédito ao projeto independente e preserva a origem
no Qwen. Essa configuração de identidade não é uma melhoria aprendida nos pesos
e fica fora dos benchmarks. Para consultar a apresentação ou conversar:

```
python liquid_sense_chat.py --about
python liquid_sense_chat.py --message "Quem é você?"
```

## Resultados do ciclo anterior

| Subconjunto local | Qwen original | Liquid Sense (pai preservado) |
|---|---:|---:|
| LiveCodeBench v6 — 8 problemas | 1/8 | 2/8 |
| GSM8K — 16 questões, resposta concisa | 1/16 | 1/16 |
| IFEval estrito — 12 prompts | 8/12 | 8/12 |

As amostras são pequenas e os protocolos locais têm limites e restrições;
esses números não equivalem aos benchmarks completos da Liquid AI nem
estabelecem superioridade geral. Nenhuma nova candidata foi promovida.
[Relatório completo](REASONING_BENCHMARK_REPORT.md),
[saídas e estatísticas](benchmarks/reasoning_20261105/summary.json) e
[teste de identidade do chat](reasoning/identity_probe.json) estão preservados.

## Histórico preservado — busca de 100 tentativas

O estágio abaixo foi pausado após 31 rejeições; não foi reiniciado nesta
continuação. Seus registros, pesos e checkpoints permanecem preservados.

Protocolo deste estágio histórico: 100 rodadas de busca direta em pesos, sem gradientes. Cada tentativa
parte do melhor checkpoint. Pioras e empates são descartados; o melhor é restaurado
após cada avaliação e salvo no Git. Não são 100 passagens internas do decoder.
O híbrido SenseNova + Liquid permanece ativo com 2/3/4 passagens internas.

- [Protocolo de aceitação e limites](rsi100/PROTOCOL.md)
- [Estado real e contador](rsi100/status.json)
- [Execução](.github/workflows/liquid-sense-rsi100.yml)
- [Relatório ao concluir](RSI100_REPORT.md)

A busca repetida usa explicitamente tarefas observadas como currículo. Validação
e teste novos medem transferência; o teste final não escolhe pesos. É adaptação
por busca com recompensa, não prova de autonomia ou de ser o melhor modelo pequeno.
A execução espera a avaliação anterior terminar antes de consumir novas CPUs.

---

# liquid sense 0.8 b LOOP — programação e loops experimentais

Pedido atual: melhorar programação por edição direta dos pesos e feedback de
execução, mantendo SenseNova + Liquid. Estado em `code_rsi/status.json`.
O novo conjunto tem 48 funções Python em quatro divisões; é um piloto pequeno.
O modelo recebe enunciado e seu próprio feedback, sem soluções de referência
ou respostas-alvo nos prompts. Todos os pesos experimentais são salvos.

Testar gates e caches para duas, três e quatro passagens pelo bloco compartilhado.
Mais computação não garante melhor raciocínio. Não há alegação de ser o melhor
modelo pequeno ou de já ter qualidade geral excepcional. A base nominal é 0,8B;
o híbrido ampliado carrega aproximadamente 1,02B parâmetros.

- [Protocolo e referências](code_rsi/PROTOCOL.md)
- [Estado real](code_rsi/status.json)
- [Workflow atual](.github/workflows/liquid-sense-coding-rsi.yml)
- [Relatório ao terminar](CODE_REPORT.md)

O ciclo 2 anterior está concluído: nenhuma edição foi promovida.
Os resultados anteriores foram preservados abaixo e no histórico.

---

# liquid sense 0.8 b LOOP — RSI ciclo 2

Continuação da V2 híbrida ativa. A V3 NCM foi arquivada separadamente.
A base nominal Qwen é 0,8B; o híbrido ampliado carrega cerca de 1,02B parâmetros.
Componentes inspirados em SenseNova e Liquid permanecem ativos; não são
os modelos completos nem seus pesos pré-treinados.

O ciclo atual escreve diretamente a última matriz MLP, em três etapas de
regressão fechada sem gradientes. O assistente definiu e controla o programa;
não é autoaperfeiçoamento autônomo. Cada etapa salva pesos, erros e decisão
em commit. Nenhum ganho é garantido.

- Protocolo: [lab_rsi/PROTOCOL.md](lab_rsi/PROTOCOL.md).
- Estado: [lab_rsi/status.json](lab_rsi/status.json).
- Execução: [.github/workflows/liquid-sense-rsi-cycle2.yml](.github/workflows/liquid-sense-rsi-cycle2.yml).
- Resultados anteriores: [history/PILOT1_REPORT.md](history/PILOT1_REPORT.md).
- Relatório novo após conclusão: [LAB_REPORT.md](LAB_REPORT.md).

No piloto anterior, híbrido 39/64 e original 34/64 em teste customizado.
Nenhuma edição nova passou na validação. O ciclo 2 começa dessa base híbrida,
usa perguntas novas e seleciona principalmente por respostas exatas geradas.
O teste final não escolhe pesos.

Reprodução CPU: instalar requirements-ci.txt e torch 2.15.0+cpu;
executar download_model.py, build_sensenova_port.py e python lab_rsi/ci.py develop.
O workflow organiza validação, congelamento e teste final sem misturar conjuntos.
Não repetir o teste observado para selecionar edições.
Os comandos do histórico abaixo não definem o ciclo atual.

---

# liquid sense 0.8 b LOOP

Nome nominal da base: 0,8B. Híbrido ampliado: aproximadamente 1,02B parâmetros carregados.

Novo piloto baseado em referências públicas de pesquisa automatizada: [LAB_METHODS.md](LAB_METHODS.md). SenseNova e componentes inspirados na Liquid devem permanecer ativos nas novas candidatas.

Execução paralela do novo piloto em CPUs padrão do GitHub: [GITHUB_ACTIONS.md](GITHUB_ACTIONS.md).
Estado atual do novo piloto: `lab_rsi/status.json`. O primeiro piloto abaixo é histórico.

## Primeiro piloto concluído

Código, estado retomável, patch de calibração e seis rodadas reais salvos. Nenhuma das seis candidatas de RSI venceu o critério de desenvolvimento; o checkpoint foi preservado.

| Teste novo, 24 perguntas | Acertos |
|---|---:|
| Qwen original | 17/24 |
| Loop adaptado preservado | 18/24 |
| Loop + componentes inspirados no LFM3, experimental | 19/24 |

A vantagem de duas perguntas é limitada e não prova melhora geral. A variante experimental permanece registrada, sem promoção com base no teste. Consulte [PILOT_REPORT.md](PILOT_REPORT.md) para todas as respostas e decisões. Estado atual: piloto concluído e pausado no checkpoint.


Experimento de Felipe. O assistente ChatGPT Work controla os ciclos: propõe
uma alteração, escreve valores diretamente nos pesos, mede o resultado e
aceita ou rejeita a candidata. A IA pequena também produz sugestões reais,
registradas sem correção em cada rodada. A escolha executada é identificada
como decisão do assistente; não inventamos uma proposta da IA quando ela falha.

Isso é uma pesquisa de melhoria guiada com feedback. Não é demonstração de
autoaperfeiçoamento recursivo geral, consciência da arquitetura ou crescimento
ilimitado de inteligência. O estado real está em `rsi/status.json`.

## Modelo e alterações

- Base pública: `Qwen/Qwen3.5-0.8B`, revisão fixa no manifesto.
- Núcleo SenseNova: 32 camadas físicas, bloco [4,28) visitado duas vezes,
  56 execuções, mHC de duas vias. Dimensões menores do Qwen preservadas.
- Controle por visita: divide a contribuição residual entre primeira e
  segunda passagem. Na inicialização conservadora, duas sondas tiveram logits
  idênticos aos do Qwen original.
- LFM3: inspiração na convolução curta de sete posições e na atenção local
  de 256 tokens. Mantemos Gated DeltaNet do Qwen; não é a arquitetura completa
  ou os pesos treinados do LFM3.
- Ajuste dos pesos de convolução por regressão ridge fechada, regularizada
  pelo original, usando ativações em oito textos. Zero backward passes.
- A adaptação é aprendida por dados e feedback. Não é correto chamá-la de
  processo totalmente sem aprendizagem só por não usar gradientes.

O arquivo `v2_adaptation/closed_form_fit.json` registra os coeficientes
efetivamente alterados. Os pesos de entrada e os conhecimentos do LFM3 não
foram transplantados entre espaços latentes incompatíveis.

## Persistência e retomada

`checkpoints/liquid_patch.pt` guarda exatamente os pequenos tensores ajustados
(carregar com `weights_only=True`). `checkpoints/incumbent.json` registra o
modelo base, revisão, receita de cirurgia e hash do patch. Juntos com o código,
permitem reconstruir o mesmo checkpoint sem versionar gigabytes de pesos base.
`rsi/round_*.json` preserva proposta, sugestão real da IA, métrica, decisão e
estado. As gravações locais usam arquivos temporários, fsync e troca atômica.
O GitHub preserva os checkpoints confirmados; o campo `pending` ajuda a detectar
uma rodada interrompida. Não repita uma rodada finalizada.

Os arquivos `data_v2.json` separam oito textos de calibração, oito problemas
de desenvolvimento e 24 testes novos. Somente desenvolvimento decide promoção.
O teste reservado é executado depois de congelar o estado e nunca escolhe pesos.

## Executar

Instale primeiro PyTorch CPU e dependências:

```bash
pip install torch==2.15.0+cpu --index-url https://download.pytorch.org/whl/cpu
pip install transformers==5.22.1 accelerate==1.15.0 safetensors==0.8.0 numpy
python download_model.py
python build_sensenova_port.py
```

Para reconstruir os ajustes algébricos desde o início, em vez do patch salvo:

```bash
python v2_adaptation/experiment.py teacher
python v2_adaptation/experiment.py adapt
```

Uma rodada é executada pelo controlador com uma receita explícita, por exemplo:

```bash
python rsi_cycle.py --round 1 --gain 0.05 --beta 0.025 --liquid-mix 0 --reason "Dividir a contribuição entre camadas originais e inseridas"
```

A numeração precisa coincidir com o checkpoint atual; use `rsi/status.json`.
Uma candidata só é promovida se reduzir a NLL média de desenvolvimento em mais
de 0,0001. Isso não garante melhora em perguntas novas. Sugestões do modelo são
dados para inspeção, não comandos que serão executados automaticamente.

O experimento roda em CPU durante a sessão. Este repositório não promete um
serviço de treinamento permanente nem dispara gastos ou APIs pagas.

## Fontes e licenças

Qwen e código SenseNova são Apache-2.0, conforme seus repositórios. A licença
e o aviso de atribuição estão incluídos. O LFM3 serve como referência de desenho:

- https://huggingface.co/Qwen/Qwen3.5-0.8B
- https://github.com/OpenSenseNova/SenseNova-Loop
- https://www.liquid.ai/blog/lfm3
- https://arxiv.org/abs/1511.05641 — transformações que preservam a função
- https://arxiv.org/abs/2605.23872 — amortecimento de computação em loops

As adaptações específicas deste repositório são experimentais. Resultados e
limitações devem ser lidos antes de alegar que o modelo melhorou.
