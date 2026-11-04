# Edição localizada para programação, sem soluções prontas

Pedido: usar análise de programação para direcionar alterações dos pesos.
Este piloto procura grupos candidatos associados às tarefas de código. Não
presume um módulo independente de programação nem um mapa conhecido entre
um erro de algoritmo e seus pesos responsáveis.

## Continuidade

Não interromper ou mudar a busca de 100 rodadas. O workflow novo espera que ela
termine com sucesso. Importar somente sua seleção congelada e o checkpoint
escolhido, verificando o hash. Não consultar seus resultados finais para selecionar
pesos. Se a busca precisar de recuperação, parar antes de importar pesos incertos.
O pai pode continuar sendo o híbrido original se nenhuma edição tiver sido promovida.

## Erros observados e limites do diagnóstico

A auditoria manual em `error_audit.json` explica cinco falhas de lógica e um caso
de eco de prompt. Ela não contém uma implementação corrigida e não é enviada ao
modelo. Por exemplo, repetir uma soma da lista inteira não implementa somas de
prefixos, e pular o tamanho inteiro da substring impede contar sobreposições.
Essas observações identificam defeitos no programa gerado, não as causas neurais.

A habilidade do assistente em escrever código não fornece valores corretos de
pesos de uma rede. A aplicação aqui é construir testes e intervenções verificáveis.

## Identificação de candidatos e intervenções

1. Em oito enunciados de programação sem soluções e oito prompts de prosa,
   capturar a ativação absoluta na entrada da projeção de saída MLP, no último
   token do prompt. Para camadas repetidas, usar o valor da última visita.
2. Medir quatro camadas físicas: 5, 13, 25 e 31. Elas cobrem profundidades diferentes;
   sua escolha não equivale a identificar previamente onde fica a programação.
3. Para cada camada, comparar médias código/prosa por log-razão e selecionar
   64 canais entre os suficientemente ativos. Selecionar outro grupo de 64 canais,
   disjunto e aproximadamente pareado em magnitude de atividade, com semente fixa.
4. Comparar 16 intervenções pré-registradas: zerar canais-alvo, zerar controle,
   multiplicar os canais-alvo por 1,15 ou por 0,85, em cada uma das quatro camadas.
5. Cada patch salva as colunas BF16 já alteradas. Ao carregar, `index_copy_` escreve
   na matriz existente; não há adaptador ou hook de steering durante a avaliação.

O contraste entre código e prosa tem diferenças de tamanho, assunto e formato.
Ele produz hipóteses de seletividade de tarefa, não prova especialização em lógica.
Ablatação contra controle mede influência na bateria observada. Não comprova uma
função exclusiva, nem que o efeito generalize a outras tarefas ou modelos.

## Seleção e preservação

Desenvolvimento: 16 funções já observadas, identificadas explicitamente como
currículo de pesquisa. Recompensa é execução do código em sandbox isolado.
Somente amplificação/atenuação podem ser promovidas; ablações são diagnósticos.
Exigir mais tarefas com todos os testes aprovados, nenhum teste previamente
correto perdido, nenhum controle geral perdido e NLL genérica sem aumento
(tolerância numérica de 1e-6). As duas melhores elegíveis seguem à validação.

Validação: oito especificações novas, sem reutilizar os testes dos experimentos
anteriores. Confirmar as mesmas regras antes de congelar. Teste final: outras oito
funções novas, quatro controles gerais e comparação com o Qwen original e o pai.
Não usar teste final para escolher pesos. Sem ganho confirmado, preservar o pai.
Oito funções são um piloto pequeno, não evidência de melhor modelo pequeno.

Apenas enunciados entram nos prompts; referências geram oráculos no construtor
de dados. Nenhuma solução pronta, resposta esperada ou perda de tokens-alvo é usada
na adaptação. Sem autograd/backpropagation. Generalidade de resposta é protegida
apenas pelos controles limitados e NLL de 12 textos; não há promessa de qualidade
excepcional geral.

## Arquitetura e execução

Preservar mHC, número de passagens e operadores Liquid do pai congelado.
Nenhuma intervenção desliga essas famílias arquiteturais. Desativar 64 canais
MLP para diagnóstico não remove o loop nem a convolução Liquid. O modelo continua
uma adaptação compatível de dimensões Qwen, não os modelos SenseNova/LFM3 completos.
A base é nominalmente 0,8B; o híbrido é aproximadamente 1,02B.

CPU pública padrão, quatro threads, até quatro avaliações paralelas. Mesmo greedy,
pass@1, até 160 tokens por função, sem feedback durante avaliação. Mais loops no
pai significam mais computação. Guardar hashes, patches e decisões no Git, sem
force push. Artefatos duram três dias; commits preservam os resultados. Ao fim, parar.
Não alterar os conjuntos após observar as respostas.

## Referências primárias e escopo

- Yin et al., [Neuron-Guided Interpretation of Code LLMs](https://arxiv.org/abs/2512.19980):
  analisa neurônios/camadas em modelos de código diferentes deste híbrido.
- Kargaran et al., [How Programming Concepts and Neurons Are Shared](https://aclanthology.org/2025.findings-acl.1379/):
  mostra estruturas compartilhadas entre linguagens e limites da identificação
  de neurônios exclusivos. Não fornece o mapa de pesos do nosso modelo.
- Gu et al., [Neuron Patching](https://arxiv.org/abs/2312.05356): motivação para
  reparos localizados. Usa relações com saídas desejadas; não alegamos reproduzir
  seu método ou seus resultados sob a restrição atual de não fornecer soluções.

Este experimento foi definido pelo assistente e não é autoaperfeiçoamento autônomo.
