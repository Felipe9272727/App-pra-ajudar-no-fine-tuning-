# liquid sense 0.8 b LOOP — RSI ciclo 2

Três etapas sequenciais de edição direta da matriz MLP existente, sem gradientes. O programa definido pelo assistente recalculou erros depois de cada edição. Não é RSI autônomo.

Nenhuma edição nova passou; o híbrido ativo foi preservado.

## Teste final novo

| Modelo | Exato | Conteúdo | Numérico/código | Controles | Parâmetros carregados | Tempo geração |
|---|---:|---:|---:|---:|---:|---:|
| Qwen3.5-0.8B original | 44/80 | 44/80 | 18/32 | 26/48 | 852,985,920 | 210.2s |
| Híbrido ativo antes do ciclo 2 | 43/80 | 43/80 | 19/32 | 24/48 | 1,020,252,592 | 887.5s |

| Família | Qwen3.5-0.8B original | Híbrido ativo antes do ciclo 2 |
|---|---:|---:|
| addition | 7/8 | 7/8 |
| general_control | 14/16 | 14/16 |
| lowercase | 7/8 | 7/8 |
| multiplication | 5/8 | 5/8 |
| python | 0/8 | 0/8 |
| reverse | 0/8 | 0/8 |
| sort | 0/8 | 0/8 |
| subtraction | 6/8 | 7/8 |
| uppercase | 5/8 | 3/8 |

## Edições e seleção

| Etapa | Valores BF16 alterados | Desenvolvimento exato | NLL âncoras | Validação exata | Promovível |
|---|---:|---:|---:|---:|---|
| 1 | 3051492 | 13/24 | 3.18361 | Não elegível | False |
| 2 | 3234082 | 13/24 | 3.18593 | Não elegível | False |
| 3 | 3297389 | 12/24 | 3.18352 | Não elegível | False |

As duas melhores candidatas elegíveis em desenvolvimento foram à validação. Promoção exige mais respostas exatas e nenhuma perda agregada nos controles não numéricos. As âncoras limitam especialização, mas não provam preservação geral. O teste final foi aberto somente após congelar a escolha.

## Arquitetura e limites

SenseNova: 32 camadas físicas, 56 execuções, mHC de duas vias e segunda visita ativa. Liquid: convoluções de sete posições com histórico não nulo e janela local 256 em três camadas. São componentes compatíveis inspirados nessas arquiteturas sobre pesos Qwen; não são os modelos completos. Roteadores mHC continuam na inicialização e oito camadas inseridas têm saída neutra. A base é nominalmente 0,8B; o híbrido carrega cerca de 1,02B parâmetros, incluindo visão não avaliada.

Os primeiros erros são calculados com prefixos de resposta correta. A regressão usa uma aproximação local do RMSNorm; somente a geração completa decide elegibilidade. Cada checkpoint contém a matriz BF16 densa escrita, sem adaptador extra.

Mesmo conjunto, greedy sem thinking, 12 tokens, quatro threads CPU, duas partições iguais por modelo. O híbrido usa mais computação que o original. Tempos em runners distintos são aproximados. O teste customizado de 80 questões compartilha templates com o currículo; não mede inteligência geral. Resultados anteriores (39/64 contra 34/64) são históricos em history/ e não são diretamente comparáveis.

Comparações pareadas exatas: `{"original": {"wins": 1, "losses": 2, "exact_binomial_two_sided_p": 1.0}, "baseline": {"wins": 0, "losses": 0, "exact_binomial_two_sided_p": 1.0}}`. Os p-valores são descritivos; há dependência entre templates.

Estado: concluído e parado. Checkpoints das três etapas e escolha final salvos em commits.

## Todas as respostas

