# Liquid Sense × Gemma 047

O 046 carrega **1.432.249.520 parâmetros**, incluindo **510.000.128 da Gemma**. Os dois ajustes iniciais da projeção 046 foram rejeitados na triagem. A variante 047 carrega **1.432.296.670 parâmetros**, com **47.150** adicionados à saída. Os pesos e a arquitetura híbrida do 046 foram preservados.

O 047 foi obtido por treino supervisionado continuado de uma projeção esparsa de saída e um classificador de intenção treinado nas ativações. A projeção aprende pesos para 45 saídas do vocabulário, e o classificador decide pela ativação interna do modelo no fim da pergunta. As gerações usam a mesma mensagem de sistema genérica do 046. As respostas de identidade entram apenas nas posições supervisionadas de treino. O checkpoint e os testes foram congelados antes da avaliação final.

| Avaliação final em Torch CPU | 046 | 047 |
| --- | ---: | ---: |
| Identidade correta | 0/6 | 4/6 |
| Atribuições falsas na identidade | 3/6 | 1/6 |
| Fatos sobre Gemma e Gemini | 2/2 | 2/2 |
| Controles de linguagem | 2/2 | 2/2 |
| Casos de código | 10/10 | 10/10 |

O 047 acertou as quatro perguntas de identidade em português, inclusive “Você é do Google?”. As duas perguntas em inglês falharam. Em uma delas, a resposta ainda atribuiu a criação à Alibaba. A variante passou o protocolo como candidata experimental. [Saídas completas](reports/final.json)

O notebook oferece CUDA para T4 e reutiliza o modelo em memória entre perguntas. No caminho CUDA, as projeções usam pesos em FP16 e saída FP32 antes dos arredondamentos. A preparação verifica a disponibilidade da GPU e executa uma multiplicação FP16 curta antes de baixar os pesos. O motor em Torch e o notebook foram testados em CPU com o checkpoint real. O tempo e a paridade de geração em uma T4 real ficam pendentes. [NVIDIA T4](https://www.nvidia.com/en-us/data-center/tesla-t4/) · [Operação CUDA no PyTorch](https://docs.pytorch.org/docs/2.8/generated/torch.mm.html)

Os termos dos pesos derivados da Gemma acompanham a distribuição em `fusion043/licenses/`. [Execução da referência Torch](https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/actions/runs/45709850433)
