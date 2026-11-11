# Dossiê de pesquisa para Codex — Liquid Sense 0.8B LOOP
**Tema:** como aproveitar (1) a metodologia de dados validados da CCORE e (2) a decodificação especulativa DSpine da Tencent.  
**Preparado em:** 2026-11-08  
**Finalidade:** documento de transferência de contexto; **não é um relatório de experimentos executados no repositório do usuário**.

> **Regra central:** nosso primeiro objetivo é melhorar **capacidade de programação**; o segundo é reduzir **latência/custo de inferência**. São dois problemas diferentes. Nenhum benchmark externo comprova automaticamente ganhos no Liquid Sense.

---

## 0. Contexto do projeto a recuperar primeiro

- Nome de trabalho: **Liquid Sense 0.8B LOOP**.
- Base mencionada na sessão anterior: **Qwen 3.5 0.8B** (confirmar o ID exato do checkpoint e a arquitetura antes de modificar quaisquer arquivos).
- Direção arquitetural experimental: ideias **SenseNova Loop**, **Liquid AI** e roteamento/expansão; confirmar no código o que realmente foi implementado e o que ainda é proposta.
- Meta: desenvolver um modelo pequeno, especializado em **programação**, sem prejudicar significativamente suas capacidades gerais.
- Abordagem anterior: edição direta dos pesos, guiada por hipóteses e ativações, com seleção de checkpoints mediante testes.
- Resumo histórico fornecido pela conversa anterior, **ainda não verificado em logs/repositório**:
  - 31 rodadas automáticas de RSI; nenhuma melhoria automática aceita.
  - Um experimento **V3 NCM** foi descartado.
  - Na **segunda edição guiada por ativações**, houve melhora local relatada: tarefas 11→12, casos 69→72, 4/4 controles preservados.
  - A validação em **problemas inéditos** e a confirmação do **checkpoint efetivamente salvo** ficaram pendentes.
- **Antes de qualquer experimento novo:** localizar repositório, branch, commits, pesos, scripts, relatórios e checkpoint; não tratar esses números de conversa como resultados auditados.

### Ordem de prioridade
1. Recuperar e validar o último checkpoint promissor (sem contaminação de benchmarks).
2. Adaptar a lição sobre **dados de qualidade e validação automática** da CCORE.
3. Avaliar, **se houver justificativa de hardware e throughput**, uma trilha separada de aceleração DSpine.

---

## 1. Pesquisa A — CCORE Qwen3.5-4B-GLB-3D-Coder

### Fonte principal

- Modelo: https://huggingface.co/ccore/Qwen3.5-4B-GLB-3D-Coder
- Dataset GLB: https://huggingface.co/datasets/ccore/ThreeJS-3D-GLB-Assets
- Modelo anterior de cenas Three.js: https://huggingface.co/ccore/Qwen3.5-4B-3D-Coder
- Dataset anterior: https://huggingface.co/datasets/ccore/ThreeJS-3D-Scenes
- Relatório técnico do **modelo anterior**, não necessariamente do GLB mais novo: https://huggingface.co/ccore/Qwen3.5-4B-3D-Coder/blob/main/Qwen3.5-4B-3D-Coder_Technical_Report.pdf

### O que a fonte oficial confirma

- Projeto independente **CCORE**, baseado em **Qwen/Qwen3.5-4B**, lançado em **5/11/2026**.
- Modelo especializado em escrever **HTML/JavaScript com Three.js**, apresentando prévia e botão para exportar um **GLB** reutilizável em engines como Godot.
- Pesos distribuídos em **Safetensors** e quantizações **GGUF** (Q4_K_M, Q8_0).
- Licença do modelo: **Apache-2.0**; verificar licenças de cada dataset antes de reutilizar ou redistribuir.
- Dataset GLB liberado com **3.918 exemplos** em **40 domínios**; segundo a descrição do mantenedor, os exemplos foram **renderizados/testados** e seus GLBs de exportação **validados**.
- Os exemplos públicos incluem dados de prompt, respostas em código e rastros de raciocínio conforme as descrições de lançamento; conferir colunas e splits reais ao baixar.
- **Importante:** a existência de pesos, dataset e relatório técnico de modelo relacionado **não prova que todo o pipeline executável de geração, filtragem e treinamento do GLB foi publicado**. Codex deve verificar isso; não apresentar scripts inexistentes como oficiais.

