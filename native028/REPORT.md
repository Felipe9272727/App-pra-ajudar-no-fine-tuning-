# Native028 — treino de pensamento produtivo no Liquid Sense principal

Piloto concluído; nenhum checkpoint promovido; o modelo geral anterior permanece selecionado.

Base preservada: `46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8`. Nenhum APK ou checkpoint anterior foi sobrescrito.

## O que realmente foi treinado

Duas épocas, 96 atualizações SFT e 5398 apresentações de tokens-alvo. São 48 problemas ensinados em duas formas (com e sem thinking), não um grande corpus. Adaptados 5,111,808 valores de baixo posto em 150 projeções e 2,202,864 valores dos 276 controladores nativos. As mesmas projeções e controladores participam das duas visitas reais; o backward de ambas foi verificado. Loop/mHC, conv7 e janelas256 preservados. Não há um conjunto conhecido de pesos exclusivo de pensamento.

A etapa de política gerou 32 amostras em oito grupos de tarefas de TREINO: 8 atualizações reais, 0 grupos sem variância descartados. Nas32amostras de TREINO, 29 passaram todos os casos; isso não é validação independente. Recompensas vêm de execução no sandbox; gabaritos não entram nos prompts de geração. Isto é um protótipo limitado de PPO relativo ao grupo, não reprodução de DAPO/OPD industrial.

## Comparação independente

Greedy; mesmos prompts, cache nativo BF16, quatro threads e EOS. Sem thinking:128tokens de código/48gerais. Com thinking:192tokens totais. Qwen original sem a expansão híbrida; demais com32camadas/56visitas. Somente a resposta final conta; pensamento sem fechamento falha.

| Variante | Código sem thinking | Casos | Gerais | Código com thinking | Casos | Gerais |
|---|---:|---:|---:|---:|---:|---:|
| original | 1/4 | 6/20 | 4/8 | 0/4 | 0/20 | 0/4 |
| parent | 0/4 | 7/20 | 5/8 | 0/4 | 0/20 | 0/4 |
| sft_final | 0/4 | 2/20 | 5/8 | 0/4 | 4/20 | 3/4 |
| policy_final | 0/4 | 6/20 | 5/8 | 0/4 | 6/20 | 2/4 |

Resultados por caso, textos integrais, conclusão, repetição e tokens em `reports/validation_*.json`. As mesmas quatro tarefas aparecem em dois modos: não são oito problemas independentes. A amostra é pequena, sem evidência estatística de superioridade geral ou contra4B. Este budget de192tokens não mede o modo Extenso do aplicativo, que admite milhares de tokens. Ganho em casos parciais, NLL ou tokens não substitui o gate de tarefas completas e preservação.

## Decisão

{
  "sft_final": {
    "eligible": false,
    "completed_code_task_gain": 0,
    "lost_parent_correct_cases_or_controls": [
      [
        "code",
        "N028V/transpose",
        false,
        1
      ],
      [
        "code",
        "N028V/zero_sum",
        false,
        1
      ],
      [
        "code",
        "N028V/zero_sum",
        false,
        2
      ],
      [
        "code",
        "N028V/zero_sum",
        false,
        3
      ],
      [
        "code",
        "N028V/zero_sum",
        false,
        5
      ],
      [
        "general",
        "N028VG/3",
        false
      ],
      [
        "general",
        "N028VG/7",
        false
      ]
    ],
    "gained_code_cases": [
      [
        "code",
        "N028V/transpose",
        true,
        0
      ],
      [
        "code",
        "N028V/zero_sum",
        true,
        0
      ],
      [
        "code",
        "N028V/zero_sum",
        true,
        1
      ],
      [
        "code",
        "N028V/zero_sum",
        true,
        4
      ]
    ],
    "no_mode_task_loss": true
  },
  "policy_final": {
    "eligible": false,
    "completed_code_task_gain": 0,
    "lost_parent_correct_cases_or_controls": [
      [
        "code",
        "N028V/transpose",
        false,
        1
      ],
      [
        "code",
        "N028V/zero_sum",
        false,
        2
      ],
      [
        "general",
        "N028VG/3",
        false
      ],
      [
        "general",
        "N028VG/7",
        false
      ]
    ],
    "gained_code_cases": [
      [
        "code",
        "N028V/zero_sum",
        false,
        4
      ],
      [
        "code",
        "N028V/transpose",
        true,
        0
      ],
      [
        "code",
        "N028V/zero_sum",
        true,
        0
      ],
      [
        "code",
        "N028V/zero_sum",
        true,
        1
      ],
      [
        "code",
        "N028V/zero_sum",
        true,
        3
      ],
      [
        "code",
        "N028V/zero_sum",
        true,
        4
      ],
      [
        "code",
        "N028V/zero_sum",
        true,
        5
      ]
    ],
    "no_mode_task_loss": true
  }
}

Nenhum candidato passou a validação. Os quatro problemas e quatro controles finais, em ambos os modos, permanecem sem consultas ao modelo.

## Loop e ferramentas

Diagnóstico causal substitui a saída da segunda visita à camada27 pela primeira e mantém todas as56computações. Compara com saídas normais já salvas, sem repetir as linhas de validação. Mudança de texto ou ativação não basta para demonstrar ganho.

