"""One hundred finite forward-only weight-search rounds, with strict rollback."""
import argparse,copy,json,os,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'rsi100'
sys.path.insert(0,str(ROOT/'code_rsi'))
import runtime as cr
from checkpoint_io import tensor_checkpoint
from policy import flatten,dominates,accept
# Import this directory explicitly: code_rsi also has a publisher.
import importlib.util
spec=importlib.util.spec_from_file_location('r100_publish',HERE/'publish.py');pub=importlib.util.module_from_spec(spec);spec.loader.exec_module(pub)
from mutation import propose
import torch
DATA=json.loads((HERE/'data.json').read_text());DATA_HASH=cr.file_hash(HERE/'data.json')
CK=HERE/'checkpoints';REPORTS=ROOT/'rsi100_output'

def save(name,obj):cr.atomic_json(HERE/name,obj)
def state(**kw):
 p=HERE/'status.json';j=json.loads(p.read_text());j.update(kw);j['updated_unix']=time.time();save('status.json',j)
def provenance():
 return {'data_sha256':DATA_HASH,'source_commit':os.environ.get('GITHUB_SHA'),
  'code_sha256':{str(p.relative_to(ROOT)):cr.file_hash(p) for p in [HERE/'engine.py',HERE/'mutation.py',HERE/'policy.py',ROOT/'code_rsi/runtime.py',ROOT/'code_rsi/sandbox.py',ROOT/'v2_adaptation/native_runtime.py']},
  'protocol':{'max_new_tokens':160,'greedy':True,'feedback_at_evaluation':False,'cpu_threads':4,'code_image':os.environ.get('CODE_IMAGE')}}
def snapshot(model):
 text=model.model.language_model
 return {'dense_weight':text.layers[31].mlp.down_proj.weight.detach().clone(),
  'history':{str(i):l.linear_attn.conv1d.weight[:,:,:3].detach().clone() for i,l in enumerate(text.layers) if hasattr(l,'linear_attn')},
  'router_bias':{f'{i}.{name}':getattr(l,name).bias.detach().clone() for i,l in enumerate(text.layers) if 4<=i<28 for name in ['mhc_attn','mhc_ffn']},
  'passes':2,'late_gain':.05,'data_sha256':DATA_HASH,'round':0,'backward_passes':0}
@torch.inference_mode()
def apply(model,checkpoint):
 assert checkpoint['data_sha256']==DATA_HASH
 text=model.model.language_model;text.layers[31].mlp.down_proj.weight.copy_(checkpoint['dense_weight'])
 for key,h in checkpoint['history'].items():text.layers[int(key)].linear_attn.conv1d.weight[:,:,:3].copy_(h)
 for key,b in checkpoint['router_bias'].items():
  i,name=key.split('.');getattr(text.layers[int(i)],name).bias.copy_(b)
 passes=checkpoint['passes'];g=checkpoint['late_gain']
 return cr.configure_loops(model,passes,[1-g]+[g/(passes-1)]*(passes-1))
@torch.inference_mode()
def coding(model,tok,rows):
 out=[]
 for task in rows:
  generated=cr.generate(model,tok,task['prompt']);generated.pop('trace')
  result=cr.evaluate(generated['output'],task)
  bits=result.get('case_passed',[False]*len(task['cases']))
  assert len(bits)==len(task['cases']) and sum(bits)==result['passed']
  out.append({'id':task['id'],**generated,**result,'case_passed':bits})
  print('EVAL',task['id'],result['passed'],result['total'],flush=True)
 return out
@torch.inference_mode()
def quality(model,tok,rows):
 results=[]
 for row in rows:
  out=cr.generate(model,tok,row['question'],max_tokens=32);ok,_=cr.grade(out['output'],row)
  results.append({'id':row['id'],'output':out['output'],'correct':ok})
 return results
@torch.inference_mode()
def full_score(model,tok):
 rows=coding(model,tok,DATA['search']+DATA['guard'])
 controls=quality(model,tok,DATA['search_controls']);anchor=cr.likelihood(model,tok,DATA['anchors'],anchors=True)['mean_nll']
 return {'rows':rows,'control_bits':[x['correct'] for x in controls],'controls':controls,'anchor_nll':anchor,**provenance()}
