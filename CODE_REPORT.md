# liquid sense 0.8 b LOOP — programação e feedback de execução

Nenhuma nova edição passou. O híbrido anterior foi preservado.

## Teste final customizado novo

| Modelo | Tarefas com todos os testes | Testes individuais | Controles gerais | Tempo geração |
|---|---:|---:|---:|---:|
| original | 11/24 | 82/121 | 7/8 | 708.2s |
| baseline | 14/24 | 87/121 | 8/8 | 273.1s |

## Diagnóstico e limites

{
  "categories": {
    "passed": 5,
    "WrongReturnValue": 3
  },
  "informative_reward_variation": true,
  "repairs_attempted": 2,
  "repairs_passed": 0,
  "causal_status": "Activation correlations are hypotheses. Development interventions isolate weight edits and extra loop passes. They do not identify a unique internal cause.",
  "prior_limit": "Earlier 12-token tests did not evaluate full code generation. Old dense edits changed teacher-forced likelihood but did not improve development exact answers.",
  "model_received_reference_answers": false
}

As soluções esperadas não entraram nos prompts nem em perdas de tokens. A adaptação usou apenas ativações do código gerado e a fração de testes aprovados. As correlações de canais não identificam uma causa interna única. As intervenções em sinais opostos e em números de loops testam hipóteses.

Os checkpoints escrevem a matriz BF16 existente da última MLP; gates FP32 e configuração de cache ficam salvos. Passagens 2/3/4 executam 56/80/104 camadas, com parâmetros compartilhados e slots de cache independentes. Todas as variantes mantêm convoluções Liquid de sete posições com histórico aprendido e janelas locais. O corpo é Qwen; os roteadores mHC ainda não foram aprendidos e oito camadas inseridas têm saída neutra.

O teste é um piloto customizado de 24 funções Python, greedy pass@1 até 160 tokens, sem ferramentas ou feedback no modelo durante avaliação. Original e híbridos recebem o mesmo orçamento de resposta. Mais loops custam mais computação. Quatro/oito controles curtos e NLL de textos não demonstram qualidade geral excepcional. Não é HumanEval, MBPP ou LiveCodeBench completo e não permite chamar este modelo de melhor modelo pequeno em programação.

O ensaio de thinking é separado, só em treino, limitado a 160 tokens e não escolhe pesos. As referências, hipóteses e protocolo estão em code_rsi/PROTOCOL.md.

Estado: concluído e parado; checkpoints e resultados preservados no Git.
