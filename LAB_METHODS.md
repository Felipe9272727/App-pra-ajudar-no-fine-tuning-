# Referências públicas e mudanças deste piloto

Modelo: **liquid sense 0.8 b LOOP**. O nome nominal vem da base Qwen 0,8B;
o híbrido ampliado carrega aproximadamente 1,02B parâmetros.

## O que os laboratórios descrevem publicamente

**OpenAI.** A publicação de setembro de 2026 descreve agentes ajudando a
programar e executar experimentos, com pessoas escolhendo prioridades e
avaliando os resultados. Ela apresenta progresso em automação da pesquisa;
não demonstra que RSI geral já esteja resolvido. A página da equipe RSI
também cita avaliações, dados sintéticos, ambientes de RL e treinamento de
capacidades que faltam. Não temos acesso a seus procedimentos internos.

https://openai.com/index/research-acceleration-view-inside-openai/
https://openai.com/careers/research-engineer-research-scientist-ai-systems-engineer-rsi-san-francisco/

**Google DeepMind — AlphaEvolve.** Modelos propõem programas, avaliadores
automáticos medem resultados e uma base de candidatas conserva ideias
promissoras para novas iterações. Isso melhora algoritmos e infraestrutura;
não equivale a simplesmente editar arbitrariamente todos os pesos do modelo.

https://deepmind.google/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/

**Anthropic — Automated Weak-to-Strong Researcher.** Agentes formulam
hipóteses, executam experimentos e mantêm registros. A publicação enfatiza a
qualidade das avaliações, testes fora da distribuição e falhas causadas por
atalhos ou sobreajuste da métrica. Os resultados usam treinamento e recursos
muito maiores que os deste experimento local.

https://alignment.anthropic.com/2026/automated-w2s-researcher/

## O que estamos implementando

1. Hipóteses diferentes, uma população de candidatas e arquivo de resultados,
   em vez de repetir somente ajustes dos mesmos três controles.
2. Currículo sintético com respostas verificadas por código, separado em
   treino, desenvolvimento, validação e teste final.
3. Ajuste fechado de uma matriz MLP existente usando erros de tokens e âncoras
   de preservação. Os novos valores são escritos diretamente nos pesos;
   não há backpropagation ou calculadora durante a inferência.
4. Avaliação em etapas: probabilidade e regressões baratas primeiro; geração
   de respostas depois; teste final novo usado uma vez após a seleção.
5. Loop/mHC SenseNova e os componentes inspirados em LFM3 permanecem ativos
   em todas as candidatas. As melhorias devem funcionar dentro desse híbrido.

O controlador é o assistente desta sessão. Essas escolhas são inspiradas em
princípios públicos de pesquisa automatizada; não são uma reprodução dos
pipelines internos desses laboratórios nem prova de RSI autônomo geral.
