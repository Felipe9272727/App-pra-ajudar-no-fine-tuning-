# Liquid Sense 0.8B LOOP

## Prévia 0.4 — limites maiores e recuperação de ferramentas (13/11/2026)

[**Baixar APK 0.4 no Gofile**](https://gofile.io/d/hmAohFD5) (~1,62 GB, ARM64 / Android 9+). **Atualiza o Tools 0.3**, com o mesmo pacote e certificado, preservando suas conversas. Pesos gerais integrados; o seletor da Especializada 015E continua disponível.

O botão **Raciocínio** oferece Normal (até 2.048 tokens de resposta), Profundo experimental (1.024 para pensar + 2.048 de resposta) e Extenso experimental (2.048 + 4.096), por etapa. Contexto máximo de 16 mil tokens. Chamadas incompletas têm reparo limitado; resultados reais ficam na conversa, com Continuação e diagnóstico local.

**Mais thinking não demonstrou ganho:** no mesmo cálculo, o Normal anterior acertou e o Profundo repetiu marcadores sem responder. Normal permanece padrão. O teste de I/O com programa Python explícito passou; o uso espontâneo sem `print` não contou como número verificado. Mesmos pesos gerais e arquitetura híbrida preservada, sem novos treinos nem promoção de qualidade.

Assinatura, CRC, alinhamento, hashes e upload verificados. Esta versão 0.4 ainda não foi testada no telefone físico. [Guia](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/blob/3c241b8ef04294f2e00666aa81dfb1700e89840f/android_thinking024/README.md) · [Resultados e falhas preservadas](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/blob/3c241b8ef04294f2e00666aa81dfb1700e89840f/android_thinking024/REPORT.md) · [138 artefatos verificados](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/blob/3c241b8ef04294f2e00666aa81dfb1700e89840f/android_thinking024/ARTIFACT_VERIFICATION.json)

## Prévia0.3 — internet, Python e seletor de modelos (13/11/2026)

[**Baixar APK Tools0.3 no Gofile**](https://gofile.io/d/fowGW6q4) (~1,62GB, ARM64/Android9+, modelo geral integrado). App separado **Liquid Sense · Tools**. Busca real com fontes, consulta verificada à documentação Python e execução local de Python3 limitado (math/json/f-strings, sem pacotes externos), em serviço isolado.

O botão **Trocar modelo** fica abaixo do cabeçalho: Web e Python, Base geral offline e Especializada015Eoffline. Para a especialista, mantenha instalado/atualizado o [app0.2](https://gofile.io/d/iNjQRGpN); essa opção usa seus assets públicos e preserva seus dados. A especialista fez8/8programas ENSINADOS no PyTorch,7/8na portabilidade Rust e0/8transferência anterior: não é HumanEval completo.

Os novos treinos022e023foram salvos e **rejeitados**:022perdeu8→6programas ensinados;023caiu2/4→1/4nas tarefas de ferramentas. **APK usa o geral anterior, com Loop/mHC e operadores temporais preservados, sem overlays rejeitados.** Ferramentas ampliam o sistema; não há ganho novo geral/de pensamento nos pesos comprovado. Assinatura/CRC/zipalign/hashes e upload verificados; execução física no celular não medida.

[Guia e arquivos](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/blob/2cdd5d6af98b3cd969b975d8d0725faa4904d357/tooluse023/README.md) · [Resultados e limitações](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/blob/2cdd5d6af98b3cd969b975d8d0725faa4904d357/tooluse023/REPORT.md) · [Verificação de141artefatos](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/blob/2cdd5d6af98b3cd969b975d8d0725faa4904d357/tooluse023/ARTIFACT_VERIFICATION.json)

Experimento de Felipe: adaptar diretamente os pesos de Qwen3.5-0.8B a um decoder loop/mHC inspirado em SenseNova-Loop-9B e a operadores compatíveis inspirados em Liquid LFM3.

Registro inicial (histórico): calibração algébrica concluída; ciclos de melhoria e avaliação em preparação. Não há demonstração de autoaperfeiçoamento recursivo geral ou de ganho de inteligência.

Este repositório será usado para código, estado retomável, logs reais, checkpoints incrementais e resultados. O histórico inicial fica na branch `codex/qwen-sensenova-liquid-rsi-20261103`.

## Prévia rápida0.1.1 e estudos017–020 (12/11/2026)

[**Baixar APK no Gofile**](https://gofile.io/d/j7WqfPBY) (~1,61GB, ARM64/Android9+, modelo geral integrado). Instala separadamente como **Liquid Sense Rápido** e mostra preparação/tokens por segundo. Mesmos pesos gerais; o app anterior e seu histórico ficam preservados. Essa prévia0.1.1não tinha seletor; as versões0.2/0.3estão descritas acima.

No servidor, o protótipo Rust019teve **1,1633x de throughput do backbone** (14,04%menos tempo),12pares fixos,8testes técnicos e estados/tokens idênticos nos testes. APK ARM64assinado e verificado; **sem medição física no Snapdragon**. O piloto de treino conjunto018fez8atualizações e mudou224tensores/1.245.166valores, preservando10/12controles, porém0/2programas comthinking256e0/1no diagnóstico1024. **Rejeitado para promoção; principal geral preservado.** Variante94,8M é desenho dimensional, não modelo treinado nem prova contra4B.

[Relatório e comparações](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/blob/3887ac5c139a72756fe3640c65860f3118ccee7b/SPEED_REASONING_REPORT.md) · [171artefatos verificados](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/blob/3887ac5c139a72756fe3640c65860f3118ccee7b/RESEARCH_ARTIFACT_VERIFICATION.json) · [Fonte e verificação do APK](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/blob/3887ac5c139a72756fe3640c65860f3118ccee7b/android_fast020/README.md).

## Treino conjunto Loop/mHC e operadores temporais — estudo 016 (12/11/2026)

Uma candidata recebeu 16 atualizações supervisionadas conjuntas em 330 tensores elegíveis (6.345.904 parâmetros), incluindo Loop/mHC e operadores inspirados na Liquid. Mudaram efetivamente 298 tensores e 2.815.113 valores; os outros 369 tensores permaneceram idênticos ao especialista 015E. A arquitetura híbrida foi preservada.

| Modelo | HumanEval ensinado /8 | MBPP observado /8 | Controles /12 |
|---|---:|---:|---:|
| Qwen original | 1 | 0 | 10 |
| Principal geral preservado | 1 | 0 | 10 |
| Especialista 015E | 8 | 0 | 6 |
| Candidata 016 | 8 | 0 | 8 |

A candidata recuperou três controles e perdeu um contra E: 7 × 8 passou de 56 para 7. **Rejeitada para promoção por regressão e retenção insuficiente.** Principal geral e especialista anterior foram preservados. O único grupo adicional aprovado no MBPP aceita o zero constante como False; não demonstra aprendizado do algoritmo. Os oito problemas novos de programação e os oito controles corrigidos v2 ficaram sem consulta. O conjunto v1, com quatro fatos já existentes em estudos antigos, foi preservado sem uso. Nenhum ganho geral de inteligência ou vantagem sobre 4B foi demonstrado.

[Relatório e limitações](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/blob/a6a5d5f58f317dc9293caf9fe1956521a6dd7c85/BALANCED_JOINT_REPORT.md) · [Resultados](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/blob/a6a5d5f58f317dc9293caf9fe1956521a6dd7c85/balanced016/summary.json) · [Checkpoint experimental exato](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/blob/a6a5d5f58f317dc9293caf9fe1956521a6dd7c85/balanced016/checkpoints/final/manifest.json) · [Verificação dos 59 artefatos](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/blob/a6a5d5f58f317dc9293caf9fe1956521a6dd7c85/balanced016/artifact_verification.json).

## Treino supervisionado de todos os pesos de texto — estudo015 (11/11/2026)

Após autorização explícita para gradientes, foram treinados os546 tensores ativos de texto (919.659.696 parâmetros elegíveis), preservando visão e arquitetura híbrida. A comparação binária confirmou mudança em 546 tensores/483082021 valores. original: HumanEval ensinado 1/8, MBPP diagnóstico 0/8, controles 10/12; parent: HumanEval ensinado 1/8, MBPP diagnóstico 0/8, controles 10/12; specialist: HumanEval ensinado 8/8, MBPP diagnóstico 0/8, controles 6/12. As oito soluções HumanEval foram ensinadas deliberadamente: isso mede especialização, não um resultado limpo do benchmark ou inteligência geral. MBPP ficou fora do treino, mas já era observado no014. Estado: experimental_specialist_e_preserved_after_terminal_label_repair. O especialista foi preservado separadamente; o checkpoint principal anterior permanece selecionado. Sem alegação de superioridade contra4B.

[Relatório e regressões](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/blob/9b22cc6b3a28a98dbdadf88fb8dae2856d4754f3/SUPERVISED_TEXT_REPORT.md) · [Resultados](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/blob/9b22cc6b3a28a98dbdadf88fb8dae2856d4754f3/supervised015/final_summary.json) · [Pesos exatos](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/blob/9b22cc6b3a28a98dbdadf88fb8dae2856d4754f3/supervised015/attempt_e/checkpoints/candidate/manifest.json) · [Reprodução](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/blob/9b22cc6b3a28a98dbdadf88fb8dae2856d4754f3/supervised015/attempt_e/REPRODUCE.md).

## Respostas corretas nos pesos — estudo 014 (11/11/2026)

Oito soluções corretas do HumanEval supervisionaram a edição direta de uma matriz existente da camada31; depois foram avaliados esses oito problemas e oito diferentes do MBPP, com os mesmos prompts/configurações para cada modelo. original: HumanEval ensinado 1/8, MBPP diferente 0/8; parent: HumanEval ensinado 1/8, MBPP diferente 0/8; edited: HumanEval ensinado 1/8, MBPP diferente 1/8. O resultado no conjunto ensinado mede ajuste aos exemplos, não generalização. São subconjuntos de um piloto, sem pontuações completas dos benchmarks. O acerto adicional no MBPP falhou numa contraprova de quadrado mágico, e a candidata perdeu um controle exato de formato e piorou a NLL de linguagem. Nenhum checkpoint foi promovido; o anterior permanece selecionado.

[Relatório e limites](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/blob/713c8c69827f83a0cacbe56994ed8f23c2330939/DIRECT_BENCHMARK_REPORT.md) · [Pesos e estado](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/blob/713c8c69827f83a0cacbe56994ed8f23c2330939/supervised014/teaching.json) · [Reprodução](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/blob/713c8c69827f83a0cacbe56994ed8f23c2330939/supervised014/REPRODUCE.md).

## Aprendizagem supervisionada do loop — 11/11/2026

Estudo 013 concluído. A nova autorização permitiu ensinar com soluções corretas: 120 programas verificados, adaptadores algébricos na segunda passagem e dados separados por família. Comparação de geração livre: original: 0/8 tarefas, 36/160 casos; parent: 0/8 tarefas, 43/160 casos; loop: 0/8 tarefas, 39/160 casos; joint: 0/8 tarefas, 43/160 casos. Nenhum checkpoint promovido; preservar o anterior. A auditoria identificou que o avaliador histórico rejeita o nome Python válido `_`; escores e gabaritos foram preservados, com a limitação documentada.

[Resultados e limites](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/blob/6cefca0a1194e8551d7f6ba2a3c8c36dbe32c9d3/EXPERIMENTOS_CAPACIDADE.md) · [Estado recuperado](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/blob/6cefca0a1194e8551d7f6ba2a3c8c36dbe32c9d3/STATUS_RECUPERACAO.md) · [DSpine e fontes CCORE](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/blob/6cefca0a1194e8551d7f6ba2a3c8c36dbe32c9d3/PLANO_DSPINE.md).

## Loop, linguagem e edição temporal protegida — estudo 012, 05/11/2026

O loop altera estados internos: distância L2 relativa média de **5,98%** nos 21 pontos medidos. Substituir apenas sua segunda saída pela primeira mudou quatro de sete programas, mas não os acertos: **23/35 casos e 2/7 tarefas completas**, com zero ganhos/perdas. Sete replays da chamada real com cópia do cache foram bit-exatos. Isso demonstra influência funcional, sem ganho de programação demonstrado nessa amostra.

Em seis prompts neutros, a fala diferiu do Qwen em quatro. A revisão qualitativa sem nomes preferiu Liquid2, Qwen2 e empatou2, com vantagens específicas e falhas também; sem superioridade geral de linguagem.

Uma nova edição direta, sem gradientes ou respostas fornecidas, alterou **24.522 valores em duas matrizes de memória das camadas6,25**, protegendo amostras da primeira visita. Proposta e controle oposto permaneceram **23/35 e 2/7**. Ambos foram arquivados como experimentos; **best.pt continua intacto**. O reinício do executor foi registrado e a referência recuperada reproduziu todos os textos e casos antigos.

[Relatório, dados completos, pesos e limitações](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/blob/0a70bfbd0a877c6e4793cc24742116581b0428a2/LOOP_LANGUAGE_RESEARCH_REPORT.md). Branch `codex/liquid-sense-loop-language-20261105`. Validação inédita preservada, cinco novos testes técnicos passaram e estudo encerrado sem worker em segundo plano.

## Métrica contra 4B e tensores nos erros — diagnóstico 011, 05/11/2026

Python rastreou os **699 tensores de parâmetros** durante cinco respostas erradas e duas corretas: **417 decisões, 813 slots de módulos por decisão**. Os mesmos 546 tensores textuais foram acessados nos dois grupos; não há tensor exclusivamente ligado nos erros desses exemplos. Textos, casos e todos os hashes de pesos permaneceram idênticos aos anteriores.

A métrica implementada é **Delta4B em pontos percentuais de problemas totalmente resolvidos**, com testes pareados novos e retenção. O Qwen3.5-4B está fixado por revisão e hashes, mas **a comparação permanece não medida** neste ambiente. O resultado conhecido de desenvolvimento do Liquid é 11/16 tarefas e 69/81 casos.

Os maiores contrastes exploratórios apareceram nas projeções de decaimento DeltaNet das camadas25,6,28. Trinta intervenções de ativação de ±1% mudaram logits, mas nenhum argmax contra seus controles; não houve ganho de qualidade nem edição de pesos. Dados reais (216 MB) estão preservados sem perda em onze partes verificadas.

[Relatório, tabela de todos os tensores, métrica executável e limitações](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/blob/4f1e5558cee08353cb090300729f9dbaaac1549d/TENSOR_ERROR_ANALYSIS_REPORT.md). Branch `codex/liquid-sense-error-tensors-20261105`. Validação inédita preservada; estudo encerrado sem worker em segundo plano.

## Varredura integral e adaptação nativa 010 — 05/11/2026

Python examinou todos os **1.020.252.592 valores em 699 tensores únicos** do híbrido carregado, além dos buffers e de 20,45 milhões de pesos MTP preservados fora do runtime. Não encontrou pesos não finitos.

Foram construídos e salvos três candidatos com as 32 camadas ativas, 56 execuções e até 48 roteadores mHC condicionais, alterando até **140,1 milhões de valores**, sem gradientes ou respostas nas entradas. A triagem foi **8/36, 11/36 e 11/36 casos**, todos 0/7 tarefas, contra o parent **27/36 e 3/7** e o Qwen original **27/36 e 5/7**. **Nenhum foi promovido; best.pt permanece intacto.** A validação inédita não foi consumida.

[Relatório, comparações e forma correta de recarregar os checkpoints incrementais](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/blob/f123d822d04694f431cdf1277f14ed9467201653/NATIVE_ARCHITECTURE_REPORT.md). Fontes, pesos incrementais, hashes e ativações estão na branch `codex/liquid-sense-native-audit-20261105`. Os 55 testes técnicos e as nove sondas de cache passaram. Estudo encerrado, sem processo em segundo plano e sem demonstração de superioridade sobre modelos maiores.

## Pesquisa mais recente — edições distribuídas 008/009 concluídas

[Relatório e comparações, fixados por commit](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/blob/f8a0a7f5801baeeb225aad38996e951c6f00ded7/MULTI_TENSOR_REPORT.md).
[Código, pesos e estado retomável](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/tree/codex/liquid-sense-multi-tensor-20261105).

Foram construídas duas candidatas independentes por edição direta: 32.281 valores em 40 tensores de normalização, e 4.994.722 valores em quatro matrizes MLP das camadas 5, 13, 25 e 31. Sem gradientes nem soluções corretas nas entradas; o original forneceu apenas vetores internos dos enunciados.

Na mesma triagem de sete problemas, ambas fizeram 27/36 casos e 3/7 tarefas completas, iguais ao híbrido pai. Controles inversos também não acrescentaram acertos. Não houve ganho demonstrado e nenhuma candidata foi promovida. O checkpoint anterior permanece selecionado.

Foram preservados e conferidos 22 artefatos de tensores, com os pesos exatos e as ativações. Os 46 testes técnicos passaram. Os testes de modelo terminaram; não há execução permanente nem retomada automática das 100 rodadas. O conjunto reservado continua sem execução nesta continuação, pois as candidatas falharam na triagem.

## Pesquisa anterior — diagnóstico concluído em 2026-11-05

[Relatório completo, fixado por commit](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/blob/c57b3124986268e495ff5324bdfdbe831028970e/ERROR_ANALYSIS_REPORT.md).
[Código, checkpoints e estado retomável](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/tree/codex/liquid-sense-error-analysis-20261105).

As edições diretas 006 e 007 foram concluídas sem promoção. A 006 ganhou um caso de programação, mas piorou a NLL de linguagem contra o pai. A 007 separou os fluxos mHC que operavam em igualdade, porém não mudou os acertos. Os pesos anteriores e os cinco novos artefatos de tensores foram preservados e conferidos.

Nos mesmos 16 problemas de desenvolvimento, o Qwen original resolveu 12 tarefas e 66/81 casos; o híbrido preservado resolveu 11 tarefas e 69/81 casos, ambos com 4/4 controles. São trocas entre tarefas, sem superioridade geral demonstrada. Em três problemas diagnósticos já observados, com raciocínio e até 1.024 tokens, o Qwen concluiu 2/3 respostas corretas e o híbrido 0/3, preso em repetição. O modo de raciocínio ficou opcional e experimental.

O checkpoint híbrido pai continua selecionado. Nenhuma melhoria nova nos pesos foi validada. Todos os testes deste ciclo terminaram; nenhum processo de modelo foi deixado rodando entre turnos.

## Retomada concluída em 2026-11-05

Estado desta etapa histórica: [branch de recuperação e validação](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/tree/codex/mentor002-independent-validation-20261104).
[Relatório completo, fixado por commit](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/blob/478cc5933a11925ef050507ae4f761234f0569ad/MENTOR002_VALIDATION_REPORT.md).

A hipótese 002 original tinha somente sua triagem salva; o checkpoint final não foi encontrado no estado persistido acessível. A reconstrução da hipótese reproduziu 11→12 tarefas e 69→72 casos no desenvolvimento, com 4/4 controles. Não se afirma identidade bit a bit com os pesos não salvos.

Na validação nova congelada (24 tarefas / 192 casos), Qwen original fez 5/24 e 71/192; híbrido pai fez 7/24 e 85/192; candidata reconstruída fez 7/24 e 78/192. Todos fizeram 6/12 controles estritos, com limitações e diferenças por item documentadas. A candidata ganhou 5 casos, perdeu 12 e não ganhou tarefas completas em relação ao pai. **Sem promoção: manter o checkpoint pai.**

Seleção preservada: `rsi100/checkpoints/best.pt`, SHA256 `46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8`.
A candidata, suas ativações e todos os resultados continuam arquivados como experimento. Loop/mHC + operadores inspirados em Liquid permanecem ativos; o híbrido tem aproximadamente 1,02B parâmetros carregados. Os 31 descartes antigos e a V3 NCM foram preservados. A busca automática não foi reiniciada. Avaliação concluída, sem processo de pesquisa em segundo plano.

## Pesquisa guiada e identidade — conclusão de 2026-11-05

Continuação atual: [código, pesos e artefatos](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/tree/codex/liquid-sense-reasoning-20261105).
[Relatório fixado por commit](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/blob/982cafd27ae51847d3dabdbbddc17919c723ea29/REASONING_BENCHMARK_REPORT.md).

Foram testadas três novas hipóteses: reforço dos pesos de visita em camadas selecionadas por ativações, edição direta da MLP com proteção de 137 estados e terceira visita seletiva (80 execuções de camada). As intervenções de loop não ganharam casos na triagem. A edição da MLP fez 69→70 casos de desenvolvimento, com controles preservados, mas piorou a NLL das âncoras (3,183729→3,189105) e foi rejeitada. **Nenhuma candidata promovida; manter o pai.**

| Piloto em subconjuntos fixados | Qwen original | Liquid Sense preservado |
|---|---:|---:|
| LiveCodeBench v6 (8 problemas) | 1/8 | 2/8 |
| GSM8K, resposta concisa (16 questões) | 1/16 | 1/16 |
| IFEval estrito (12 prompts) | 8/12 | 8/12 |

Os protocolos locais usam limites e um executor restrito; não reproduzem as pontuações completas publicadas pela Liquid AI. As amostras são pequenas, com trocas de acertos detalhadas no relatório e sem evidência estatística de superioridade geral.

O chat se apresenta como **Liquid Sense**, projeto independente conduzido por um desenvolvedor, com base Qwen e adaptações inspiradas em SenseNova/Liquid. Essa identidade é configuração da aplicação, sem alegação de aprendizado nos pesos nem de criação do Qwen do zero. A apresentação real e suas tentativas estão preservadas.

Foram aprovados 39 testes técnicos. Pesos anteriores, candidatas e ativações permanecem arquivados. A execução terminou; nenhum processo de pesquisa ficou em segundo plano.