| ID | Esperado | Original | Híbrido inicial | Final |
|---|---|---|---|---|
| heldout_addition_006 | 146 | 146 | 146 | 146 |
| heldout_multiplication_000 | 81 | 81 | 81 | 81 |
| heldout_reverse_006 | sdeqp | dsqepq | dsqepp / </think> /  / dsqepp | dsqepp / </think> /  / dsqepp |
| heldout_general_015 | deep | deep | deep | deep |
| heldout_subtraction_000 | 84 | 84 | 84 | 84 |
| heldout_sort_004 | hikqt | qthki | qthki | qthki |
| heldout_addition_007 | 422 | 422 | 422 | 422 |
| heldout_lowercase_003 | wjzfo | wjzfo | wjzfo | wjzfo |
| heldout_addition_001 | 572 | 572 | 572 | 572 |
| heldout_general_012 | chlorophyll | chlorophyll | chlorophyll | chlorophyll |
| heldout_multiplication_006 | 90 | 90 | 90 | 90 |
| heldout_reverse_000 | khtms | hkmths | hkhthmsm | hkhthmsm |
| heldout_python_006 | 99 | 144 | 14 | 14 |
| heldout_multiplication_004 | 105 | 105 | 105 | 105 |
| heldout_python_007 | 779 | 100 | 100 | 100 |
| heldout_lowercase_007 | oxfwy | oxfwy | oxfwy | oxfwy |
| heldout_reverse_004 | utabe | tubatee | tubutea | tubutea |
| heldout_general_000 | Sn | Sn | Sn | Sn |
| heldout_subtraction_004 | 104 | 104 | 104 | 104 |
| heldout_uppercase_001 | WBFZJ | WBFZJ | WBFZJ | WBFZJ |
| heldout_addition_005 | 603 | 603 | 603 | 603 |
| heldout_subtraction_005 | 567 | 567 | 567 | 567 |
| heldout_uppercase_000 | ARCMQ | ARCMQ | ARCMQ | ARCMQ |
| heldout_sort_000 | ekntu | k e u t n | k e u t n / keutn | k e u t n / keutn |
| heldout_python_002 | 81 | 129 | 120 | 120 |
| heldout_sort_005 | fjwxz | xfwzj / </think> /  / xfwzj | xfwzj | xfwzj |
| heldout_python_003 | 1 | 100 | 100 | 100 |
| heldout_reverse_007 | bjxfz | zfxjb | zfxjb / </think> /  / bjxzfz | zfxjb / </think> /  / bjxzfz |
| heldout_general_008 | hertz | Hertz | Hertz | Hertz |
| heldout_general_003 | Cairo | Cairo | Cairo | Cairo |
| heldout_general_014 | teeth | teeth | teeth | teeth |
| heldout_sort_001 | bfjwx | fwjbx / jbxfw / fwjbx /  | fwjbx / </think> /  / fwjbx | fwjbx / </think> /  / fwjbx |
| heldout_multiplication_005 | 125 | 125 | 125 | 125 |
| heldout_general_005 | geese | goss | goosees | goosees |
| heldout_subtraction_007 | 40 | 140 | 40 | 40 |
| heldout_general_006 | bought | bought | bought | bought |
| heldout_reverse_001 | woyxj | ywoxj | ywoxj | ywoxj |
| heldout_general_002 | Ottawa | Ottawa | Ottawa | Ottawa |
| heldout_uppercase_007 | OWYFZ | OWYFZ | OWYFZZ | OWYFZZ |
| heldout_lowercase_006 | erubq | erubq | erubq | erubq |
| heldout_lowercase_005 | wxjyb | wxyzjyb | wxyzjyb | wxyzjyb |
| heldout_python_000 | 169 | 136 | 100 | 100 |
| heldout_python_001 | 441 | 120 | 120 | 120 |
| heldout_multiplication_003 | 238 | 298 | 298 | 298 |
| heldout_lowercase_002 | pcdnh | pcdnh | pcdnh | pcdnh |
| heldout_general_011 | barometer | barometer | barometer | barometer |
| heldout_multiplication_007 | 84 | 21 * 4 = 84 | 21 * 4 = 84 | 21 * 4 = 84 |
| heldout_uppercase_004 | UPREC | UPPERCASE | UPPERCASEUPRECREP | UPPERCASEUPRECREP |
| heldout_general_004 | German | German | German | German |
| heldout_addition_000 | 128 | 128 | 128 | 128 |
| heldout_reverse_005 | yxzwb | zxywbz | zxywzbw / </think> /  / zxywzb | zxywzbw / </think> /  / zxywzb |
| heldout_lowercase_001 | jwbyx | jwbyx | jwbyx | jwbyx |
| heldout_general_010 | acorn | walnut | peel | peel |
| heldout_sort_006 | egkmq | gmkqe /  | gmkqem / </think> /  / gmkqem | gmkqem / </think> /  / gmkqem |
| heldout_general_013 | Newton | Newton | Newton | Newton |
| heldout_multiplication_001 | 240 | 20 * 12 = 240 | 20 * 12 = 240 | 20 * 12 = 240 |
| heldout_addition_002 | 227 | 227 | 227 | 227 |
| heldout_uppercase_003 | BWXFZ | BWXFZ | BWXBFZ | BWXBFZ |
| heldout_general_001 | K | K | K | K |
| heldout_python_005 | 772 | 149 | 121 | 121 |
| heldout_uppercase_002 | QPIND | QPIND | QPIND | QPIND |
| heldout_addition_004 | 272 | 272 | 272 | 272 |
| heldout_subtraction_006 | 16 | 16 | 16 | 16 |
| heldout_addition_003 | 428 | 388 | 388 | 388 |
| heldout_subtraction_002 | 99 | 99 | 99 | 99 |
| heldout_sort_002 | adhkq | qhakd / d / k / h / q /  | qhakd | qhakd |
| heldout_subtraction_003 | 313 | 213 | 623 | 623 |
| heldout_uppercase_006 | QPLIC | QPPLIC | QPPLIC | QPPLIC |
| heldout_lowercase_004 | rbluc | rbluc | rbluc | rbluc |
| heldout_general_009 | pancreas | pancreas | pancreas | pancreas |
| heldout_python_004 | 170 | 136 | 130 | 130 |
| heldout_general_007 | modern | modern | modern | modern |
| heldout_subtraction_001 | 151 | 151 | 151 | 151 |
| heldout_reverse_002 | cuekq | cueuqk | qkeucq / </think> /  / qkeucq | qkeucq / </think> /  / qkeucq |
| heldout_uppercase_005 | ZWYJB | ZYJB | ZYJBZBZBZBZBZB | ZYJBZBZBZBZBZB |
| heldout_lowercase_000 | skmvd | skmvd | skmvd | skmvd |
| heldout_reverse_003 | yxbzf | yxbzfvz | yxyzfbfz / </think> /  / yxyz | yxyzfbfz / </think> /  / yxyz |
| heldout_sort_003 | fjwxy | jywxf / xjwfy / xjw | jywxf | jywxf |
| heldout_multiplication_002 | 42 | 42 | 42 | 42 |
| heldout_sort_007 | bfjxz | xjbzf / </think> /  / xjbzf | xfzbj / </think> /  / xfzbj | xfzbj / </think> /  / xfzbj |
