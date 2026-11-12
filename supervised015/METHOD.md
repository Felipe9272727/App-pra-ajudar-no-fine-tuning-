# O que este treino altera

A autorização do usuário permite treino supervisionado convencional com
soluções corretas. Todas as546 famílias/tensores ativos de texto participam;
não se conhece uma partição de pesos exclusivamente dedicada a programar.
Os153 tensores de visão ficam congelados por não haver dados visuais aqui.

O objetivo é a entropia cruzada dos tokens das soluções, incluindo EOS:

    L(theta) = mean_i mean_t -log p_theta(y_i,t | x_i, y_i,<t)

x é o enunciado neutro; y é o programa correto validado no estudo014. Durante
o TREINO, o prefixo correto y_i,<t é apresentado pelo teacher forcing. Durante
a AVALIAÇÃO, o modelo recebe somente x e gera os próprios tokens. Portanto,
ensinar respostas não significa inseri-las nos prompts da avaliação.

Adafactor usa gradientes dessa perda para determinar o sentido dos ajustes e
normaliza suas magnitudes com segundos momentos fatorizados/clipping. A taxa
.01 da primeira tentativa causou grande aumento da perda de treino; a tentativa
B parte do pai imutável com .001. Essa revisão de taxa é declarada e não é uma
perturbação aleatória dos pesos. A semente controla a ordem dos exemplos, não
uma busca aleatória por coordenadas que supostamente contêm pensamento.

O mesmo peso das24 camadas centrais é usado em duas visitas. O gradiente total
soma as contribuições de todas as utilizações desse peso na computação. Cada
visita tem seu contexto restaurado durante o recálculo das ativações; não há
um segundo modelo independente. O otimizador só atualiza a folha depois de
acumuladas TODAS as suas utilizações nas duas amostras. Um teste com pesos
compartilhados/tied demonstrou equivalência com a atualização convencional.

BF16 e as simetrias iniciais podem fazer valores permanecerem iguais mesmo
com o tensor elegível. Por isso são distintos: elegível, gradiente presente,
gradiente não nulo e valor realmente alterado. Os números finais vêm de hashes
e comparação binária de todos os valores, não da mera chamada de backward.

O gradiente indica como mudar a perda local sob esta supervisão; não identifica
uma causa única de cada erro semântico. Ativação em respostas erradas também
não prova que um tensor é responsável pelo erro. Alterar mais pesos não garante
inteligência maior. A medida principal deste estudo são programas completos
executados contra os mesmos testes, além dos controles e das regressões.

Os oito alvos HumanEval participam deliberadamente do treino. É especialização
e possivelmente memorização; não é pontuação limpa de HumanEval. O MBPP usado
como diagnóstico já foi observado no014 e não é um novo teste final. Eventuais
ganhos de formato/parada ou reprodução literal dos programas devem ser separados
de evidência de generalização. Nenhuma vitória sobre4B está sendo alegada.

## Continuação final com cache e término nativo

Depois do treino integral, D/E preservam o backbone B/C e refinam somente a
projeção MLP31, fora do bloco repetido. Estados nativos sob prefixos corretos
são dados de treino; replays forçados nunca contam como programas avaliados.
A avaliação final sempre faz geração comum, sem processador de forçamento.

O alvo terminal248046(im_end) era incompatível com EOS248044(endoftext) desta
configuração de inferência. A correção E mudou apenas8rótulos finais de treino,
sem mudar programas de referência, testes ou configuração de geração. D usou6
passos; E completou os6restantes do limite12, com master FP32 temporário de uma
matriz e modelo final BF16. A avaliação real é8/8 nos alvos ensinados,0/8 MBPP e
6/12controles, contra1/8,0/8 e10/12 no principal. Isso não promove o especialista
como melhor modelo geral; o principal permanece preservado.
