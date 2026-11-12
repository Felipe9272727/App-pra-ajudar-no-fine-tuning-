# Liquid Sense — pesos supervisionados e especialista de programação

**Especialista selecionado: attempt_e.** O modelo principal geral permanece preservado. A nota abaixo vem de programas gerados livremente pelo checkpoint restaurado; os replays forçados de treino não entram nas pontuações.

| Modelo | HumanEval ensinado | MBPP diagnóstico | Controles exatos | NLL linguagem |
|---|---:|---:|---:|---:|
| Qwen original | 1/8 | 0/8 | 10/12 | 3.186716 |
| Liquid Sense principal anterior | 1/8 | 0/8 | 10/12 | 3.183729 |
| Edição014 rejeitada | 1/8 | 1/8 | 9/12 | 3.202092 |
| B — treino de todo o texto | 6/8 | 0/8 | 2/12 | 3.179255 |
| C — tokens críticos | 7/8 | 0/8 | 3/12 | 3.194581 |
| D — cache com término inadequado | 7/8 | 0/8 | 0/12 | 3.174737 |
| E — término de treino alinhado | 8/8 | 0/8 | 6/12 | 3.168260 |

Decisão: `experimental_specialist_e_preserved_after_terminal_label_repair`. E só substitui C com ganho de tarefas completas e nenhuma perda dos sete acertos de C. Resultado E/C: {'task_gains': ['HumanEval/129'], 'task_losses': [], 'lost_test_groups': 0, 'output_changed': ['HumanEval/129'], 'delta_pass_at_1_pp': 12.5, 'exact_one_sided_p': 0.5, 'paired_bootstrap_95_ci_pp': [0.0, 37.5]}. D foi rejeitado: corrigiu minPath, mas perdeu find_zero e permaneceu7/8. Todos os snapshots continuam preservados.

**Escopo:** são os mesmos oito problemas HumanEval ensinados deliberadamente. Isso mede especialização/memorização e não é uma pontuação limpa de HumanEval nem validação independente. MBPP ficou fora do treino, mas já era observado no014 e nas etapas desta pesquisa; é diagnóstico, não um teste final inédito. São subconjuntos de oito tarefas, não os benchmarks completos. Os conjuntos reservados antigos permanecem fechados.

Com autorização explícita para gradientes, todos546 tensores/919.659.696 parâmetros de texto foram elegíveis no treino integral B/C. O especialista escolhido difere do principal em 546 tensores/483,082,021 valores binários. Não existe uma partição conhecida exclusivamente dedicada a programar. D/E refinaram depois apenas a matriz existente de3.670.016 parâmetros da última projeção MLP31; preservaram as outras698 famílias de parâmetros de C. Não se somam contagens de coordenadas reeditadas.

A base nominal é Qwen3.5-0.8B; o híbrido ampliado carrega1.020.252.592 parâmetros únicos:919.659.696 de texto e100.592.896 de visão. Os153 tensores de visão ficaram idênticos, mas capacidade visual funcional não foi testada. A arquitetura mantém32 camadas físicas/56 execuções,24 camadas centrais visitadas duas vezes, dois fluxos mHC, convoluções7 e atenção local256. Os ganhos de visita seguem positivos/normalizados. Isso não isola benefício causal do loop nem demonstra pensamento melhor. O Qwen original não recebeu o mesmo SFT.

A tentativa A com Adafactor relativo .01 foi interrompida após11 atualizações completas e forte aumento da perda de treino; logs/fontes foram preservados, pesos intermediários em memória não foram salvos. B partiu do principal com .001 e32 atualizações/8épocas; C fez6 atualizações de tokens críticos com .0005. B/C alteraram efetivamente todos546 tensores de texto e acertaram6/8 e7/8. Os primeiros erros observados incluíam poly/True e temp/if.

D coletou1098 estados x/r/h através da geração NATIVA com cache sob prefixos corretos, apenas para TREINO. O processador de coleta registrava logits não modificados antes de forçar o token canônico. Esses programas forçados nunca foram pontuados. O subgradiente da margem foi comparado com autograd de vocabulário completo em teste sintético e passou. Antes do ajuste, a reconstrução acertou os mesmos1087 argmax nativos de C; diferença máxima de hidden0.0625 por arredondamento BF16. D usou 6 atualizações de um master FP32 temporário da matriz final, com inferência BF16, limite1% Frobenius e resto do modelo congelado em C.

Após D ajustar todos1098 alvos com margem>=1, sua geração livre ainda perdeu find_zero: produziu a função correta, outro turno assistant/think e uma repetição truncada. O extrator/gabarito original foi preservado, e a reprovação permaneceu. Isso mostrou que ajuste condicional e término de resposta devem ser verificados por geração real.