### Lição transferível para o Liquid Sense

A contribuição mais promissora **não é 3D em si**, mas **dados especializados com validação efetiva do artefato gerado**.

Padrão a adaptar:

1. Gerar tarefas de programação variadas (sintaxe, algoritmos, depuração, testes, refatoração, pequenos projetos).
2. Solicitar soluções candidatas com uma IA professora, registrando **origem, versões e custo**.
3. Executar o código em sandbox com limites de tempo/memória, sem acesso a segredos nem rede arbitrária.
4. Exigir testes unitários, casos adversariais e, quando apropriado, checks de segurança, lint e desempenho.
5. Rejeitar exemplos que não passam; registrar por que foram rejeitados.
6. Separar splits **treino / validação / teste final isolado**, idealmente com divisão por problema/projeto, não só por linha.
7. Comparar modelo original, checkpoint anterior e novos candidatos com os **mesmos prompts e configurações de inferência**.
8. No nosso experimento, usar os dados para investigar **ativações e hipóteses de alteração de pesos**; SFT/LoRA podem ser uma **trilha de comparação**, não uma substituição silenciosa da linha de pesquisa direta.

### Proposta inicial de experimento (hipótese nossa, não resultado da CCORE)

Criar um **piloto de 200 tarefas** diversificadas, com gabaritos executáveis:
- 120 para investigação/desenvolvimento;
- 40 para validação e seleção;
- 40 de **teste cego**, nunca usado na escolha de candidatos.

Não reutilizar tarefas idênticas, soluções, bibliotecas ou templates entre splits quando isso causar vazamento. Métricas: `pass@1`, taxa de execução, erros por categoria, regressões em linguagem/raciocínio, custo e latência. Relatar incerteza da amostra e seeds quando relevante.

**Critério de promoção:** ganho consistente sobre baseline **em teste inédito**, sem regressões relevantes, repetível com configurações documentadas. Se não passar, não promover.

---

## 2. Pesquisa B — Tencent DSpine / Qwen3.8-27B-DSpine-b16

### Fontes primárias e vídeo apresentado

- Vídeo do Codedigipt (08/11/2026): https://youtu.be/3lgQyTOHtIw
- Cartão do checkpoint: https://huggingface.co/tencent/Qwen3.8-27B-DSpine-b16
- Código de inferência: https://github.com/Tencent/DSpine
- Framework de treinamento: https://github.com/sgl-project/SpecForge
- Artigo: https://arxiv.org/abs/2609.36173

### O que é

**DSpine** é uma abordagem de **decodificação especulativa**. Um modelo auxiliar (*drafter*) produz candidatos de tokens futuros em paralelo. O modelo-alvo os **verifica**; a aceitação reduz os passos sequenciais necessários. O mecanismo descrito pelos autores usa **Adjacent Causal Injection**, em que camadas do drafter propagam informações previstas de posições anteriores para posições adjacentes.

**Principal objetivo: aumentar velocidade/throughput, NÃO necessariamente aumentar a competência do modelo.** Com a verificação especulativa implementada corretamente, deve-se preservar a distribuição de saída do modelo-alvo dentro das condições do algoritmo; validar a equivalência do resultado para o sistema específico.

### Configuração e números publicados

