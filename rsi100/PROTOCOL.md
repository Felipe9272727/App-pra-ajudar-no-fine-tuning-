# Cem rodadas de busca em pesos, sem gradientes

Pedido interpretado: 100 tentativas sequenciais de melhorar o checkpoint por
recompensa e descartar pioras, semelhante à seleção por recompensa em RL.
Não são 100 repetições internas do decoder. As passagens internas continuam
limitadas a 2/3/4, mantendo mHC e os componentes inspirados em Liquid ativos.
Isso é adaptação/busca em parâmetros com feedback, sem backpropagation,
SGD ou respostas-alvo nos prompts. Não demonstra RSI autônomo nem liderança.

Pai fixado: `155a8f54102d674db32431264cdc1f76aeaa56e9`. Nenhuma das quatro
edições anteriores passou pelo desenvolvimento. O início é o híbrido ativo
anterior, não uma candidata rejeitada. Os arquivos anteriores são históricos.

## Recompensa e reversão

- Currículo de busca: oito tarefas de adaptação e oito antigas de desenvolvimento,
  já observadas, reutilizadas explicitamente para otimizar. Não são um teste final.
- Em cada rodada, gerar uma perturbação a partir do melhor checkpoint atual.
- Testar primeiro até duas tarefas ainda com falhas; descartar empates ou pioras.
- Uma candidata promissora precisa ser reavaliada nas 16 tarefas, nos quatro
  controles gerais e nos 12 textos genéricos de preservação.
- Aceitar somente se nenhum caso antes correto for perdido, algum caso novo
  passar, nenhum controle correto cair e a NLL genérica não aumentar além
  da tolerância numérica de 1e-6. Não trocar um acerto antigo por dois novos.
- Após cada decisão, restaurar o melhor checkpoint. Candidatas rejeitadas só
  existem em memória; não entram nos pesos salvos. Preservar logs, seed e motivo.
- Salvar a base, o melhor atual e cada checkpoint aceito. Nunca apagar a base
  ou o histórico de auditoria e nunca fazer force push.

Cem decisões sobre esse mesmo currículo podem causar sobreajuste. Uma pontuação
melhor de busca não demonstra generalização. O checkpoint é recalibrado a cada
novo runner; se os acertos mudarem só pela troca de máquina, a pesquisa para.
As NLLs de comparação de cada rodada são medidas no mesmo runner.

## Propostas fixadas antes dos resultados

Repetir cinco famílias em ordem, com seeds determinísticas:

1. Multiplicação direta de colunas da última MLP, guiada por correlações de
   ativações anteriores mais exploração aleatória.
2. Escrita de um delta de posto um na matriz densa existente, sem adaptador.
3. Rescalamento de até 128 colunas da MLP.
4. Perturbação direta dos coeficientes históricos das convoluções Liquid.
5. Alterações pequenas de biases dos roteadores mHC e dos gates de visitas,
   com 2/3/4 passagens compartilhadas e todas as visitas ativas.

Norma total do desvio da MLP limitada a 8% da base, histórico Liquid a 20%.
Biases mHC limitados a +/-0,15 da base. Ganho total das visitas posteriores
entre 0,01 e 0,20, dividido entre elas. Arredondamento BF16 pode alterar levemente
os limites. Os pesos contextuais dos roteadores não são aprendidos; oito camadas
inseridas permanecem neutras. É uma adaptação compatível sobre Qwen, não os
modelos SenseNova/Liquid completos. Base nominal 0,8B, híbrido cerca de 1,02B.

Não há imitação de solução pronta: somente o enunciado entra na geração.
Oráculos verificam o código isoladamente e devolvem recompensas. Não enviar
saídas esperadas, implementação de referência ou perda de tokens-alvo ao modelo.

## Validação e comparação final

Depois das 100 rodadas, comparar melhor de busca versus base em oito funções
novas de validação, sem voltar à busca. Exigir mais tarefas completamente
corretas, nenhum caso antigo de validação perdido, nenhum controle perdido e
NLL genérica sem piora. Se falhar, reverter a escolha final à base.
Guardar o melhor de busca como experimento auditável, sem chamá-lo de promovido.
Congelar a escolha antes de abrir as 16 tarefas finais novas e oito controles.
O Qwen original e a base híbrida sempre participam do teste final. O melhor de
busca participa se tiver passado na validação. O teste não escolhe pesos.

Mesmo greedy pass@1 e até 160 tokens por função; quatro threads CPU.
São funções curtas sem imports, reflexão ou I/O, executadas no sandbox isolado
já validado. Isso não substitui HumanEval/MBPP/LiveCodeBench completos nem prova
qualidade de resposta geral excepcional.

## Execução, duração e persistência

Aguardar o fluxo anterior terminar para não ultrapassar quatro máquinas de
avaliação. Usar apenas CPUs padrão públicas. Uma máquina por vez faz a busca;
dez jobs sequenciais completam dez rodadas cada, com commit após cada decisão.
O teste final usa no máximo quatro jobs em paralelo. Não habilitar cobrança.
Um orçamento de 100 propostas não garante que alguma será aceita. A busca é
finita e para após o relatório final. Timeouts/erros de infraestrutura param
preservando decisões já salvas, sem declarar rodadas não realizadas como feitas.

As primeiras verificações são testes técnicos em tensores pequenos e no runtime
minúsculo; não contam como as 100 tentativas nem como resultados de inteligência.
Artefatos duram três dias, enquanto commits guardam o progresso. Logs não são
pesos rejeitados. Não alterar fonte durante o fluxo; o guard bloqueia mudanças
concorrentes. Para retomar, verificar commits e estado antes de repetir trabalho.

## Operational recovery 001

Resume after saved round 30. No data, mutation or scoring changes. Per-generation limit 180s, execution 60s, model loading 300s, anchor scoring 240s, publication 180s; total chunk 3600s. External watchdog terminates stalled process groups and exports diagnostics. Timeout is an infrastructure failure, never a rejected candidate. Git commands have a 60s deadline; uncertain pushes are verified without blind retry. Previous checkpoint ownership is explicitly handed off in recovery_001.json; all saved rounds and weights remain intact.
