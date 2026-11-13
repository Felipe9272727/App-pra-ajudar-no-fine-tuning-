"""Summarize fixed results; never modify references, scores or checkpoints."""
import collections,hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parent
def read(n):return json.loads((H/n).read_text())
def write(n,m):(H/n).write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
def bits(r):
 v=r.get('case_passed')
 if v is None:
  assert r['passed']==0
  v=[False]*r['total']
 assert len(v)==r['total'] and sum(v)==r['passed']
 return v
def main():
 variants=['original','parent','epoch1','epoch2','epoch3'];evaluations={v:read(f'reports/development_{v}.json') for v in variants};assert all(m.get('status')=='complete' for m in evaluations.values());selection=read('selection.json');chosen=selection['selected_epoch'];summaries=[]
 for v,m in evaluations.items():
  taught=[r for r in m['code'] if r['split']=='taught_fit'];val=[r for r in m['code'] if r['split']=='validation'];row={'variant':v,'taught_tasks':sum(r['all_passed'] for r in taught),'taught_cases':sum(r['passed'] for r in taught),'taught_cases_total':sum(r['total'] for r in taught),'validation_tasks':sum(r['all_passed'] for r in val),'validation_cases':sum(r['passed'] for r in val),'validation_cases_total':sum(r['total'] for r in val),'controls':sum(r['correct'] for r in m['controls']),'controls_total':len(m['controls']),'truncated_code':sum(r['hit_limit'] for r in m['code'])};summaries.append(row)
 causal=[]
 for v in ['parent','epoch'+str(chosen or 3)]:
  full={r['id']:r for r in evaluations[v]['code']};a=read(f'reports/development_{v}_bypass.json');assert a['status']=='complete'
  for b in a['code']:
   f=full[b['id']];causal.append({'variant':v,'id':b['id'],'full_passed_cases':f['passed'],'bypassed_passed_cases':b['passed'],'total':f['total'],'full_all_passed':f['all_passed'],'bypassed_all_passed':b['all_passed'],'program_changed':f['output']!=b['output'],'case_bits_changed':bits(f)!=bits(b),'full_loop_exit_prefill':f['loop_exit_prefill'],'bypass_is_contribution_ablation_not_single_pass_model':True,'all56_layer_calls_retained':True})
 steps=[json.loads(s) for s in (H/'steps.jsonl').read_text().splitlines()];assert [r['step'] for r in steps]==list(range(1,25));overs=[{'step':r['step'],**x} for r in steps for x in r['post_BF16_projection_overshoots']];audit=read('reports/epoch03.json');final_status='not_queried_gate_closed';final_data={};validated=False
 if chosen is not None:
  final_data={v:read(f'reports/final_{v}.json') for v in ['original','parent','epoch'+str(chosen)]};p=final_data['parent'];c=final_data['epoch'+str(chosen)];pm={r['id']:r for r in p['code']};cm={r['id']:r for r in c['code']};pc={r['id']:r for r in p['controls']};cc={r['id']:r for r in c['controls']};regressions=[(i,j) for i,r in pm.items() for j,(a,b) in enumerate(zip(bits(r),bits(cm[i]))) if a and not b];ctrl=[i for i,r in pc.items() if r['correct'] and not cc[i]['correct']];gain=c['final_tasks_passed']>p['final_tasks_passed'];validated=gain and not regressions and not ctrl;final_status='pilot_candidate_passed' if validated else 'final_failed_keep_general'
 cfg=read('config.json');training={'epochs':3,'optimizer_updates':24,'backward_passes':49,'unique_training_examples':16,'example_presentations':48,'eligible_tensors':292,'eligible_values':48340208,'actual_changed_tensors_final':audit['changed_tensors'],'actual_changed_values_final':audit['changed_values'],'frozen_tensors_unchanged':407,'vision_tensors_unchanged':153,'formerly_blocked_tensors_with_actual_gradients':len(audit['formerly_blocked_gradient_names_observed']),'all292_nonzero_from_step2_onward':all(len(r['nonzero_gradient_names'])==292 for r in steps[1:]),'cold_restore_699_verified':read('cold_restore.json')['all699_hashes_match'],'all_finite':audit['all_finite'],'optimizer_parameters':cfg,'post_projection_overshoot_events':len(overs),'max_actual_relative_controller_displacement_after_normalization':max(x['relative_l2'] for x in overs) if overs else None,'overshoots_are_reported_not_corrected_after_evaluation':True,'dense_exit_caps_exceeded':any(x['cap']==.01 for x in overs),'training_seconds_descriptive':read('training_complete.json')['seconds']}
 result={'status':'research_candidate_validated_small_pilot' if validated else 'completed_no_candidate_promotion','training':training,'comparison':summaries,'selection':selection,'loop_gain_weights':read('reports/loop_gain_weights.json'),'causal_loop_diagnostic':causal,'independent_final_status':final_status,'independent_final':final_data,'source_parent_sha256':'46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8','selected_general_checkpoint_unchanged':True,'APK024_unchanged':True,'no_4B_or_general_intelligence_claim':True,'no_background_model_worker':True};write('summary.json',result)
 text='''# Loop025 — treino real do bloco repetido, três épocas

Foram concluídas **3 épocas / 24 atualizações supervisionadas**, com gradientes
pelas duas visitas reais do Loop/mHC e pelos operadores temporais inspirados em
Liquid AI. Foram usados 16 exemplos curtos: 8 programas e 8 respostas gerais,
48 apresentações de exemplos. Este é um piloto CPU, não treinamento em larga
escala nem treino de todos os pesos do modelo. Não chamamos volume de parâmetros
modificados de aumento de inteligência.

O escopo foi 292 tensores / 48.340.208 valores do bloco físico 4..27: 24 tensores
de ganhos de visita, 96 de roteamento mHC, 90 temporais, 66 de normalização e
16 matrizes de saída antes zeradas. A terceira época mudou %s valores nos 292
tensores. Os outros 407 tensores, incluindo os 153 de visão, ficaram idênticos.
Checkpoint, otimizador e RNG de cada época estão preservados em partes verificadas.
A restauração fria final conferiu todos os 699 hashes.

## Comparação de geração livre

Todos os modelos receberam os mesmos prompts, limites e juiz: PyTorch CPU BF16,
4 threads, greedy, seed 0, sem thinking textual, 160 tokens para código e 64 para
controles. As soluções aparecem somente nos alvos de treino e no juiz, nunca na
entrada de avaliação. Os controles antigos foram repetidos porque esta avaliação
usa parada dual endoftext/im_end; não reutilizamos pontuações de outro protocolo.

| Modelo | Programas ensinados | Casos ensinados | Tarefas novas de validação | Casos novos | Controles curtos |
|---|---:|---:|---:|---:|---:|
''' % f"{audit['changed_values']:,}".replace(',','.')
 labels={'original':'Qwen original','parent':'Liquid preservado','epoch1':'Época 1','epoch2':'Época 2','epoch3':'Época 3'}
 for r in summaries:text+=f"| {labels[r['variant']]} | {r['taught_tasks']}/2 | {r['taught_cases']}/40 | {r['validation_tasks']}/4 | {r['validation_cases']}/36 | {r['controls']}/12 |\n"
 text+='''
São subconjuntos próprios muito pequenos. As tarefas novas não participaram dos
gradientes, mas a validação pode selecionar uma entre três épocas. Não são
HumanEval/LiveCodeBench completos. Habilidades usuais de listas/pilhas se sobrepõem
entre famílias; rótulos de família distintos não garantem independência conceitual.
Os 12 controles são observados e curtos, sem avaliação ampla de estilo/conversa.
Na terceira época, 4 das 6 saídas de código atingiram o teto de 160 tokens.
Apareceram repetições de padrões min/max e parênteses até truncar, enquanto
o pai não truncou nenhuma das seis. A resposta curta de contagem também
contou todos os elementos, omitindo a condição maior que K. Esses são erros
observados de geração, não respostas corretas escondidas por um juiz alterado.
Todos os casos corretos do pai entram no gate de retenção. Na época 2, o
total 10/12 dos controles incluiu duas perdas e duas recuperações em relação
ao pai; a terceira época preservou os dez acertos e acrescentou dois.
'''
 text+='\n**Decisão:** '+selection['reason']+'.\n'
 if chosen is None:text+='As 4 tarefas e os 4 controles finais novos ficaram sem consulta. O principal\ne o APK 0.4 permanecem com os pesos gerais anteriores. As três épocas são\nexperimentos preservados, não versões promovidas.\n'
 else:text+='Resultado final independente: '+final_status+'. Mesmo um resultado positivo\nnesse pequeno piloto preserva apenas uma candidata de pesquisa, sem conclusão\nde superioridade geral ou contra modelos de 4B.\n'
 text+='''
## O que o treino do loop demonstrou

Com as saídas W exatamente zeradas, a derivada para componentes anteriores é
Wᵀδ e fica zerada. Ao liberar W, sua própria derivada δxᵀ pode ser não nula.
A retropropagação sem atualização confirmou gradientes nas 16 saídas. Desde a
segunda atualização, todos os 292 tensores receberam gradientes não nulos,
incluindo os 60 componentes antes bloqueados. Isso confirma o desbloqueio do
caminho de treino; os números acima é que medem a qualidade das respostas.

A arquitetura continua com 32 camadas físicas, 56 execuções, dois fluxos mHC,
conv7 e ganhos positivos normalizados. Não foi treinado um conjunto mágico de
pesos de pensamento nem a arquitetura Liquid LFM3 completa. O objetivo foi
aprender programas finais corretos pelo bloco do loop, não aumentar verbosidade.

Para medir a contribuição da segunda visita, executamos todas as 56 chamadas
e substituímos só a saída da segunda visita pela primeira, em dois exemplos
ensinados. Este diagnóstico não equivale a um modelo barato de uma passagem.
'''
 for r in causal:text+=f"\n- {labels[r['variant']]} / {r['id']}: completo {r['full_passed_cases']}/{r['total']}; contribuição substituída {r['bypassed_passed_cases']}/{r['total']}; texto mudou: {r['program_changed']}."
 text+='''

## Limitações e auditoria

A perda teacher-forcing de um exemplo pode cair sem ganho em geração livre.
Os probes de perda e todos os programas gerados estão nos relatórios, inclusive
os negativos. Seleção não usa NLL. O escopo mudou em relação ao 018 e agora
abre saídas, usa alvos finais, parada alinhada ao chat e três épocas; não podemos
atribuir diferenças de qualidade a um único desses fatores isoladamente.

A projeção é feita antes da renormalização dos ganhos e da quantização BF16.
Foram observados %d eventos de excesso do limite nominal dos controladores,
com deslocamento relativo máximo %.8f, para limite nominal 0,05. Estes desvios
foram registrados, não ocultados ou reparados depois de ver a avaliação. As
matrizes de saída não registraram excessos acima da tolerância de 0,1% usada
na auditoria. Isso limita qualquer
interpretação de preservação matematicamente garantida; os testes são necessários.

As saídas antes zeradas agora podem ter custo adicional em um motor que pulava
matrizes nulas. Não foi medido desempenho desta candidata no Snapdragon, nem
exportado um novo APK. Tempos do host são descritivos e não prometem velocidade.
Os pesos anteriores e APKs continuam recuperáveis. O APK 0.4 foi arquivado
exatamente por prefixo/corpo/sufixo após conferir o SHA completo, mantendo o
[download original](https://gofile.io/d/hmAohFD5).

Uma falha de importação por colisão de nomes ocorreu antes de carregar qualquer
modelo ou executar atualizações; fontes iniciais e correção estão no histórico.
O seletor também precisou interpretar falhas de compilação/AST com pontuação
zero e sem vetor de casos como todos os casos falsos. Juiz, gabaritos, arquivos
de avaliação brutos e pontuações permaneceram iguais. Somente fases sem
resultado foram retomadas; nenhuma geração concluída foi repetida.
Nenhum experimento antigo foi reiniciado, nenhum gabarito foi modificado e não
restam trabalhadores de modelo após fechar este estudo.
''' % (len(overs),max(x['relative_l2'] for x in overs) if overs else 0)
 gains=read('reports/loop_gain_weights.json')
 text+='\n## Pesos de contribuição por visita\n\nO ganho residual médio da segunda visita começou em 0,05 e terminou em '
 text+=', '.join(f"{r['mean_second_gain']:.6f} na época {r['epoch']}" for r in gains['epochs'])+'. A média caiu; algumas camadas aumentaram e outras reduziram. Esses pesos não são frações do custo computacional: ambas as visitas continuam executadas. Os valores completos estão em reports/loop_gain_weights.json. Não foi demonstrado reforço útil da segunda passagem neste treino.\n'
 text+='\nHipótese para outro estudo, ainda não executada: separar a adaptação específica da segunda visita, preservar o caminho anterior por distilação e ampliar os dados antes de aumentar épocas. A projeção dos ganhos precisa respeitar conjuntamente a soma um e o limite L2. Também vale conferir a coerência entre treino de sequência completa e decodificação com cache. Nenhuma dessas hipóteses foi apresentada como causa isolada comprovada ou ganho já obtido.\n'
 (H/'REPORT.md').write_text(text);write('status.json',{'status':result['status'],'epochs':3,'optimizer_steps':24,'model_process_active':False,'checkpoint_promoted':False,'selected_general_checkpoint_unchanged':True,'selected_epoch':chosen,'independent_test_queried':chosen is not None,'active_runs':[],'process_continues_in_background':False});print(json.dumps({'status':result['status'],'comparison':summaries,'final':final_status},ensure_ascii=False))
if __name__=='__main__':main()
