# Benchmarks usados pela Liquid AI — piloto do Liquid Sense

Fontes primárias consultadas em 2026-11-05:
- [LFM3-1.7B, ficha oficial](https://huggingface.co/LiquidAI/LFM3-1.7B): LiveCodeBench v6 e IFEval, entre outras avaliações.
- [LFM2.5-1.2B-Thinking, anúncio oficial](https://www.liquid.ai/blog/lfm2-5-1-2b-thinking-on-device-reasoning-under-1gb): GSM8K, entre outras avaliações de raciocínio.
- [SenseNova-Loop, ficha oficial](https://huggingface.co/sensenova/SenseNova-Loop-9B-Preview): referência da arquitetura compartilhada e mHC, sem atribuir suas métricas ao nosso híbrido.

O piloto usa oito problemas de programação (até 16 casos privados cada),
16 questões de matemática e 12 instruções verificáveis. As fontes, IDs,
gabaritos e regras estão fixados em sources.json, selected_ids.json,
oracles.json e PROTOCOL.md. O código oficial IFEval foi preservado sem alterações.
Exemplos de entrada/saída dos enunciados de programação foram removidos;
nenhuma solução de referência ou resposta do avaliador entra no modelo.

São subconjuntos com orçamento e restrições locais. Não comparar estas
porcentagens diretamente com os resultados completos publicados pela Liquid AI,
que usa outra amostragem, contexto, infraestrutura e orçamentos de inferência.
Os híbridos usam mais computação interna que o Qwen original; pai/candidata
mantêm o mesmo protocolo de entradas e saída. Identidade e textos de marca
ficam fora das entradas dos benchmarks.

Para preparar uma cópia fria, instale o runtime principal do projeto e
requirements-eval.txt, depois execute download_sources.py. Os pesos upstream
continuam fixados pelos arquivos da raiz. Não reconstrua os IDs selecionados
após observar resultados. Para uma reprodução independente sem sobrescrever
saídas anteriores, use, da raiz do projeto:

```
python benchmarks/reasoning_20261105/evaluate.py original --output-dir /workspace/reproduction
python benchmarks/reasoning_20261105/evaluate.py liquid --output-dir /workspace/reproduction
```

Cada resposta é salva antes da próxima. Modelos, kernels e pesos devem ser
comparados no mesmo executor; pequenas diferenças numéricas entre máquinas
podem mudar a geração gulosa. O prompt de identidade só aparece no teste
separado reasoning/identity_probe.json.
