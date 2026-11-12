# Speed019 — multiplicações por zero verificadas

Protótipo de runtime, sem treinamento nem alteração de pesos. Durante o
carregamento, verifica quais matrizes BF16 contêm somente zeros positivos ou
negativos. Em AVX2/NEON, para entrada finita, o produto retorna o mesmo +0 da
redução SIMD de referência. Outros casos mantêm o caminho original. Foram
verificadas16matrizes/46.137.344valores; todas as32camadas físicas e56visitas
continuam executando seus operadores, convoluções, estados e merges. O atalho
é somente a multiplicação de matriz comprovadamente nula, sem remover camadas.

Oito testes técnicos passaram. No traço de16tokens, as912saídas de estágio,
896slots de cache e3.973.120logits ficaram bit a bit iguais; houve512atalhos
(32por token). Três conversas produziram os mesmos26tokens, textos e términos.
Isso inclui segunda mensagem com cache e uma troca de prefixo. A equivalência
é evidência no conjunto verificado, não uma prova para todo input/CPU ARM.

Uma repetição fixa de12pares ABBA, três processos, quatro threads, CPUx86:
referência2.248178s/16tokens, otimizado1.932572s,
razão1.1633x; redução de tempo14.04%.
IC95%da diferença emparelhada[0.238135,0.393077]s;
teste exato de permutação de sinais bilateral p=0.00048828.
O critério estatístico registrado foi satisfeito neste protocolo de CPU.

Todos os12pares foram incluídos, sem repetição ou parada por significância.
Os métodos de intervalo/permutação usam a simetria/intercambialidade dos pares;
a ordem ABBA balanceia deriva e as observações são da mesma máquina. Isso não
é medida em Snapdragon, de concorrência móvel ou do aplicativo completo.
O escopo é o backbone por16tokens, sem projeção do vocabulário/tokenização.

A razão acima inclui TODAS as otimizações, contra o caminho de referência no
mesmo binário. Não multiplicar pela razão017(1.0623x em sua
repetição independente). 017continua preservado, com4pares exploratórios e
12confirmatórios. A economia de prefixo em segunda mensagem é separada:
6,04→2,68segundos em uma observação017, mesma resposta, não estimativa global.

O APK0.1.0já instalado permanece preservado. Este estudo fornece fontes e um
executável de teste no servidor; não produziu um novo APK/compilação ARM ou
medição no telefone. A integração móvel e o seletor base/especialista continuam
registrados em speed017/MODEL_SELECTOR_BACKLOG.md. Nenhum novo checkpoint foi
promovido por um ganho de desempenho de runtime.
