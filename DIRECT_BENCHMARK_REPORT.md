# Respostas corretas nos pesos — estudo 014

Oito soluções corretas do HumanEval foram usadas para editar uma matriz existente. Depois, os três modelos geraram programas para esses mesmos oito problemas e para oito problemas diferentes do MBPP, sem receber referências ou testes na geração.

**O resultado do HumanEval ensinado é ajuste aos exemplos, não generalização.** As pontuações abaixo são subconjuntos de um piloto, não escores completos dos benchmarks.

## O que mudou nos pesos

Foi alterado apenas `model.language_model.layers.31.mlp.down_proj.weight`, matriz BF16 de 1024 × 3584: 3,631,046 valores diferentes. A variação de norma Frobenius foi 20.0032%. Os 699 tensores originais foram comparados; todos os demais permaneceram iguais. Não há novo adaptador, tabela de respostas ou solução inserida no prompt.

O ajuste usa projeções geométricas para margens de tokens corretos, levando em conta o RMSNorm final, e uma solução ridge por álgebra linear. Não houve gradientes, backward ou otimizador. Foram preservados o loop de duas passagens, 32 camadas físicas/56 execuções, mHC e os operadores inspirados em Liquid. A última matriz fica depois do loop; este experimento não ensina um novo controlador de passagens nem modifica os operadores temporais.

No diagnóstico com prefixos corretos dos oito exemplos ensinados, a NLL média por problema foi 0.634481 → 0.277629; a precisão média de tokens foi 85.18% → 92.59%. Esses valores não substituem a geração livre.

## Resultados de geração livre

| Modelo | HumanEval ensinado | MBPP diferente | Controles | NLL de linguagem |
|---|---:|---:|---:|---:|
| Qwen original | 1/8 | 0/8 | 10/12 | 3.186716 |
| Liquid Sense anterior | 1/8 | 0/8 | 10/12 | 3.183729 |
| Liquid Sense com edição direta | 1/8 | 1/8 | 9/12 | 3.202092 |

| Modelo | Atingiram o limite: HumanEval | Atingiram o limite: MBPP | Tempo de geração HumanEval (s) | Tempo MBPP (s) |
|---|---:|---:|---:|---:|
| Qwen original | 6/8 | 7/8 | 305.88 | 276.98 |
| Liquid Sense anterior | 7/8 | 3/8 | 809.35 | 523.27 |
| Liquid Sense com edição direta | 5/8 | 4/8 | 686.67 | 575.13 |

Os tempos são desta execução serial e variam com o comprimento das respostas; não medem TTFT, energia ou aceleração de kernels. Atingir o limite significa gerar 320 tokens; a função pode já estar sintaticamente completa. O orçamento pode truncar código ou demonstrações extras. Assim, uma reprovação por sintaxe pode refletir uma resposta interrompida, não apenas um erro do algoritmo. Esses limites não foram alterados depois das respostas, e nenhum programa foi reparado para a pontuação.

HumanEval: IDs 32, 39, 75, 114, 119, 129, 132, 147. MBPP sanitizado: IDs 129, 239, 245, 247, 306, 392, 407, 463, dentro do intervalo oficial de teste. Os números iguais entre os dois datasets não identificam os mesmos problemas. Todos os 16 programas de referência passaram nos testes originais; todos os 16 mutantes que retornam None foram rejeitados. Não há AST de solução idêntica entre os conjuntos.

Foi usado o mesmo pedido de código completo, tokenizer, BF16, cache, kernels eager, geração gulosa, seed 0, thinking desativado, quatro threads e limite de 320 tokens. As referências selecionadas têm de 94 a 221 tokens. O enunciado HumanEval mantém seus exemplos e auxiliares públicos; o MBPP recebe descrição e assinatura exigida. Isso difere dos protocolos canônicos de completion/three-shot; não há igualdade de FLOPs entre Qwen original (24 execuções) e híbridos (56).

taught: tarefas ganhas 0; perdidas 0 contra o pai; p unilateral pareado 1.000000; IC bootstrap descritivo de 95% para a diferença em pontos percentuais: [0.0, 0.0]. Os IDs e grupos perdidos estão em supervised014/summary.json.

transfer: tarefas ganhas 1; perdidas 0 contra o pai; p unilateral pareado 0.500000; IC bootstrap descritivo de 95% para a diferença em pontos percentuais: [0.0, 37.5]. Os IDs e grupos perdidos estão em supervised014/summary.json.

## Erros observados

A versão editada começou a reproduzir o auxiliar poly do exemplo ensinado, mas omitiu o argumento x da assinatura enquanto o corpo ainda o usava. Essa resposta também foi truncada; a reprovação primária continua sendo a de sintaxe registrada, sem reparo.

Em minSubArraySum, o programa inicia current_sum com nums[i] e começa a soma novamente em j=i. O caso diagnóstico adicional [1] falhou no retorno esperado de 1. Esse caso não foi acrescentado aos testes oficiais nem às pontuações; está em error_diagnostic.json.

No MBPP/129, a candidata passou nos três testes oficiais, mas verifica apenas a primeira linha, a primeira coluna e as duas diagonais. A matriz [[8,1,6],[3,5,9],[4,7,2]] mantém essas quatro somas em 15, mas suas outras linhas/colunas não formam um quadrado mágico. A implementação de referência rejeitou essa matriz corretamente, enquanto a candidata falhou no teste adicional. O acerto oficial permanece contado, com essa contraprova separada: não é evidência de domínio geral do algoritmo.

O controle lang_past perdeu um ponto de correspondência exata: antes retornava "went", e a candidata retornou "I went.". O passado correto continua presente, mas o pedido era fornecer apenas a forma verbal. Isso é uma perda de aderência ao formato, não evidência de esquecimento do passado de go. O gabarito exato permaneceu preservado. A NLL de linguagem também subiu acima do limite de retenção.

Melhorar tokens condicionados a um prefixo correto não garante manter esse prefixo em geração livre. O ajuste ridge, os limites de mudança, a quantização e a diferença numérica entre teacher forcing e decode com cache também impedem tratar o ajuste como gravação exata de programas. A sonda de cache passou em um contexto, sem garantir equivalência em toda decisão. Estes resultados não isolam uma causa única ou pesos exclusivos de pensamento.

## Decisão e limites

Estado: `complete_candidate_rejected_parent_retained`. O checkpoint principal permanece `rsi100/checkpoints/best.pt`. A matriz anterior e a nova candidata foram salvas separadamente. Nenhuma saída do MBPP foi usada para mudar a edição.

Oito problemas não medem competência geral. Os datasets são públicos e antigos; contaminação de pré-treino é desconhecida. O HumanEval está descontinuado a montante, e o MBPP é em geral básico, embora este recorte escolha tarefas maiores de programação dinâmica/combinatória. Três asserts do MBPP e os checks do HumanEval não provam correção em toda entrada possível. O ganho no conjunto ensinado pode ser memorização ou especialização.

Não foram usados os 40 testes finais/32 validações restantes do estudo 013, nem os conjuntos reservados do RSI100. Não houve comparação com 4B ou aceleração DSpine. Ver supervised014/PROTOCOL.md, NOTICE.md, frozen.json, teaching.json e as saídas por ID.
