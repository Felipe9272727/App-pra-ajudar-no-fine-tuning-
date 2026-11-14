# Modelos atuais próximos do Liquid Sense principal — 14/11/2026

O principal já herda o pré-treino e o pós-treino do Qwen3.5-0.8B. Tem suporte
a thinking e executa o loop neural. A diferença a investigar é a eficácia das
adaptações, o treinamento delas e o custo de executá-las. Esta revisão não
avalia os filhos18M/95M, não executa benchmarks e não altera pesos ou APK.

## Comparáveis consultados em fontes oficiais

| Modelo | Faixa / inventário público consultado | O que sua receita acrescenta |
|---|---|---|
| [Qwen3.5-0.8B](https://huggingface.co/Qwen/Qwen3.5-0.8B) | 0,8B nominal; 852.985.920 carregados no nosso executor original | GatedDeltaNet+atenção, thinking/não-thinking e MTP já aparecem na base. Precisamos preservar essas capacidades ao alterar o grafo. |
| [BotPsy-0.8B](https://huggingface.co/qvac/BotPsy-0.8B) | 852.985.920; mesma base Qwen3.5-0.8B; lançamento11/11/2026 | SFT de ferramentas, destilação on-policy de três professores e duas fases de RL verificável, com recuperação de conhecimento/instruções após a especialização inicial. |
| [MiniCPM5-1B](https://huggingface.co/openbmb/MiniCPM5-1B) | 1.080.632.832; Transformer denso,24camadas | Base/mid-training, SFT de thinking e não-thinking, RL especializado e destilação dos professores para um só modelo. Publica conjuntos de dados e checkpoints intermediários. |
| [LFM2.5-1.2B-Thinking](https://huggingface.co/LiquidAI/LFM2.5-1.2B-Thinking) | 1.170.340.608;16camadas | Dez blocos convolucionais com gates e seis de atenção; receita nativa,28T tokens declarados e pós-treino. A eficiência depende também dos motores de inferência. |
| [Falcon-H1-Tiny-R-0.6B](https://huggingface.co/tiiuae/Falcon-H1-Tiny-R-0.6B) | 622.326.880; lançamento da família15/01/2026 | Pré-treino específico em rastros de raciocínio, orçamento declarado900B tokens e GRPO. Publica versões pré/pós-RL. |
| [LFM3-1.7B](https://huggingface.co/LiquidAI/LFM3-1.7B) | 1.728.801.536; referência maior, não par de tamanho idêntico |24camadas nativas:13convolucionais,5atenções locais,6globais. Declara22T tokens, SFT, RL misto, destilação de especialistas e RL em agentes. |

As revisões e configurações JSON estão em [official_metadata.json](official_metadata.json).
Data de criação do repositório e última edição dos arquivos não são datas de
lançamento. Contagens nominais, embeddings, visão e cabeças auxiliares precisam
ser distinguidas: o arquivo Qwen inclui20.452.864 parâmetros MTP que o nosso
executor original padrão e o híbrido não instanciam. O principal carrega
1.020.252.592 parâmetros, dos quais919.659.696 são de texto; a visão não é usada
no chat textual. Não se converte contagem de parâmetros em capacidade efetiva.

O card LFM2.5 declara contexto32.768, enquanto o JSON atual tem
max_position_embeddings128.000. O JSON sozinho não valida a qualidade no teto.
O LFM3 é explicitamente apresentado pelos autores como inadequado para coding
agentic e raciocínio complexo de muitos passos, apesar de ser maior que o nosso.
As limitações oficiais também fazem parte da comparação.

## O thinking do Liquid Sense já existe

No APK0.4, Normal é o padrão, sem trecho thinking explícito e com até2048tokens
de resposta. Profundo permite1024tokens de thinking+2048de resposta; Extenso,
2048+4096. A preferência é por opção de modelo. Não sabemos a escolha atual
no telefone do usuário. O loop32camadas/56visitas continua ativo nos três modos.
Esses perfis não treinam pesos nem aumentam o número de visitas neurais.

A distinção é entre ativar o formato de thinking e aprender a usar esse
orçamento para conferir, corrigir e terminar. O estudo024 registrou repetição
e ausência de resposta final no seu teste longo; isso é um diagnóstico pequeno,
não uma avaliação geral de todo thinking. O modo longo não foi promovido como
melhoria comprovada.

## Diferenças verificadas no principal

- A base original tem24camadas. Nosso grafo faz56visitas a32camadas físicas.
  Mais visitas custam computação e não provam ganho de raciocínio.
- A auditoria preservada do pai encontrou48matrizes de roteamento mHC com
  entrada zerada e fluxos iguais nas chamadas observadas. O loader também
  mantém oito camadas inseridas com projeções de saída neutras. Há estrutura
  adicional cuja capacidade condicional ainda precisa ser aprendida/validada.
- O ganho da segunda visita do pai é0,05 e o da primeira0,95. Esses coeficientes
  não medem porcentagem de pensamento ou utilidade de cada passagem.
- Já houve treino conjunto:025 treinou292tensores e48,34M valores durante
  três épocas/24atualizações, sobre16exemplos. As candidatas regrediram e foram
  rejeitadas. Não é correto dizer que nunca treinamos o loop; o checkpoint
  principal não incorporou esse treino rejeitado.
- Ferramentas reais já existem no app. A confiabilidade aprendida de escolher
  ferramentas, seus argumentos, tratar erros e concluir continua limitada. No
  estudo023, a edição de pesos também foi rejeitada; não foi incorporada ao APK.

Fontes locais preservadas: [loop025](../loop025/summary.json),
[roteadores](../reasoning/cycle2/router_static_audit.json),
[operadores nativos](../v2_adaptation/native_runtime.py),
[MTP preservado](../native010/unloaded_weights.json),
[APK024](../android_thinking024/README.md),
[ferramentas023](../tooluse023/REPORT.md).

## O que aproveitar dos trabalhos atuais

O caso mais diretamente comparável é o BotPsy: melhora um Qwen do mesmo tamanho
por pós-treino, sem depender da nossa expansão em loop. Os autores reportam
BFCLv4 de23,4para44,0 e IFEval de59,7para90,8 no seu próprio harness. No GPQA,
reportam3690contra11563tokens de raciocínio por acerto no subconjunto de questões
que todos os modelos acertam; a acurácia usa o conjunto completo. Isso não é
medição de tokens/segundo nem prova de velocidade no Snapdragon7sGen2.

A receita usa demonstrações, feedback por token de professores especializados
e recompensa verificável. O SFT inicial deles piorou conhecimento e instruções;
a destilação foi usada para recuperá-los. Código de treinamento e dados completos
do BotPsy não foram publicados junto dos pesos, portanto não há reprodução
integral pronta para executar.
[Método dos autores](https://huggingface.co/blog/qvac/botpsy).

O MiniCPM5 relata200B tokens de SFT de thinking profundo e200B de thinking
híbrido, seguidos por RL e destilação on-policy. Seus dados públicos podem
informar um currículo futuro; disponibilidade não dispensa curadoria, licença,
verificação e separação dos testes.
[Receita oficial](https://huggingface.co/openbmb/MiniCPM5-1B#training-recipe).

O Falcon0.6B relata melhora após GRPO e redução do comprimento médio de geração
de cerca de16kpara8ktokens. Seus resultados pass@1,pass@16 e votação majoritária
são métricas diferentes; as comparações com modelos grandes precisam respeitar
o orçamento de amostragem.
[Relatório dos autores](https://tiiuae-tiny-h1-blogpost.hf.space/).

O LFM3 mistura código de repositórios, matemática, dados de agentes, professores
especializados e recompensa com penalidade de comprimento. Os operadores
convolucionais/locais/globais são treinados na sua própria arquitetura.
[Treino oficial](https://huggingface.co/LiquidAI/LFM3-1.7B#training).

## Direção para a próxima experiência no principal

Hipótese: uma adaptação conservadora do bloco compartilhado, com ensino de
planejamento/verificação/correção, mistura de tarefas gerais e retenção do pai,
pode melhorar a conclusão correta sem simplesmente alongar respostas.

1. Treinar exemplos corretos e verificados, nos formatos thinking e não-thinking.
2. Adaptar conjuntamente lineares do loop e controladores mHC/temporais, preservando
   o tronco e as referências anteriores. Confirmar gradientes nas duas visitas.
3. Manter comportamento geral com exemplos gerais e regularização em dados de
   treino. A retenção nos exemplos não garante retenção universal; testar à parte.
4. Experimentar recompensa de execução em problemas de TREINO, com saídas reais
   do aluno e código em sandbox. Ausência de variação de recompensa deve ser
   registrada como ausência de sinal, sem inventar atualizações de RL.
5. Avaliar código novo, geral, término, repetição, tokens e tempo sob condições
   pareadas. Separar benefício do thinking, benefício causal do loop e qualidade
   geral. Preservar o pai se houver regressão.

Essa hipótese não é o pipeline industrial completo de BotPsy/MiniCPM/LFM3.
Não executamos os pares atuais neste hardware e não comparamos seus números
publicados aos nossos oito problemas próprios. Nenhuma superioridade entre
esses pares e o Liquid Sense foi medida nesta revisão.

O usuário autorizou a aplicação dessa direção após a revisão. O novo piloto de
treino será separado desta pesquisa documental, com protocolo, dados e fontes
congelados antes das atualizações. Não houve alteração de pesos nesta revisão.