No cartão do **Qwen3.8-27B-DSpine-b16**:
- Drafter de **aproximadamente 2B parâmetros** e **cinco camadas**; **bloco 16**; janela deslizante de **8.192 tokens**.
- Avaliação reportada em **SGLang 0.5.22, BF16, FlashAttention 3, concorrência 8**, com condições adicionais descritas no cartão.
- *Throughput* end-to-end em workloads de agentes, esforço `low`, vs geração autorregressiva:
  - **WorkBuddy Code:** **2,71×**
  - **WorkBuddy Web:** **3,13×**
  - **WorkBuddy Office:** **3,84×**
  - **SWE-bench Pro:** **2,95×**
  - **τ²-bench:** **3,20×**
- **Esses valores são relatados pelos autores**. Não são um ganho universal de 4×, nem equivalem à aceleração de uma única conversa ou do nosso hardware.

No README de `Tencent/DSpine`, consta:
- código de inferência e pesos disponibilizados;
- treinamento DSpine disponibilizado no **SpecForge** em outubro de 2026;
- implementação e versões suportadas podem variar por commit; consultar a versão atual antes de tentar executar.

### Limitações para o Liquid Sense 0.8B

- **Não é possível simplesmente acoplar** o drafter feito para Qwen3.8-27B ao nosso 0.8B.
- Um drafter de ~2B pode ser mais pesado que o próprio modelo principal de 0.8B: a aceleração pode ser **nula ou negativa**.
- Compatibilidade de tokenizer, embeddings, arquitetura, hidden states, cache e verificação precisa ser estudada.
- Há overhead de computação/memória; resultados CUDA/servidor não podem ser extrapolados para celular/CPU.
- Prioridade inicial: **medir tokens/s, TTFT, latência total, RAM/VRAM, consumo e taxa de aceitação** sem aceleração; fazer um orçamento quantitativo antes de implementar.

### Experimento sugerido (trilha independente)

1. Analisar requisitos do `Tencent/DSpine` e `SpecForge` sem modificar nosso modelo principal.
2. Medir baseline de geração do Liquid Sense e do Qwen base nas cargas reais de código.
3. Estimar custo de criar e treinar um drafter **substancialmente menor** para esse target.
4. Antes de DSpine, testar se alternativas simples de inferência (cache, quantização verificada, batching adequado e/ou uma forma mais leve de speculative decoding) já resolvem o problema.
5. Apenas se viável, criar **branch experimental** para drafter compatível; comparar desempenho **e equivalência de saída**, sem alterar checkpoint de qualidade.
6. Registrar claramente se a experiência ficou em análise, protótipo ou benchmark executado.

---

## 3. Como as pesquisas se combinam — sem misturar objetivos

| Eixo | Inspiração externa | Pergunta no nosso projeto | Métrica primária |
|---|---|---|---|
| **Capacidade** | CCORE: dataset específico e código verificado | O 0.8B resolve mais programas novos corretamente? | `pass@1`, regressões |
| **Edição de pesos** | Nosso experimento de ativações | Alterações guiadas melhoram a generalização? | ganho cego vs baseline |
| **Velocidade** | DSpine: previsão paralela e verificação | O 0.8B gera mais rápido no nosso runtime? | latência, tokens/s, memória |
| **Reprodutibilidade** | Checkpoints e validações | Conseguimos demonstrar a melhoria com logs completos? | scripts, seeds, hashes |

**Não presumir** que edição de pesos inspirada em CCORE reproduza o SFT da CCORE. **Não presumir** que DSpine aumenta raciocínio ou precisão. As duas são linhas complementares de P&D.

---

## 4. Tarefas para Codex — retomada segura

### Etapa A — auditoria e recuperação
- [ ] Encontrar repositório/branch corretos e `README`, configurações, modelo de base real, checkpoints e logs.
- [ ] Verificar persistência da **segunda edição guiada por ativações**; anotar caminho, commit e SHA256, se existir.
- [ ] Reproduzir os testes locais anteriores; marcar resultados não reproduzíveis como **não confirmados**.
- [ ] Executar tarefas **inéditas** e relatório de comparação.

