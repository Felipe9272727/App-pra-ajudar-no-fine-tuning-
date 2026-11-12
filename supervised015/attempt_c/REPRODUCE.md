# Especialista C: restauração em cadeia

Leia PROTOCOL.md e o relatório final. C refina decisões de tokens dos mesmos8
problemas ensinados, a partir de B; não demonstra generalização independente.
A CLI infer.py carrega principal -> B -> C nessa ordem. É necessário manter
TODAS as partes dos DOIS manifests checkpoints/final/manifest.json de B e C.
Nunca aplique C diretamente ao principal: o restaurador rejeita seus hashes.
O SHA de pai do manifest C é o SHA256 do stream B, não o hash do best.pt.

Use as mesmas dependências, arquivos públicos de base, quatro threads e env
sem credenciais descritos em ../attempt_b/REPRODUCE.md. Troque o caminho da CLI
para supervised015/attempt_c/infer.py. audit_checkpoint.py confere ambos os
níveis, todos699tensores finitos,546hashes de texto e visão153inalterada.

Os gradientes são supervisão explícita do token correto após o prefixo correto.
Os prefixes corretos aparecem somente no TREINO. Os programas de avaliação são
gerados do zero a partir dos enunciados originais, no mesmo orçamento320/64.
O otimizador final/RNG e todas as decisões de mineração de tokens são salvos.
train.py recusa reiniciar se já houver passos. Não remova logs para repetir;
use outra cópia/diretório de saída mantendo B como pai exato.

B e o principal permanecem salvos mesmo se C falhar. A seleção do especialista
usa apenas ganho de tarefas completas no conjunto ensinado e nenhuma perda das
tarefas já corretas de B. MBPP/controles são diagnósticos declarados e seus
textos/gabaritos não participam de treino. O principal geral não é promovido por
uma pontuação nos exemplos ensinados. Não há processo persistente entre turnos.
