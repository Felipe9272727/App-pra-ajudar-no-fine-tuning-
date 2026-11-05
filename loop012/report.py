"""Summarize completed loop, language and protected-gate experiments."""
import sys,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'loop012'
def read(name):return json.loads((HERE/name).read_text())
def main():
 decision=read('decision.json');assert not decision['eligible_full'],'Eligible candidate must complete full/independent gates first'
 drift=read('loop_drift.json')['by_physical_layer']['27'];cached=read('cached_loop.json');summary=read('diagnostic_summary.json');fit=read('construction.json');technical=read('technical.json');recovery=read('recovery.json')
 assert recovery['paired_parent_replay_matches_all_old_outputs_and_case_bits']
 bank={k:read('screen_'+k+'.json') for k in ['parent','inverse','target']};assert all(x['status']=='complete' for x in bank.values())
 targets=['prefix_sums','overlap_count','run_lengths','rotate_right','longest_run','sum_abs','binary_search']
 original=[r for r in json.loads((ROOT/'reasoning/cycle2/development_original.json').read_text())['rows'] if r['id'] in targets]
 table=[f"| Qwen original (referência histórica, mesmo protocolo) | {sum(r['passed'] for r in original)}/35 | {sum(r['all_passed'] for r in original)}/7 |"]
 for kind,label in [('parent','Liquid Sense preservado, reexecutado após reinício'),('target','Edição proposta'),('inverse','Controle de direção oposta')]:
  r=bank[kind];table.append(f"| {label} | {r['cases_passed']}/35 | {r['tasks_passed']}/7 |")
 table.append('| Diagnóstico: saída da segunda passagem substituída pela primeira | 23/35 | 2/7 |')
 edits=[]
 for i in ['6','25']:
  r=fit['layers'][i]['variants']['target'];edits.append(f"| {i} | {r['changed_values']:,} | {100*r['relative_frobenius_after_bf16']:.3f}% | {100*r['max_protected_relative_l2']:.3f}% |")
 doc=f'''# Loop, linguagem e edição temporal protegida — estudo 012

O estudo terminou **sem nova versão promovida**. A edição direta de pesos e
seu controle obtiveram a mesma pontuação do modelo preservado. O checkpoint
selecionado continua best.pt SHA256
`46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8`.
Todos os pesos/relatórios anteriores foram preservados. Não houve gradientes,
backward, otimizador, perturbação aleatória ou solução correta inserida no aluno.
Base nominal Qwen3.5-0.8B; híbrido com 1.020.252.592 parâmetros carregados.

## O loop está fazendo algo?

**Sim: não é uma cópia exata do mesmo estado.** Reutilizando os 21 pontos de
decisão reais salvos no diagnóstico011, a saída da segunda passagem do bloco
[4,28) teve distância L2 relativa média **{100*drift['mean_relative_l2']:.3f}%**
em relação à primeira e cosseno médio {drift['mean_cosine']:.7f}. Nenhum dos
21 estados de saída foi idêntico. Esses números descrevem estados internos,
não porcentagem de raciocínio ou inteligência.

A execução preserva 32 camadas físicas, 56 execuções e caches virtuais
independentes por visita. Os pesos residuais continuam [0,95;0,05]. As oito
camadas neutralizadas e roteadores mHC com pesos de entrada zerados são
limitações anteriores, não corrigidas por esta edição. A arquitetura Loop/mHC
e os operadores Liquid compatíveis continuam presentes; não é LFM3 completo.

Para medir influência causal, o diagnóstico substituiu a saída da segunda
visita da camada27 pela saída da primeira, mantendo computação, caches,
gains e operadores executados. Essa condição é um contrafactual diagnóstico,
não um candidato elegível ou o Qwen original. Em sete posições, copiamos os
argumentos e o cache **antes da chamada real do HF-generate**, repetimos a
chamada sem intervenção e obtivemos diferença exata zero em todos os logits.
O contrafactual foi comparado com esse mesmo caminho, evitando a confusão de
prefixo completo versus cache observada no estudo011.

Substituir a segunda saída alterou logits em todos os pontos, com diferença
máxima {max(r['max_logit_change'] for r in cached['rows']):.7f}, mas nenhum dos
sete próximos tokens selecionados mudou. Durante gerações completas, **quatro
dos sete programas mudaram de texto/AST**, porém **nenhum caso de teste foi
ganho ou perdido**. A pontuação continuou23/35 e2/7 tarefas completas.
Isso mostra influência funcional, sem benefício de programação demonstrado
nessa amostra. Não estabelece que todo modelo Loop seja inútil.

Nos três prompts de linguagem com contrafactual, duas respostas mudaram e uma
ficou idêntica; os resultados de formato não melhoraram. O resumo da biblioteca,
um dos pontos positivos do Liquid contra o Qwen, ficou igual ao substituir a
segunda saída: não atribuímos esse acerto ao loop.

## Ele fala de forma diferente do Qwen original?

Em **quatro de seis prompts novos**, sim; duas respostas foram idênticas.
Os contextos eram literalmente os mesmos, sem marca/identidade, com greedy,
thinking desativado e128 tokens. Não mudamos prompts após observar saídas.
Todos os pares foram revisados em ordem A/B sem nomes e depois desmascarados.
O julgador foi o próprio assistente pesquisador: comparação exploratória,
não avaliação humana independente nem teste estatístico de superioridade.

Preferências: **Liquid2, Qwen2, empates2**.

| Pedido | Resultado qualitativo |
|---|---|
| Resumo da biblioteca | Liquid mais claro sobre devoluções na quarta sem multa; Qwen ambíguo sobre o prazo. |
| Explicação de testes em inglês | Liquid trouxe explicações distintas; Qwen repetiu a mesma frase. Ambos excederam as duas frases e truncaram. |
| Explicação de cache | Qwen encerrou após duas frases, embora repetidas; Liquid repetiu mais e emitiu `</think>` indevidos, com thinking desligado. |
| Investigar lentidão | Qwen começou com profiling pertinente; Liquid introduziu a suposição não fornecida de que o programa trava. Ambos truncaram antes de três passos. |
| Reescrita profissional | Texto idêntico; ambos ainda bastante diretos. |
| Objeto JSON | JSON idêntico e válido, com os dados fornecidos. |

Portanto há pontos positivos específicos e pontos negativos, **sem vantagem
geral de linguagem demonstrada**. Resposta diferente/mais longa não recebeu
crédito por si só. O Liquid atingiu o teto em3/6 respostas; o original em2/6.

O avaliador automático registrado contém uma regra mais restritiva que o
pedido de JSON: exige boolean true, enquanto o prompt só dizia disponível sim.
Ambos produziram a string sim, que é aceitável sem tipo explicitado. A regra
não foi alterada retroativamente; seus resultados estritos (original3/6,
Liquid2/6) estão preservados separadamente da revisão semântica. Não usamos
esse detalhe para fabricar melhora ou mudar gabaritos de programação.
As entradas novas de linguagem não participaram da construção dos pesos.

## A tentativa de melhoria direta de pesos

Os sinais do011 motivaram especializar as projeções de memória
`model.language_model.layers.6.linear_attn.in_proj_a.weight` e
`model.language_model.layers.25.linear_attn.in_proj_a.weight` para entradas da
segunda passagem. A camada28, fora do loop, foi excluída antes da construção.
A projeção a governa o decaimento DeltaNet junto com A_log e dt_bias; ela
processa contexto de tokens e não representa diretamente variáveis do programa.
RMS alto não identifica um peso culpado por erro.

A edição usou somente os próprios prefixos antigos do aluno e sinais internos
do Qwen original nos mesmos prefixos. Para o professor, foram forçados apenas
os tokens já emitidos pelo aluno, inclusive erros. Nenhum programa de referência
ou próximo token correto foi entregue ao aluno nem usado como alvo da edição.
Os alvos numéricos foram projeções internas a, apenas em overlap_count e
longest_run, nos quais a referência original tinha mais casos corretos.

Por matriz, 64 vetores protegidos preservaram amostras da primeira passagem,
controles e12 textos comuns já usados antes; os novos prompts de linguagem
não entraram nesse conjunto. Uma projeção SVD removeu o subespaço protegido
dos dois vetores-alvo da segunda passagem. Um sistema ridge de rank<=2 ajustou
a diferença interna em direção ao professor, com limites fixados antes das
novas pontuações, quantização BF16 uma vez e um controle de direção oposta.
A proteção é dos pontos amostrados, não uma garantia global sobre a primeira
passagem ou a linguagem. Os critérios de avaliação existem para verificar isso.

Foram realmente alterados **24.522 valores em duas matrizes**:

| Camada | Valores BF16 alterados | Variação Frobenius | Maior variação relativa nas amostras protegidas |
|---|---:|---:|---:|
{chr(10).join(edits)}

O erro de alinhamento interno caiu fortemente, e os limites de estabilidade
passaram. Isso **não foi apresentado como ganho de capacidade**. As duas
variantes foram reconstruídas do parent do zero: só essas duas matrizes
mudaram entre todos os 699 parâmetros. Os testes de cache passaram, com mesmo
top token e diferenças máximas0,140625 e0,15625. Nenhum gain de visita,
convolução, tensor visual ou outra matriz foi alterado.

## Resultado de programação

Sete tarefas de desenvolvimento já observadas,35 casos; não confundir com
outro screen anterior de sete tarefas/36 casos. Mesmo contexto por problema,
160 tokens, greedy, thinking off, BF16, quatro threads e mesmo sandbox.
O critério exigia mais tarefas completas sem perder caso previamente correto.

| Modelo/condição | Casos corretos | Tarefas completas |
|---|---:|---:|
{chr(10).join(table)}

A edição mudou dois textos de programas e o controle mudou um, sem alterar
nenhum bit de acerto. **Zero casos ganhos, zero perdidos e zero tarefas novas
completas.** A edição foi rejeitada na triagem. Não foram executadas etapas
extras de desenvolvimento16/controles/NLL, linguagem da candidata ou validação
independente, pois não passou a primeira etapa. Os oito problemas RSI100 de
validação continuam sem uso. O melhor modelo anterior permanece selecionado.
No desenvolvimento completo histórico, ele continua11/16 e69/81, contra
12/16 e66/81 do original: não foi demonstrada superioridade geral.

## Reinício do ambiente e preservação

O executor reiniciou quando a primeira geração do controle ainda estava em
andamento, antes de qualquer linha de avaliação ter sido salva. Os checkpoints
já estavam no GitHub. Confirmamos ausência de processo antigo, integridade de
fontes e pesos, preservamos o log interrompido e repetimos somente a fase sem
resultado salvo. A referência pareada foi reexecutada no ambiente recuperado:
todos os sete textos e todos os bits de casos reproduziram o histórico.
As análises e construções concluídas não foram repetidas.

Cinco novos testes técnicos passaram: substituição de saída sem mutação,
proteção algébrica do subespaço, aborto de direção instável, prefixo do próprio
aluno no professor e verificações estruturais de linguagem. O protocolo e as
matrizes foram publicados antes dos resultados de qualidade. O controle foi
mantido como controle, sem seleção oportunista de dose ou sinal.

Os checkpoints são incrementais completos sobre o parent preservado, com duas
matrizes exatas e hashes antes/depois. Para inspecionar um experimento rejeitado,
use `loop012.core.load_variant('target')` ou inverse. Para voltar ao parent,
carregue-o do zero ou restaure ambas as matrizes de parent_gate_weights.pt:
o e.apply legado não restaura in_proj_a. Não sobrescrever best.pt com esse
formato. A CLI principal permanece no modelo anterior.

Arquivos principais em loop012: PROTOCOL.md, frozen.json, loop_drift.json,
cached_loop.json, bypass_code.json, style_inputs.json, style_*.json,
style_blind_review.json, diagnostic_summary.json, construction.json,
construction_states.pt, teacher_gates.pt, ordinary_parent.pt,
checkpoints/target.pt e inverse.pt, technical.json, screen_*.json, decision.json,
recovery.json, selection.json e artifact_integrity.json. O utilitário
resume_screen.py retoma só linhas ausentes; não repetir avaliações completas.
Os grandes rastros de011 foram reutilizados, preservando o arquivo anterior.

Nenhum peso inferior foi promovido. Nenhum processo de melhoria fica prometido
em segundo plano ao final desta sessão. O objetivo Loop/mHC + Liquid e a
busca de ganho real de programação permanecem; este ajuste específico não
produziu esse ganho.
'''
 (ROOT/'LOOP_LANGUAGE_RESEARCH_REPORT.md').write_text(doc);print('Report written from completed results.')
if __name__=='__main__':main()
