# Programação: edição de pesos com feedback, sem soluções nos prompts

Objetivo do usuário: melhorar programação, preservar o híbrido SenseNova +
Liquid e testar mais loops. Este é um piloto limitado, sem promessa de ser
o melhor modelo pequeno ou de atingir qualidade geral excepcional.

O pai é `cd8cb5826ac17100cb0960d428389a3d714d5417`. A V3 segue arquivada.
As edições rejeitadas do ciclo 2 não são incorporadas à base ativa.
O Qwen original usa os pesos canônicos fixados em `manifest.json`.
A base é nominalmente 0,8B; o híbrido ampliado tem aproximadamente 1,02B.
Os módulos são compatíveis e inspirados nessas arquiteturas, não os modelos
SenseNova/LFM3 completos. Os roteadores mHC ainda não foram aprendidos;
oito camadas inseridas continuam com saída neutra.

## Diagnóstico sem fornecer uma solução pronta

Os testes anteriores tinham no máximo 12 tokens e não mediam geração completa
de código. As ativações temporárias completas não foram salvas naquele ciclo.
Os checkpoints, saídas e métricas foram preservados. Este piloto coleta de novo:

- Ativação absoluta média dos canais da entrada da última projeção MLP.
- Deriva de norma e cosseno entre visitas, no prefill de três camadas.
- Código realmente gerado, sintaxe, contrato, exceções, timeout e testes aprovados.
- Até duas tentativas de reparo, com código próprio e mensagem de erro/fração
  aprovada. Não enviar valores esperados, solução de referência ou tokens-alvo.

As soluções de referência só constroem oráculos em `make_data.py`. Nunca entram
nos prompts ou no ajuste por tokens. Isto é adaptação por recompensa verificável,
não ausência de supervisão: os testes são sinais de desempenho.
As correlações entre canais e recompensa não estabelecem uma causa interna única.

## Alteração literal dos pesos e dos loops

Calcular correlação entre ativações e fração de testes aprovados. Centralizar,
normalizar RMS e limitar a direção a [-2,2]. Multiplicar diretamente cada coluna
da matriz existente `layers.31.mlp.down_proj.weight` por 1 +/- 0,03 * direção.
Salvar a matriz BF16 densa, sem adaptador adicional. Sem autograd/backward.
Se todas as recompensas forem constantes, usar uma direção aleatória fixa,
registrada explicitamente como exploração, sem inventar sinal aprendido.

Quatro candidatas fixadas antes dos resultados:

| Candidata | Matriz | Passagens | Execuções de camadas |
|---|---|---:|---:|
| edit_plus | sinal positivo | 2 | 56 |
| edit_minus | sinal negativo | 2 | 56 |
| edit_plus_loop3 | mesma matriz positiva | 3 | 80 |
| edit_plus_loop4 | mesma matriz positiva | 4 | 104 |

A comparação de sinais testa a direção da edição. A comparação com a mesma matriz
positiva em mais passagens isola o efeito de profundidade nessa matriz, não uma
teoria geral de raciocínio. Não são quatro novos modelos já comprovadamente melhores.
O bloco [4,28) compartilha parâmetros, com slots de cache de cada visita separados.
O total de ganho residual fica 1: primeira visita 0,95; 0,05 dividido entre as
visitas seguintes, todas ativas. Os gates FP32 e a configuração ficam no checkpoint.
Todos os componentes Liquid permanecem ativos: convoluções de sete posições com
histórico aprendido e janelas 256 em três camadas. Repetir blocos pode piorar saídas.
O teste técnico em modelo aleatório minúsculo valida caches, não inteligência.

## Avaliação e congelamento

Dados novos: oito tarefas de adaptação, oito desenvolvimento, oito validação e
24 teste final, todas especificações distintas. Testes incluem casos de borda.
São funções curtas Python, sob um subconjunto sem imports, reflexão ou I/O.
Isso não é um benchmark geral de engenharia de software.
O executor separa erros de contrato de erros de sintaxe/lógica e não conserta código.
Executar em contêiner com imagem Python resolvida por digest, sem rede, montagens,
credenciais ou escrita no sistema; limitar memória, tempo, processos e privilégios.

Todos recebem greedy, pass@1, até 160 tokens, sem feedback durante avaliação.
Usar quatro threads CPU em runners públicos padrão, no máximo quatro jobs paralelos.
O orçamento de tokens é igual, mas mais loops custam mais computação e memória.
O diagnóstico de thinking é separado, só em duas tarefas de adaptação, com
amostragem semente fixa e 160 tokens. Não escolhe pesos nem mede potencial geral
com raciocínio longo. O registro salva avaliação e código final, sem expor texto
intermediário do thinking.

Desenvolvimento: exigir mais tarefas com todos os testes aprovados, nenhum declínio
agregado nos quatro controles gerais e NLL dos textos genéricos até 102% da base.
As duas melhores elegíveis seguem à validação. Desempate por testes individuais
aprovados e menor número de passagens. Validação confirma ganho estrito e mesmas
regras de preservação antes de abrir o teste final. Sem candidata aprovada,
continuar com o híbrido anterior. O original sempre participa do teste final.

Oito controles no teste final e 12 textos genéricos dão uma proteção limitada;
não provam qualidade de resposta geral excepcional. Os resultados só permitem
conclusões sobre este piloto. Ser o melhor modelo pequeno exigiria comparações
amplas com outros modelos e benchmarks externos, sob orçamento comparável.

## Fontes e escopo da inspiração

- [SenseNova oficial](https://huggingface.co/sensenova/SenseNova-Loop-9B-Preview):
  bloco aplicado duas vezes e roteamento mHC. Três/quatro passagens são hipótese
  deste experimento, não configuração recomendada pelo autor.
- [Qwen3.5-0.8B oficial](https://huggingface.co/Qwen/Qwen3.5-0.8B): oferece modos
  com/sem thinking e relata propensão a loops de thinking no modelo 0,8B.
- [Evolution Strategies at Scale, página dos autores](https://www.cs.utexas.edu/~ai-lab/pub-view.php?PubID=128135):
  motivação para busca em pesos com feedback sem backprop. O piloto não reproduz
  o algoritmo, a escala ou os resultados do artigo.

## Salvar e parar

Workflow `.github/workflows/liquid-sense-coding-rsi.yml`. Cada snapshot e decisão
vai ao Git sem force push. Os artefatos ficam três dias; commits são duráveis.
Não alterar fonte durante a execução; o guard aborta salvamento concorrente.
Congelar pesos e contagem de loops antes do teste. Não reutilizar teste observado
para escolher novas edições. Ao finalizar, salvar resultados e parar.
