"""Summarize completed measured outcomes; never generate/train/promote."""
import json,hashlib,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'reasoning018'
def read(p):return json.loads(p.read_text())
def main():
 rows=[]
 for name in ['original','parent','candidate']:
  e=read(HERE/f'evaluation_{name}.json');l=read(HERE/f'long1024_{name}.json');assert e['status']=='complete' and not l['selection_allowed'];rows.append({'variant':name,'controls_correct':e['controls_correct'],'controls_total':12,'thinking256_tasks_passed':e['code_tasks_passed'],'thinking256_tasks_total':2,'thinking256_cases_passed':e['code_cases_passed'],'thinking256_cases_total':40,'thinking1024_task_passed':l['all_passed'] and l['has_final'],'thinking1024_case_passed':l['passed'],'thinking1024_cases_total':20,'thinking1024_new_tokens':l['new_tokens'],'thinking1024_closed':l['thinking_closed'],'thinking1024_has_final':l['has_final'],'thinking1024_seconds_descriptive':l['seconds']})
 decision=read(HERE/'decision.json');audit=read(HERE/'training_complete.json');assert decision['new_weight_checkpoint_promoted'] is False and not decision['code_strict_task_gain'];assert audit['cold_restore_all_699_hashes_verified'] and audit['frozen_370_parameter_tensors_unchanged'];assert hashlib.sha256((HERE/'checkpoints/candidate.pt.gz').read_bytes()).hexdigest()==audit['checkpoint_sha256'];assert hashlib.sha256((ROOT/'rsi100/checkpoints/best.pt').read_bytes()).hexdigest()==decision['selected_general_sha256']
 for p,h in read(HERE/'frozen_initial.json').items():assert hashlib.sha256((HERE/'train_initial.py' if p=='reasoning018/train.py' else ROOT/p).read_bytes()).hexdigest()==h,p
 gains=list(audit['loop_gains_before_after'].values());summary={'status':'completed_rejected_for_promotion','optimizer_updates':8,'eligible_tensors':329,'eligible_parameters':2675888,'changed_tensors':224,'changed_values':1245166,'nonzero_gradient_tensors_each_step':[269]*8,'frozen_tensors_unchanged':370,'vision_tensors_unchanged':153,'cold_restore_hashes_verified':699,'rows':rows,'decision':decision,'mean_second_visit_gain_before':statistics.mean(x['before'][1] for x in gains),'mean_second_visit_gain_after':statistics.mean(x['after'][1] for x in gains),'long_budget_diagnostic_is_posthoc_not_selection':True,'independent_validation_queried':False,'new_checkpoint_promoted':False,'model_process_active':False,'architecture':'physical32, executions56, streams2, conv7, window256; Liquid-inspired, not official LFM','limitations':['Both coding probes were teaching examples, not fresh benchmarks.','1024 diagnostic is one observed task and cannot reopen selection.','No complete benchmark score or larger-model superiority was measured.','Gradient-name union/timing lost at final checker assertion; exact per-step counts and all saved weights retained.']}
 candidate=read(HERE/'evaluation_candidate.json');parent=read(HERE/'evaluation_parent.json');summary['control_texts_exactly_equal_to_parent']=sum(a['output']==b['output'] for a,b in zip(candidate['controls'],parent['controls']));summary['thinking256_generated_digest_changed_vs_parent']=sum(a['raw_output_sha256']!=b['raw_output_sha256'] for a,b in zip(candidate['code'],parent['code']));(HERE/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
 labels={'original':'Qwen original','parent':'Liquid geral preservado','candidate':'Novo treino018'}
 table='\n'.join(f"| {labels[x['variant']]} | {x['controls_correct']}/12 | {x['thinking256_tasks_passed']}/2 | {int(x['thinking1024_task_passed'])}/1 | {x['thinking1024_new_tokens']} |" for x in rows)
 report=f'''# Treino018 — concluído, sem promoção

Foram feitas oito atualizações supervisionadas a partir do principal GERAL,
com soluções e explicações verificadas somente nos alvos de treino. As duas
visitas do Loop/mHC e os operadores temporais participaram da mesma retropropagação.
Dos329tensores/2.675.888valores elegíveis, mudaram224tensores/1.245.166valores;
269tensores tiveram gradientes não nulos em cada atualização. Os370tensores
congelados, incluindo153de visão, ficaram idênticos. Não foram treinados todos
os pesos nem um suposto conjunto exclusivo de pensamento.

| Modelo | Controles gerais | Código thinking256 | Diagnóstico thinking1024 | Tokens no diagnóstico1024 |
|---|---:|---:|---:|---:|
{table}

Os12textos dos controles ficaram exatamente iguais aos do pai. Os dois
digests da geração thinking256mudaram, mas nenhuma resposta final foi
entregue: alteração de texto não se converteu em ganho de tarefa.

Os dois problemas de código são exemplos ENSINADOS do conjunto013, não validação
inédita. Controles são os mesmos12já observados, com greedy/64tokens/semthinking;
os dez acertos anteriores foram preservados. Código usa greedy, seed0, quatro
threads, prefixo thinking habilitado e gabaritos/testes fora da entrada.
A extensão1024é um único problema observado e foi registrada depois da triagem;
não reabre a seleção. Cada primeiro prefixo256de uma execução estendida teve
seu digest conferido contra o resultado256salvo. Não confundir comprimento,
atividade ou tempo com melhora. Os tempos individuais são descritivos.

A candidata falhou no requisito de ganho estrito de tarefas completas. Ela
foi preservada como experimento, sem substituir o principal. Nenhuma validação
reservada013/016/RSI100foi consumida. Não há evidência de ganho geral de
inteligência ou de desempenho contra4B.

A auditoria verificou16matrizes de saída BF16 numericamente zeradas em oito
camadas neutras,46.137.344valores. Como ficaram congeladas,60tensores anteriores
a essas saídas não podiam afetar a perda: dL/dx=WᵀdL/dy=0 quando W=0. Contagens
por família coincidem com todos os oito logs. Isso limita este escopo de treino;
não prova causa exclusiva das falhas, inclusive observadas no Qwen original.
O ganho médio da segunda visita foi{summary['mean_second_visit_gain_before']:.9f}→{summary['mean_second_visit_gain_after']:.9f};
não é reforço demonstrado nem benefício de raciocínio. NEXT_TRAINING_DESIGN.md
custa um futuro treino das saídas; não foi executado como outro ensaio.

Os pesos foram salvos antes de uma asserção do auditor exigir desligar
requires_grad. A correção recuperou os699hashes por carregamento frio, sem
repetir atualizações. Código inicial/corrigido, logs, checkpoint e otimizador
estão preservados. Uma reconexão do ambiente interrompeu a primeira execução
1024sem resultado; somente fases sem resultado final foram retomadas, com
progresso64tokens e comparação de prefixo. OOMkill observado=0.

Principal selecionado: rsi100/checkpoints/best.pt,
SHA256 {decision['selected_general_sha256']}.
Novo arquivo experimental: checkpoints/candidate.pt.gz,
SHA256 {audit['checkpoint_sha256']} ({audit['compressed_bytes']}bytes).
Restauração exata: reasoning018.restore.load_candidate. Não aplicar o loader
legado novamente depois do overlay: ele apagaria parte da adaptação.
'''
 (HERE/'REPORT.md').write_text(report)
 (HERE/'status.json').write_text(json.dumps({'status':'completed_rejected_preserve_general','model_process_active':False,'optimizer_updates':8,'checkpoint_promoted':False,'independent_validation_queried':False,'process_continues_in_background':False},indent=2)+'\n')
 for name in ['original','parent','candidate']:
  p=HERE/f'long_progress_{name}.json';d=read(p) if p.exists() else {};l=read(HERE/f'long1024_{name}.json');d.update(complete=True,new_tokens=l['new_tokens'],completed_result_file=f'long1024_{name}.json');p.write_text(json.dumps(d,indent=2)+'\n')
 print(json.dumps(rows))
if __name__=='__main__':main()
