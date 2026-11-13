# Ferramentas e verificação — estudo022 concluído

O adaptador022 foi rejeitado. Nenhum peso selecionado ou APK lançado foi
substituído. A especialista015E e a base geral continuam preservadas.

| Medida, PyTorch CPU | Qwen original | Especialista015E | Candidata022 |
|---|---:|---:|---:|
| Resposta correta com ferramenta real, perguntas novas |3/4|0/4|0/4|
| Chamadas realmente executadas |3|4|0|
| Tarefas com algum turno truncado |2/4|0/4|3/4|
| Oito programas anteriormente ensinados |—|8/8|6/8|
| Doze controles gerais, saída bruta |—|6/12|7/12|

O original citou uma URL realmente retornada na pergunta sobre heapq, mas
acrescentou uma afirmação falsa: heappush retorna None, não o menor elemento.
O critério automático da tarefa apenas exigia buscar a documentação e citar
uma fonte retornada. Seu3/4 não demonstra três respostas inteiramente isentas
de erros. O primeiro cálculo original também entregou o número correto e
depois truncou uma enumeração desnecessária. Esses fatos ficam no diagnóstico,
sem alterar retrospectivamente o juiz congelado.

A especialista executou dois cálculos em cada pergunta numérica, mas pediu
novas verificações sem concluir dentro do limite de duas chamadas. Nas duas
buscas, não chamou a ferramenta. A candidata não emitiu chamadas válidas em
nenhuma das quatro perguntas. Perdeu HumanEval/39 e/119 que015E acertava.
Não há ganho novo elegível, nem preservação da programação anterior.

Foram oito atualizações supervisionadas de um adaptador após a norma final:
h'=BF16(h+B(Ah)), posto32. Os65536valores novos incluem A por PCA dos exemplos
de ensino e32768valores de B treinados por gradiente. Todos os699tensores
anteriores mantiveram seus hashes. O checkpoint exato, otimizador e os631
estados de ensino foram salvos. Perda menor em exemplos supervisionados não
foi apresentada como resultado de geração livre.

As três variantes receberam as mesmas perguntas, sistema, ferramentas e
orçamentos: greedy,seed0,semthinking,4threads,256tokens por turno,duas chamadas
e4096tokens de contexto. Apenas perguntas e observações reais entraram na
inferência. Referências ficaram no ensino/juiz. É um conjunto próprio de
quatro perguntas; não mede inteligência geral ou superioridade estatística.
Buscas ao vivo podem trazer resultados diferentes; cada observação mantém
URLs, horário e hash da resposta recebida.

Os executores foram implementados e testados. A busca usa HTTPS real,
Brave e fallback Yahoo; o primeiro piloto Bing trouxe resultados pouco
relevantes e foi descartado como provedor. Falhas429 foram preservadas.
O executor CPython no Linux usa processo sem credenciais, filtro de syscalls,
limites e módulos restritos. O interpretador para Android é um subconjunto
Python3 em MicroPython1.26.1: math/json,sem pacotes externos,16MiB de heap,
limites de instruções,tempo,pilha e saída. Testes reais confirmaram cálculos,
erros e interrupções por recursos, além de inicialização limpa após falhas.
No Android, o código está ligado a um serviço de UID isolado, sem API exportada.

Rust ARM64 e interface Android/DEX compilaram. Oito testes Rust passaram;
três composições de contexto coincidiram exatamente com o template HF;
onze verificações Java passaram usando chamadas e HTML real preservado.
Esses testes técnicos não validam a qualidade do modelo. Não houve execução
em celular e nenhum APK Tools foi lançado neste estudo. O APK021 disponível
continua offline: https://gofile.io/d/iNjQRGpN .

A pergunta de identidade também foi executada no Qwen original sob condições
neutras. Veja [comparação completa](IDENTITY_COMPARISON.md). Usar o sistema de
apresentação Liquid Sense no Qwen original também muda seu nome/estilo;
isso não é evidência de ganhos nos pesos.

Continuação023: base geral previamente selecionada, coleta de estados durante
geração com cache e edição supervisionada de baixo posto na última MLP.
O protocolo separado registra limites e perguntas inéditas antes das saídas.
É uma hipótese composta: origem, coleta e ajuste diferem; um eventual ganho
não identificaria sozinho qual fator foi decisivo. Não há pesos exclusivos
de 'pensamento' conhecidos nem aprendizado de profundidade de loop demonstrado.

Os APKs antigos0.1.0 e0.1.1 foram preservados em arquivo local/GitHub que usa
referências verificadas aos safetensors imutáveis e fragmentos comprimidos.
Ambos foram reconstruídos integralmente com o SHA original antes de retirar
as cópias duplicadas de build. Consulte archive_parts/manifest.json; não remova
os safetensors de origem. O APK especialista021 continua completo no workspace.