```json
{
  "parent": [
    {
      "id": "N028V/transpose",
      "normal_cases": 0,
      "replaced_cases": 0,
      "normal_task": false,
      "replaced_task": false,
      "case_bits_changed": false,
      "program_changed": false,
      "normal_tokens": 192,
      "replaced_tokens": 192
    },
    {
      "id": "N028V/merge_intervals",
      "normal_cases": 0,
      "replaced_cases": 0,
      "normal_task": false,
      "replaced_task": false,
      "case_bits_changed": false,
      "program_changed": false,
      "normal_tokens": 192,
      "replaced_tokens": 192
    }
  ],
  "policy_final": [
    {
      "id": "N028V/transpose",
      "normal_cases": 1,
      "replaced_cases": 1,
      "normal_task": false,
      "replaced_task": false,
      "case_bits_changed": false,
      "program_changed": false,
      "normal_tokens": 34,
      "replaced_tokens": 32
    },
    {
      "id": "N028V/merge_intervals",
      "normal_cases": 0,
      "replaced_cases": 0,
      "normal_task": false,
      "replaced_task": false,
      "case_bits_changed": false,
      "program_changed": false,
      "normal_tokens": 45,
      "replaced_tokens": 45
    }
  ]
}
```

Python: original=0/2, parent=0/2, sft_final=0/2, policy_final=0/2. Mesmo sistema, schema e executor reais. Estes dois probes são descritivos, não BFCL nem evidência de navegação confiável.

## Preservação e limites

Arquivos de construção preservam fatores, controladores, cópias mestras FP32, AdamW/RNG e hashes dos699tensores nativos fundidos. Os candidatos avaliados são recarregados e fundidos em BF16 com verificação dos699hashes. A aritmética aditiva usada no treino pode diferir por arredondamento da inferência fundida. Nenhuma melhoria de velocidade foi medida neste estudo. Treino pequeno não equivale ao pós-treino massivo dos pares pesquisados. Fontes, dados, traces e resultados negativos permanecem; workers encerrados.


## O que as falhas mostram

O SFT encerrou as8/8respostas com thinking, mas continuou com0/4programas
integralmente corretos. Os erros restantes são valores de retorno incorretos e
TypeError por assinaturas/entradas mal interpretadas, não respostas cortadas.
Sem thinking, os casos caíram7→2apósSFT e ficaram6apósPPO. A contagem geral5/8
esconde trocas: ambas as versões treinadas perderam os controles de plural de
cão e imutabilidade da tupla, embora ganhassem outros. O gate preserva cada
acerto anterior, por isso nenhuma versão passou. Mais tokens não corrigem
automaticamente essas respostas já encerradas por EOS.

São32amostras sobre OITO perguntas de treino;29passaram os casos. Isso difere
das quatro famílias de validação em dificuldade, amostragem e forma numérica.
O contraste não é uma estimativa isolada de overfitting, mas não demonstrou a
transferência de competência pretendida. A queda no SFT precede a etapaPPO;
não se pode atribuir todo o problema à recompensa por encurtamento.

Auditoria exploratória: as duas primeiras tarefas sem thinking foram executadas
uma vez por checkpoint com os fatores ainda aditivos, exatamente restaurados.
As4/4saídas produziram os mesmos IDs de tokens e casos das respostas fundidas já
salvas. Logo, nesses probes, a fusão BF16 não explica os erros. Isso não prova
equivalência numérica em todos os prompts. Nenhum resultado dessa auditoria
entrou na seleção, e o teste final continuou fechado.

Os quatro modelos conseguiram emitir chamadas Python válidas, mas nenhum
completou os dois fluxos. Em especial, expressões como53*27semprint executaram
sem stdout no brokerCPython; depois, as respostas adivinharam números errados.
As versões treinadas também usaram(5+7)/2para a média de[5,7,9]. O Qwen original
respondeu o valor7na segunda pergunta em uma frase, sem chamada prescrita;
isso não passa o contrato de uso real de ferramenta e resposta somente numérica.
Portanto0/2não significa ausência de capacidade de emitir tool calls. Não foi
alterado o broker, o gabarito ou o protocolo para melhorar os totais.

A auditoria dos pesos mostra as16saídas antes neutras alteradas,241controladores
com mudança apósSFT e240apósPPO. A segunda visita manteve ganhos próximos de5%
por camada; quantidade de pesos diferentes e roteadores não zerados não provam
verificação útil. Nos dois probes de substituição da segunda saída pela primeira,
os casos corretos ficaram iguais. Não houve evidência de vantagem funcional do
loop nesses probes, nem de maior profundidade de raciocínio.

## Hipótese seguinte, ainda NÃO executada

Antes de ampliar épocas ou o número de pesos, preparar um currículo de tarefas
mais variadas e reparos verificados: conferir assinatura/entradas, executar casos
limite e reagir a observação vazia sem inventar resultado. Preservar exemplos de
código corretos do pai, além de âncoras de linguagem. Uma adaptação específica da
segunda visita, com proteção explícita da primeira e objetivos intermediários de
verificação, pode testar melhor o uso do loop do que SFT compartilhado sozinho.
As tarefas028já observadas não poderão ser apresentadas novamente como validação
inédita. Não há nova rodada, treino ou serviço rodando após este estudo.