def read_checkpoint(name):
 path=CK/name;payload=torch.load(path,weights_only=True);assert payload['data_sha256']==DATA_HASH;return payload

def export(stage):
 import shutil
 dest=REPORTS/stage
 paths=list(HERE.glob('*.json'))+[ROOT/'RSI100_REPORT.md']
 if stage=='frozen' or json.loads((HERE/'status.json').read_text())['status']=='interrupted':
  paths += [CK/'baseline.pt',CK/'best.pt']
 for p in paths:
  if p.exists():
   q=dest/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)

@torch.inference_mode()
def chunk(start,stop):
 assert 1<=start<=stop<=100 and stop-start<10 and not (HERE/'frozen.json').exists()
 status=json.loads((HERE/'status.json').read_text());done=status['rounds_completed']
 if done>=stop:print('CHUNK_ALREADY_SAVED',done);return
 assert start-1<=done<stop
 model,_=cr.load('baseline');tok=cr.tokenizer();fresh=False
 if not (CK/'baseline.pt').exists():
  base=snapshot(model);tensor_checkpoint(base,CK/'baseline.pt');tensor_checkpoint(base,CK/'best.pt')
  measured=full_score(model,tok);fresh=True;save('baseline_metrics.json',measured);save('best_metrics.json',measured)
  state(status='initialized',model_process_active=False,best_round=0)
  pub.publish('save initial active hybrid and reward baseline')
 baseline=read_checkpoint('baseline.pt');best=read_checkpoint('best.pt');apply(model,best)
 # Recalibrate on this runner. Never credit hardware changes as improvements.
 prior=measured if fresh else full_score(model,tok)
 saved=json.loads((HERE/'best_metrics.json').read_text())
 assert flatten(prior['rows'])==flatten(saved['rows']) and prior['control_bits']==saved['control_bits'],'Incumbent changed outcomes across runners; stop'
 save('best_metrics.json',prior)
 direction=torch.load(ROOT/'code_rsi/checkpoints/activation_summary.pt',weights_only=True)['direction']
 tasks={r['id']:r for r in DATA['search']+DATA['guard']}
 for number in range(done+1,stop+1):
  state(status='searching',model_process_active=True,current_round=number)
  proposal,metadata=propose(best,baseline,direction,number,DATA['seed'])
  arch=apply(model,proposal)
  if proposal['passes']!=best['passes']:cr.cache_check(model,tok,proposal['passes'])
  hard=[r['id'] for r in prior['rows'] if not r['all_passed']] or list(tasks)
  keys=[hard[(number-1)%len(hard)]]
  if len(hard)>1:keys.append(hard[number%len(hard)])
  screened=coding(model,tok,[tasks[k] for k in keys])
  previous_screen=[r for r in prior['rows'] if r['id'] in keys]
  promising=dominates(flatten(screened),flatten(previous_screen))
  record={'round':number,'parent_best_round':best['round'],'proposal':metadata,'architecture':arch,
   'incumbent_anchor_nll':prior['anchor_nll'],'incumbent_control_bits':prior['control_bits'],
   'incumbent_case_bits':{r['id']:r['case_passed'] for r in prior['rows']},
   'screen':screened,'accepted':False,'reason':'no monotone screen gain','heldout_used':False,**provenance()}
  if promising:
   measured=full_score(model,tok);accepted,reason=accept(measured,prior)
   record.update(full_evaluation=measured,accepted=accepted,reason=reason)
   if accepted:
    tensor_checkpoint(proposal,CK/f'accepted_{number:03d}.pt');tensor_checkpoint(proposal,CK/'best.pt')
    best=proposal;prior=measured;save('best_metrics.json',measured)
  # Bad and tied proposals never enter the deployed checkpoint or Git weights.
  # Restore even after success, so the replay path is exercised every round.
  apply(model,best);del proposal
  save(f'round_{number:03d}.json',record)
  state(status='round_saved',rounds_completed=number,best_round=best['round'],
    accepted_rounds=sum(json.loads(p.read_text())['accepted'] for p in HERE.glob('round_*.json')),
    rejected_rounds=number-sum(json.loads(p.read_text())['accepted'] for p in HERE.glob('round_*.json')),
    model_process_active=False,current_round=None)
  pub.publish(f'round {number:03d} '+('accept' if record['accepted'] else 'reject and restore best'))
  print('ROUND',number,'ACCEPT' if record['accepted'] else 'REJECT',record['reason'],flush=True)
 state(status='search_complete' if stop==100 else 'awaiting_next_chunk',model_process_active=False)
 pub.publish(f'chunk through round {stop:03d} complete')
 export(f'chunk-{stop}')