### Etapa B — piloto inspirado na CCORE
- [ ] Inspecionar *schema* real e licenças dos datasets da CCORE e procurar scripts de treinamento efetivamente publicados.
- [ ] Criar especificação para dataset de programação com validação executável e sandbox.
- [ ] Implementar gerador/verificador de 200 tarefas com splits isolados e relatórios.
- [ ] Comparar checkpoint com baseline antes e depois de quaisquer novas edições; preservar pesos originais.
- [ ] Registrar ganho, regressão e possível vazamento de benchmarks.

### Etapa C — DSpine, em paralelo e opcional
- [ ] Ler paper e implementação atual, identificar dependências para target de 0.8B.
- [ ] Medir baseline real de inferência no hardware disponível.
- [ ] Fazer análise de viabilidade RAM/VRAM/CPU/GPU e custo de treinamento de drafter.
- [ ] Se a viabilidade não fechar, documentar **não recomendado agora**.
- [ ] Se fechar, prototipar em branch separada, sem mexer no checkpoint validado.

### Entregáveis desejados
1. `STATUS_RECUPERACAO.md`: o que realmente foi encontrado e o que falta.
2. `EXPERIMENTOS_CAPACIDADE.md`: benchmarks, protocolos, resultados e regressões.
3. `PLANO_DSPINE.md`: requisitos, compatibilidade e decisão de viabilidade.
4. Scripts e logs reproduzíveis, com testes.
5. Checklist de promoção de checkpoint: somente resultados **confirmados em testes cegos**.

**Evitar:** apagar experimentos antigos; inventar resultados ou checkpoints; tratar conteúdo de vídeo como validação independente; lançar 100 novos loops sem validar a edição anterior; baixar pesos gigantes antes de confirmar necessidade e recursos.

---

## 5. Prompt curto para colar no Codex

> Retome o projeto Liquid Sense 0.8B LOOP usando este documento como contexto de pesquisa. PRIMEIRO audite repositório, branches, logs e checkpoints e recupere a segunda edição guiada por ativações, cuja validação em tarefas inéditas está pendente. NÃO suponha que o checkpoint foi salvo. Depois planeje um piloto de dados de programação executáveis inspirado na metodologia de validação da CCORE, mantendo a edição direta de pesos como trilha experimental, e avalie separadamente a viabilidade de DSpine para aceleração do nosso 0.8B. Não confunda ganho de inteligência com ganho de velocidade; não use resultados externos como se fossem nossos. Implemente o que for possível, registre comparações, preserve os checkpoints e descreva precisamente o que foi realizado, o que falhou e o que falta.

---

## 6. Referências verificadas (8/11/2026)

1. CCORE GLB model card: https://huggingface.co/ccore/Qwen3.5-4B-GLB-3D-Coder
2. CCORE dataset GLB: https://huggingface.co/datasets/ccore/ThreeJS-3D-GLB-Assets
3. CCORE modelo anterior: https://huggingface.co/ccore/Qwen3.5-4B-3D-Coder
4. CCORE dataset anterior: https://huggingface.co/datasets/ccore/ThreeJS-3D-Scenes
5. Tencent DSpine model card: https://huggingface.co/tencent/Qwen3.8-27B-DSpine-b16
6. Tencent/DSpine: https://github.com/Tencent/DSpine
7. SGLang/SpecForge: https://github.com/sgl-project/SpecForge
8. Artigo DSpine: https://arxiv.org/abs/2609.36173
9. Vídeo que motivou a pesquisa: https://youtu.be/3lgQyTOHtIw

**Observação sobre fonte:** o vídeo foi usado como ponto de partida; os detalhes técnicos e números acima foram contrastados com a documentação dos criadores. A disponibilização de **todo** o pipeline GLB de treinamento não foi confirmada — conferir antes de afirmar.
