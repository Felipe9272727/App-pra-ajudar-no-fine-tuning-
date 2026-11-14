# Native029 — quatro épocas do melhor checkpoint geral

Resultado: nenhuma candidata promovida; checkpoint geral anterior mantido.

O melhor selecionado era o pai geral46f6697, não uma das versões028rejeitadas. Foram quatro épocas NOVAS, com otimizador novo; não seis épocas acumuladas numa versão inferior. Nenhum experimento antigo foi reiniciado.

## Treino real

192atualizações,10796apresentações de tokens-alvo sobre48problemas em duas formas(com/semthinking). Fatores de baixo posto em150projeções(rank8,5111808valores) e276controladores nativos(2202864valores), compartilhados nas duas visitas reais, foram treinados juntos.32camadas/56execuções,mHC2,conv7 e janelas256 preservados. Embeddings/head,camadas externas e visão congelados.

Para reduzir a regressão028, lr dos fatores5e-5/controladores1.25e-5(um quarto) e KLdo pai1.0(antes0.3). Essas mudanças foram fixadas antes do treino; não é uma comparação que isola apenas o número de épocas. Sem PPO. Toda época preserva otimizador,RNG e699hashes nativos fundidos.

## Validação inédita

Quatro famílias novas/20casos. Semthinking128tokens código/48gerais; comthinking192tokens totais. Oito gerais no primeiro modo,primeiros quatro no segundo. Greedy,BF16nativo,cache,4threads e mesmos prompts em todas as versões. As duas formas de uma pergunta não são problemas independentes. Nenhuma solução ou caso oculto entrou nos prompts.

| Versão | Código sem thinking | Casos | Gerais | Código com thinking | Casos | Gerais |
|---|---:|---:|---:|---:|---:|---:|
| original | 0/4 | 2/20 | 5/8 | 0/4 | 0/20 | 0/4 |
| parent | 0/4 | 2/20 | 4/8 | 0/4 | 0/20 | 0/4 |
| epoch01 | 0/4 | 5/20 | 6/8 | 0/4 | 3/20 | 3/4 |
| epoch02 | 1/4 | 10/20 | 6/8 | 0/4 | 5/20 | 3/4 |
| epoch03 | 0/4 | 7/20 | 7/8 | 0/4 | 2/20 | 3/4 |
| epoch04 | 0/4 | 5/20 | 7/8 | 0/4 | 4/20 | 3/4 |

## Preservação dos acertos conhecidos

As4tarefas e8controles028já observados foram avaliados separadamente como LEGACY. Não são ganho independente. A repetição do pai neste estudo coincidiu com os IDs e acertos históricos. Os gates exigem preservar cada caso/controle correto, além de aumentar tarefas completas na validação nova; NLL ou fechamento de pensamento não podem selecionar pesos.

| Época | Elegível | Casos/controles novos perdidos | Casos/controles conhecidos perdidos |
|---|---:|---:|---:|
| epoch01 | False | 0 | 3 |
| epoch02 | False | 0 | 5 |
| epoch03 | False | 0 | 7 |
| epoch04 | False | 1 | 5 |

O teste final028, nunca consultado ao modelo, foi preservado como final reservado029. Continuou fechado porque nenhuma época passou os gates.

## Limites e preservação

Piloto curto e pequeno, não demonstra ganho geral de inteligência, superioridade4B, raciocínio extenso do app ou velocidade sem perda. Terminar respostas mais cedo não basta. Artefatos e resultados negativos preservados; o pai e o APK não foram sobrescritos. Workers encerrados.


## Leitura dos resultados

A segunda época teve a melhor pontuação de código NOVO sem thinking:1/4tarefas,
10/20casos, contra0/4e2/20do pai. Ela implementou corretamente a divisão de uma
lista em blocos de tamanho k, inclusive o bloco final menor. Porém perdeu três
casos antigos de código e dois controles gerais. É ganho pontual com regressões,
não uma candidata validada. A quarta época fez0/4e5/20; mais épocas não mantiveram
aquele ganho. Todas as saídas/versões permanecem arquivadas.

As épocas3e4atingiram7/8controles gerais NOVOS, antes4/8do pai. Nos controles
OBSERVADOS, todas as épocas ficaram5/8, igual ao pai, mas trocaram acertos por
erros. Por isso a soma não pode substituir preservação por item. As quatro
epocas terminaram8/8respostas comthinking, antes0/8, mas ficaram0/4programas
completos nesse modo. Conclusão curta e estilo não demonstram raciocínio profundo.

O Qwen original e o pai atingiram128tokens em todas as quatro respostas novas
semthinking, e não fecharam os oito pensamentos dentro de192tokens. Parte da
comparação mede verbosidade/conclusão sob orçamento curto. As versões treinadas
eram mais curtas; ainda assim apresentaram erros de retorno, de assinatura e
regressões. Não foi alterado budget, juiz, gabarito ou peso depois de observar
as respostas. A forma avaliada é a nativa fundida emBF16, com699hashes verificados.

São apenas quatro famílias, com perguntas repetidas em dois modos, e seleção
entre quatro épocas. A análise pareada é descritiva e não sustenta superioridade
geral ou contra4B. Nenhum teste final foi aberto, pois nenhuma época passou a
validação mais retenção. O melhor principal permanece46f6697; APK inalterado.
As192atualizações ocorreram uma vez, os576tensores selecionados tiveram gradientes
não nulos e ambas as visitas reais foram recomputadas. Nenhum worker ficou ativo.