@torch.inference_mode()
def freeze():
 status=json.loads((HERE/'status.json').read_text());assert status['rounds_completed']==100
 assert not (HERE/'frozen.json').exists()
 model,_=cr.load('baseline');tok=cr.tokenizer();results={}
 for variant in ['baseline','best']:
  checkpoint=read_checkpoint(variant+'.pt');apply(model,checkpoint)
  rows=coding(model,tok,DATA['validation']);controls=quality(model,tok,DATA['controls']['val'])
  anchors=cr.likelihood(model,tok,DATA['anchors'],anchors=True)['mean_nll']
  results[variant]={'rows':rows,'control_bits':[x['correct'] for x in controls],'controls':controls,'anchor_nll':anchors,**provenance()}
  save('validation_'+variant+'.json',results[variant])
 a,b=results['baseline'],results['best']
 gain=dominates(flatten(b['rows']),flatten(a['rows']))
 taskgain=sum(r['all_passed'] for r in b['rows'])>sum(r['all_passed'] for r in a['rows'])
 preserves=all(not x or y for x,y in zip(a['control_bits'],b['control_bits'])) and b['anchor_nll']<=a['anchor_nll']+1e-6
 promoted=bool(gain and taskgain and preserves)
 save('frozen.json',{'selected':'best' if promoted else 'baseline','search_best_round':status['best_round'],
  'selected_sha256':cr.file_hash(CK/('best.pt' if promoted else 'baseline.pt')),
  'final_variants':['original','baseline']+(['best'] if promoted else []),
  'selection_used_heldout':False,'data_sha256':DATA_HASH,'frozen_unix':time.time(),
  'reason':'new validation confirms pass-at-one gain and no regression' if promoted else 'search changes did not pass fresh transfer gate; deploy baseline'})
 state(status='frozen_for_final',selected='best' if promoted else 'baseline',model_process_active=False)
 pub.publish('freeze transfer decision before final test');export('frozen')

@torch.inference_mode()
def final(variant,shard):
 frozen=json.loads((HERE/'frozen.json').read_text());assert not frozen['selection_used_heldout'] and variant in frozen['final_variants'] and shard in [0,1]
 model,_=cr.load('original' if variant=='original' else 'baseline');tok=cr.tokenizer()
 patch=None
 if variant!='original':
  checkpoint=read_checkpoint(variant+'.pt');apply(model,checkpoint);patch=cr.file_hash(CK/(variant+'.pt'))
  if variant==frozen['selected']:assert patch==frozen['selected_sha256']
 rows=coding(model,tok,DATA['heldout'][shard::2])
 result={'variant':variant,'shard':shard,'shards':2,'rows':rows,'patch_sha256':patch,
  'frozen_sha256':cr.file_hash(HERE/'frozen.json'),'status':'complete',**provenance()}
 if shard==0:result['controls']=quality(model,tok,DATA['controls']['test'])
 save(f'final_{variant}_{shard}.json',result);export(f'final-{variant}-{shard}')

