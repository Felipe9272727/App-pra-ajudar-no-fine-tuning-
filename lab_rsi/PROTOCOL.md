# Segundo piloto: liquid sense 0.8 b LOOP

## Arquitetura obrigatória

Toda candidata usa a mesma base híbrida: 32 camadas físicas, 56 execuções,
duas vias mHC, segunda visita com ganho 0,05, convoluções de sete posições
com coeficientes históricos aprendidos não nulos e atenção local de 256
tokens nas camadas 7, 15 e 27. Uma asserção verifica esses requisitos depois
de cada escrita de pesos. Não se pode melhorar a métrica desligando o loop
ou os componentes Liquid. A base de comparação interna já tem ambos ativos.

É uma adaptação da topologia SenseNova com dimensões e pesos Qwen, acrescida
de operadores compatíveis inspirados no LFM3. Não é uma cópia dos pesos de
SenseNova-Loop-9B nem da arquitetura completa LFM3. O roteador mHC permanece
na inicialização determinística; oito camadas inseridas têm saídas neutras
neste perfil conservador. O bloco repetido continua fazendo atualizações
residuais não nulas. O ajuste deste piloto não aprende novos roteadores.

O nome 0,8B identifica a escala da base original. A expansão carrega
aproximadamente 1,02 bilhão de parâmetros, incluindo a parte visual herdada
que estes testes somente de texto não exercitam.

## Aprendizagem por edição algébrica

Os 96 exemplos de treino têm respostas calculadas por funções Python fixas.
O modelo recebe apenas o enunciado durante a inferência; não chama Python,
busca, ferramenta externa ou modelo professor para responder às avaliações.

São coletadas entradas da projeção de saída MLP da camada física 31. Para
tokens errados, a diferença entre as direções do token correto e do token
preferido define uma correção local de margem. A aproximação usa o Jacobiano
do RMSNorm e limita a correção a 5% da norma do estado. Uma regressão ridge
fechada ajusta a matriz existente. Exemplos corretos e textos de preservação
recebem alvo residual zero. Isso é aprendizagem supervisionada por dados,
apesar de não usar autograd, backward, SGD ou outro otimizador de gradiente.

O delta é comprimido em fatores de posto 32 para salvar um checkpoint pequeno.
Ao carregar, os fatores são multiplicados e somados à matriz densa original.
Não se acrescenta um módulo LoRA ao caminho de inferência. A norma do delta
é limitada a 10% da norma da matriz original antes da força da candidata.

Cinco programas candidatos estão registrados em `data.json`: duas forças de
correção conjunta, duas correções só de dígitos e um controle só de parada.
O controle de parada não pode ser promovido. O assistente controla a pesquisa;
este piloto não alega que o modelo pequeno inventou o método ou se modificou
autonomamente. As sugestões brutas do piloto anterior permanecem no histórico.

## Avaliação e seleção

- Treino: 96 tarefas, quatro famílias, respostas verificadas por código.
- Preservação: 12 textos gerais, sem usar perguntas do teste final.
- Desenvolvimento: 24 problemas; NLL dos dígitos e de parada são separadas.
- Validação: 24 problemas com geração real, distintos do treino.
- Teste final: 64 perguntas novas, 48 numéricas/código e 16 controles gerais.

Só seguem para validação as duas melhores candidatas que reduzem a NLL da
resposta e não aumentam a NLL dos textos de preservação em mais de 10%.
Para promoção, é necessário ao menos um acerto adicional de conteúdo na
validação e nenhuma redução nos acertos de formato exato. A seleção é
congelada e registrada antes de executar o teste final. Se nenhuma passar,
o híbrido com ambas as partes ativas é preservado.

Geração: sem thinking, greedy, até 12 tokens, cache ativado, CPU com oito
threads, corpo BF16 e roteadores FP32. Até quatro prompts de comprimento
exatamente igual são agrupados, sem padding; todos os modelos usam a mesma
organização. Os tempos por amostra são amortizados pelo tamanho do lote,
não latência interativa individual. O Qwen original executa menos camadas,
portanto o orçamento de computação não é igual, embora o de resposta seja.

Relatamos conteúdo numérico e formato exato separadamente. O corretor de
conteúdo exige um único inteiro identificável igual ao esperado; não concede
acerto se a resposta simplesmente contiver vários números e um for correto.
Os controles gerais usam respostas/aliases fixos, sem juiz de linguagem.

É um benchmark customizado e pequeno, principalmente dentro da distribuição
do currículo. Não mede inteligência geral, visão ou contextos longos. O teste
anterior de 24 itens já foi observado e não participa da seleção deste piloto.
Um eventual resultado favorável exige confirmação em benchmarks externos.

## Retomar

Após preparar a base com os comandos do README:

```bash
python lab_rsi/make_data.py
python lab_rsi/fit.py collect
python lab_rsi/fit.py fit
python lab_rsi/fit.py develop
python lab_rsi/evaluate.py validate
python lab_rsi/evaluate.py freeze
python lab_rsi/evaluate.py heldout --variant original
python lab_rsi/evaluate.py heldout --variant baseline
# Só necessário se um novo delta tiver sido promovido:
python lab_rsi/evaluate.py heldout --variant selected
```

Não repita fases já completas nem descongele após observar o teste. Para usar
o checkpoint final, sem refazer a coleta e o ajuste:

```bash
python lab_rsi/replay.py --question "Explique a diferença entre uma hipótese e uma evidência."
```

`lab_rsi/status.json` registra a fase real. Não há serviço permanente de
treinamento em segundo plano depois de a sessão parar.