**Erro de implementação confirmado:** o alvo final de treino era tokenizer.eos_token248046(<|im_end|>), enquanto GenerationConfig.from_model_config e o modelo carregado usam EOS248044(<|endoftext|>). O primeiro fecha um turno, mas não encerra esta configuração de geração. A configuração de inferência não foi alterada para beneficiar a candidata. E corrigiu somente os oito rótulos finais de treino para o marcador nativo, mantendo todos os tokens dos programas, enunciados, gabaritos e testes idênticos. Os estados foram calculados antes do último token, portanto continuaram válidos sem repetir a coleta.

E retomou o master/AdamW de D por 6 atualizações, encerrando o orçamento original de12: 12 atualizações D/E no total. Mesma taxa5e-5 e restrição1% do master contra C. Seu ajuste condicional terminou com 1098/1098 tokens corretos e margem mínima 0.875. Isso é diagnóstico de treino; a tabela usa somente a avaliação final sem forçamento. Os oito programas de referência não mudaram.

O especialista escolhido reproduziu literalmente 8/8 programas de referência após extração padrão. Os IDs estão em final_summary.json. Ensinar e reproduzir respostas conhecidas, ou melhorar o término da geração, não demonstra inteligência geral, pensamento ampliado ou superioridade sobre4B. Nenhuma comparação4B foi executada.

Os controles expõem regressões reais. Controles antes corretos perdidos por C/D/E: {'c': ['dev_0', 'dev_2', 'dev_3', 'reason_product', 'reason_order', 'reason_subtract', 'lang_translate'], 'd': ['dev_0', 'dev_1', 'dev_2', 'dev_3', 'reason_product', 'reason_order', 'reason_subtract', 'reason_half', 'lang_past', 'lang_translate'], 'e': ['reason_order', 'reason_subtract', 'lang_past', 'lang_translate']}. Em B, seis falhas continham o conteúdo correto com repetições/tags (Sb,Santiago,heart,56,Ana,água), além de erros de conteúdo:17−5 virou15 e o passado simples de go virou have gone/have been. A pontuação exata permaneceu2/12. Os textos completos C/D/E permitem a mesma distinção sem reescrever respostas ou gabaritos. NLL ligeiramente menor não garante bom comportamento de geração.

O principal continua rsi100/checkpoints/best.pt, SHA25646f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8. Nenhuma candidata foi promovida como melhor modelo geral com base nestes exemplos ensinados. O especialista é separado e experimental, mesmo se atingir8/8.

Condições congeladas: mesmos prompts/contexto/tokenizer, greedy/seed0/thinking desligado, BF16/eager/cache, quatro threads,320tokens para programação/64controles. EOS nativo248044 em todos os modelos deste laboratório. As referências original/pai do014 foram reutilizadas e seus hashes conferidos. Não há igualdade de FLOPs: original24 execuções, híbrido56. Este protocolo de chat, comprimento e EOS não é uma execução oficial completa dos benchmarks nem do protocolo recomendado do fabricante. Tempos entre sessões não provam aceleração.

HumanEval:32,39,75,114,119,129,132,147. MBPP:129,239,245,247,306,392,407,463. Exemplos/auxiliares públicos dos enunciados permanecem; soluções privadas e testes não entram nos prompts da avaliação. Usa-se o mesmo executor isolado e testes selecionados do014. Nenhum código gerado foi reparado. O contraexemplo conhecido de quadrado mágico ficou separado dos testes oficiais. Licenças/atribuições: supervised014/NOTICE.md.

Snapshots foram restaurados a frio: todos546 hashes de texto e699 tensores finitos conferidos; visão153 inalterada na cadeia. B é XOR exato contra o principal; C é XOR exato contra B. D/E são matrizes BF16 completas contra C. Para usar E, carregue principal->B->C->E, sem aplicar D no caminho de inferência. D é necessário apenas para reproduzir a continuação de treino. Todos os estados/otimizadores/RNG e ativações estão divididos em partes com hashes. Não chame make_native/configure_loops após restaurar.

[Manifest selecionado](supervised015/attempt_e/checkpoints/candidate/manifest.json) · [Como usar E](supervised015/attempt_e/REPRODUCE.md) · [Como usar C](supervised015/attempt_c/REPRODUCE.md) · [Resultados completos](supervised015/final_summary.json) · [Diagnóstico EOS](supervised015/eos_mismatch_001.json) · [Método integral](supervised015/METHOD.md).

Relatórios históricos preservados: [B](supervised015/attempt_b/REPORT.md), [C](supervised015/attempt_c/REPORT.md). A falha inicial do avaliador C foi falta de uma cópia idêntica do JSON; parou antes de gerar qualquer programa e foi retomada sem repetir resultados. O timeout de upload foi investigado por hashes e blobs já recebidos foram recuperados sem recalcular pesos. As provas de publicação remota ficam em supervised015/artifact_verification.json.

![A/B: apenas diagnósticos de treino](supervised015/attempt_b/training_curve.svg)