def report():
 frozen=json.loads((HERE/'frozen.json').read_text());scores={}
 for variant in frozen['final_variants']:
  parts=[json.loads((HERE/f'final_{variant}_{i}.json').read_text()) for i in range(2)]
  for p in parts:assert p['status']=='complete' and p['frozen_sha256']==cr.file_hash(HERE/'frozen.json') and p['data_sha256']==DATA_HASH
  for k in ['variant','code_sha256','protocol','patch_sha256']:assert parts[0][k]==parts[1][k],k
  rows=parts[0]['rows']+parts[1]['rows'];assert len(rows)==len(DATA['heldout']) and {r['id'] for r in rows}=={r['id'] for r in DATA['heldout']}
  scores[variant]={'tasks_passed':sum(r['all_passed'] for r in rows),'total':len(rows),
   'tests_passed':sum(r['passed'] for r in rows),'tests_total':sum(r['total'] for r in rows),
   'controls_correct':sum(r['correct'] for r in parts[0]['controls']),'controls_total':len(parts[0]['controls'])}
 status=json.loads((HERE/'status.json').read_text());assert status['rounds_completed']==100
 summary={'status':'complete','rounds_completed':100,'accepted_rounds':status['accepted_rounds'],
  'rejected_rounds':status['rejected_rounds'],'selected':frozen['selected'],'search_best_round':status['best_round'],
  'scores':scores,'backward_passes':0,'selection_used_heldout':False,'data_sha256':DATA_HASH}
 save('summary.json',summary)
 lines=['# liquid sense 0.8 b LOOP — 100 rodadas sem gradientes','',
  f"Concluídas 100 propostas: {status['accepted_rounds']} aceitas e {status['rejected_rounds']} descartadas. Melhor rodada de busca: {status['best_round']}.",'',
  'As 100 rodadas são tentativas de editar pesos, não 100 passagens internas. O híbrido mantém 2/3/4 passagens, mHC e os operadores Liquid ativos. '
  'Esta é adaptação por busca em parâmetros com recompensa de execução; não usa backpropagation nem soluções-alvo nos prompts.','',
  f"Escolha final após validação nova: {frozen['selected']}. {frozen['reason']}",'',
  '| Modelo | Tarefas completas | Testes individuais | Controles |','|---|---:|---:|---:|']
 for v,s in scores.items():lines.append(f"| {v} | {s['tasks_passed']}/{s['total']} | {s['tests_passed']}/{s['tests_total']} | {s['controls_correct']}/{s['controls_total']} |")
 lines+=['','As tarefas de busca e guarda já eram observadas no piloto anterior e foram reutilizadas explicitamente para otimizar. '
  'Melhorar essa recompensa pode ser sobreajuste. Validação e teste final novos são tarefas diferentes; teste não escolhe pesos. '
  'Dezesseis tarefas finais e oito controles são um piloto pequeno, não prova de liderança em programação ou de preservação geral.','',
  'Pesos rejeitados só existiram temporariamente em memória, foram descartados e o melhor checkpoint foi restaurado. '
  'Métricas, seeds e motivos de rejeição permanecem no Git. Checkpoints aceitos e base anterior continuam preservados.','',
  'Matrizes Qwen com topologia compatível inspirada em SenseNova e operadores Liquid, não os modelos completos. '
  'Roteadores aprendem apenas alterações de bias nesta busca; pesos contextuais continuam na inicialização. '
  'Oito camadas inseridas mantêm saída neutra. Base nominal 0,8B, híbrido aproximadamente 1,02B.','',
  'Estado: concluído e parado. Protocolo em rsi100/PROTOCOL.md.']
 (ROOT/'RSI100_REPORT.md').write_text('\n'.join(lines)+'\n')
 state(status='complete',model_process_active=False,final_test_evaluated=True,selected=frozen['selected'])
 export('report');print(json.dumps(summary,indent=2),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['chunk','freeze','matrix','final','report']);p.add_argument('--start',type=int);p.add_argument('--stop',type=int);p.add_argument('--variant');p.add_argument('--shard',type=int);a=p.parse_args()
 if a.phase=='chunk':
  try:chunk(a.start,a.stop)
  except Exception:
   state(status='interrupted',model_process_active=False);export(f'chunk-{a.stop}');raise
 elif a.phase=='freeze':freeze()
 elif a.phase=='matrix':print(json.dumps(json.loads((HERE/'frozen.json').read_text())['final_variants']))
 elif a.phase=='final':final(a.variant,a.shard)
 else:report()
