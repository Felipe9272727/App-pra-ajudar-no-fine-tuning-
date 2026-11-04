"""Localize task-selective MLP channels, intervene on weights, test transfer."""
import argparse,collections,hashlib,importlib.util,json,os,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'code_focus';CK=HERE/'checkpoints';OUT=ROOT/'focus_output'
sys.path.insert(0,str(ROOT/'code_rsi'))
import runtime as cr
from checkpoint_io import tensor_checkpoint
from selectivity import choose_channels,write_columns
import torch
spec=importlib.util.spec_from_file_location('focus_publish',HERE/'publish.py');pub=importlib.util.module_from_spec(spec);spec.loader.exec_module(pub)
DATA=json.loads((HERE/'data.json').read_text());HASH=cr.file_hash(HERE/'data.json');LAYERS=DATA['layers']
VARIANTS=['parent']+[f'{kind}_{layer}' for layer in LAYERS for kind in ['ablate_target','ablate_control','boost','attenuate']]
def save(name,j):cr.atomic_json(HERE/name,j)
def state(**kw):
 j=json.loads((HERE/'status.json').read_text());j.update(kw);j['updated_unix']=time.time();save('status.json',j)
def provenance():return {'data_sha256':HASH,'source_sha':os.environ.get('GITHUB_SHA'),
 'code_hashes':{str(p.relative_to(ROOT)):cr.file_hash(p) for p in [HERE/'focus.py',HERE/'selectivity.py',ROOT/'code_rsi/runtime.py',ROOT/'code_rsi/sandbox.py',ROOT/'v2_adaptation/native_runtime.py']},
 'protocol':{'greedy':True,'max_new_tokens':160,'feedback_at_evaluation':False,'cpu_threads':4,'image':os.environ.get('CODE_IMAGE')}}
def export(stage,weights=False):
 paths=list(HERE.glob('*.json'))+[ROOT/'CODE_FOCUS_REPORT.md']
 if weights:paths+=list(CK.glob('*.pt'))
 for p in paths:
  if p.exists():
   q=OUT/stage/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
def import_parent():
 # Read only the frozen selection, never use the preceding final-test scores.
 branch='refs/heads/codex/liquid-sense-rsi100-20261104'
 subprocess.run(['git','fetch','origin',branch],check=True)
 commit=subprocess.check_output(['git','rev-parse','FETCH_HEAD'],text=True).strip()
 frozen=json.loads(subprocess.check_output(['git','show','FETCH_HEAD:rsi100/frozen.json']))
 assert not frozen['selection_used_heldout'] and frozen['selected'] in ['best','baseline']
 assert frozen['data_sha256']==cr.file_hash(ROOT/'rsi100/data.json')
 raw=subprocess.check_output(['git','show',f"FETCH_HEAD:rsi100/checkpoints/{frozen['selected']}.pt"])
 assert hashlib.sha256(raw).hexdigest()==frozen['selected_sha256']
 CK.mkdir(parents=True,exist_ok=True);(CK/'parent_checkpoint.pt').write_bytes(raw)
 save('parent_import.json',{'commit':commit,'frozen_selection':frozen,'checkpoint_sha256':hashlib.sha256(raw).hexdigest(),'final_test_scores_read':False})
 pub.publish('import frozen RSI100 parent without final-test selection')
@torch.inference_mode()
def load(variant='parent'):
 if variant=='original':return cr.load('original')[0],{'variant':'original'}
 info=json.loads((HERE/'parent_import.json').read_text());path=CK/'parent_checkpoint.pt'
 assert cr.file_hash(path)==info['checkpoint_sha256']
 parent=torch.load(path,weights_only=True);assert parent['data_sha256']==cr.file_hash(ROOT/'rsi100/data.json')
 model,_=cr.load('baseline');text=model.model.language_model
 text.layers[31].mlp.down_proj.weight.copy_(parent['dense_weight'])
 for i,h in parent['history'].items():text.layers[int(i)].linear_attn.conv1d.weight[:,:,:3].copy_(h)
 for key,b in parent['router_bias'].items():
  i,name=key.split('.');getattr(text.layers[int(i)],name).bias.copy_(b)
 passes=parent['passes'];g=parent['late_gain'];cr.configure_loops(model,passes,[1-g]+[g/(passes-1)]*(passes-1))
 meta={'variant':variant,'parent_checkpoint_sha256':info['checkpoint_sha256'],'patch_sha256':None}
 if variant!='parent':
  p=CK/f'{variant}.pt';patch=torch.load(p,weights_only=True)
  assert patch['data_sha256']==HASH and patch['parent_checkpoint_sha256']==info['checkpoint_sha256']
  indices=patch['indices'];weight=text.layers[patch['layer']].mlp.down_proj.weight
  assert len(indices)==DATA['channels'] and len(indices.unique())==len(indices)
  assert patch['columns_weight'].shape==(weight.shape[0],len(indices))
  # Advanced indexing copy_ would edit a temporary. index_copy_ writes the parameter.
  write_columns(weight,indices,patch['columns_weight']);meta['patch_sha256']=cr.file_hash(p)
 meta['architecture']=cr.check_architecture(model,passes)
 return model,meta

@torch.inference_mode()
def collect():
 assert not (HERE/'frozen.json').exists()
 if not (HERE/'parent_import.json').exists():import_parent()
 model,meta=load();tok=cr.tokenizer();captures={};handles=[];stats={'code':{i:[] for i in LAYERS},'prose':{i:[] for i in LAYERS}}
 for i in LAYERS:
  def hook(module,inputs,i=i):captures[i]=inputs[0][0,-1].detach().float().abs().cpu()
  handles.append(model.model.language_model.layers[i].mlp.down_proj.register_forward_pre_hook(hook))
 lengths={}
 try:
  for domain in ['code','prose']:
   lengths[domain]=[]
   for text in DATA[domain+'_prompts']:
    ids=cr.prompt(tok,text);captures.clear();model(input_ids=ids,use_cache=False,logits_to_keep=1)
    assert set(captures)==set(LAYERS)
    for i in LAYERS:stats[domain][i].append(captures[i])
    lengths[domain].append(ids.shape[1])
 finally:
  for h in handles:h.remove()
 tensor_checkpoint({'activations':{d:{str(i):torch.stack(v) for i,v in values.items()} for d,values in stats.items()},'parent_checkpoint_sha256':meta['parent_checkpoint_sha256'],'data_sha256':HASH},CK/'features.pt')
 localization={'layers':{},'prompt_token_lengths':lengths,'data_sha256':HASH,
  'scope':'last prompt-token MLP activity, final visit; candidate task selectivity, not a proven coding module','reference_solutions_used':False}
 archive=[]
 for i in LAYERS:
  code=torch.stack(stats['code'][i]).mean(0);prose=torch.stack(stats['prose'][i]).mean(0)
  target,control,scores=choose_channels(code.tolist(),prose.tolist(),DATA['channels'],DATA['seed']+i)
  localization['layers'][str(i)]={'selected_indices':target,'control_indices':control,'selected_log_ratios':[scores[j] for j in target],'code_mean':[float(code[j]) for j in target],'prose_mean':[float(prose[j]) for j in target]}
  weight=model.model.language_model.layers[i].mlp.down_proj.weight
  for kind,factor in DATA['protocol']['scales'].items():
   name=f'{kind}_{i}';indices=torch.tensor(control if kind=='ablate_control' else target,dtype=torch.long)
   columns=(weight.index_select(1,indices).float()*factor).to(weight.dtype)
   p=CK/f'{name}.pt'
   tensor_checkpoint({'indices':indices,'columns_weight':columns,'layer':i,'kind':kind,'factor':factor,'data_sha256':HASH,'parent_checkpoint_sha256':meta['parent_checkpoint_sha256'],'runtime_adapter':False,'backward_passes':0},p)
   archive.append({'id':name,'layer':i,'kind':kind,'factor':factor,'patch_sha256':cr.file_hash(p),
    'changed_bf16_values':int((columns.view(torch.int16)!=weight.index_select(1,indices).view(torch.int16)).sum()),'promotion_allowed':kind in ['boost','attenuate']})
 save('localization.json',localization);save('archive.json',{'candidates':archive,'data_sha256':HASH,'heldout_used':False})
 state(status='awaiting_development',model_process_active=False)
 pub.publish('save localized channels, activity controls and direct column patches');export('collection',True)

@torch.inference_mode()
def evaluate(variant,phase,shard=None):
 model,meta=load(variant);tok=cr.tokenizer()
 split={'development':'development','validation':'validation','final':'heldout'}[phase];rows=DATA[split]
 if phase=='final':
  f=json.loads((HERE/'frozen.json').read_text());assert not f['selection_used_heldout'] and variant in f['final_variants'] and shard in [0,1]
  rows=rows[shard::2];meta['frozen_sha256']=cr.file_hash(HERE/'frozen.json')
  if variant==f['selected'] and variant!='parent':assert meta['patch_sha256']==f['patch_sha256']
 results=[]
 for row in rows:
  out=cr.generate(model,tok,row['prompt']);out.pop('trace');score=cr.evaluate(out['output'],row)
  bits=score.get('case_passed',[False]*len(row['cases']));assert sum(bits)==score['passed']
  results.append({'id':row['id'],**out,**score,'case_passed':bits})
  print('FOCUS_CODE',variant,phase,row['id'],score['passed'],score['total'],flush=True)
 result={**meta,**provenance(),'status':'complete','rows':results,'tasks_passed':sum(r['all_passed'] for r in results),
  'tests_passed':sum(r['passed'] for r in results),'tests_total':sum(r['total'] for r in results),'total':len(results)}
 if phase!='final' or shard==0:
  controls=DATA['development_controls'] if phase=='development' else DATA['controls']['val' if phase=='validation' else 'test'];controlled=[]
  for row in controls:
   out=cr.generate(model,tok,row['question'],max_tokens=32);ok,_=cr.grade(out['output'],row)
   controlled.append({'id':row['id'],'correct':ok,'output':out['output']})
  result['controls']=controlled;result['control_bits']=[r['correct'] for r in controlled]
  result['anchor_nll']=cr.likelihood(model,tok,DATA['anchors'],anchors=True)['mean_nll']
 suffix=variant+(f'_{shard}' if phase=='final' else '')
 save(f'{phase}_{suffix}.json',result);export(f'{phase}-{suffix}')

def improved(result,base):
 if result['tasks_passed']<=base['tasks_passed']:return False
 if len(result['rows'])!=len(base['rows']):raise ValueError('Task set mismatch')
 for a,b in zip(base['rows'],result['rows']):
  assert a['id']==b['id'] and len(a['case_passed'])==len(b['case_passed'])
  if any(x and not y for x,y in zip(a['case_passed'],b['case_passed'])):return False
 return all(not x or y for x,y in zip(base['control_bits'],result['control_bits'])) and result['anchor_nll']<=base['anchor_nll']+1e-6

def select(phase):
 base=json.loads((HERE/f'{phase}_parent.json').read_text());assert base['status']=='complete' and base['data_sha256']==HASH
 archive=json.loads((HERE/'archive.json').read_text());eligible=[]
 queue=VARIANTS[1:] if phase=='development' else json.loads((HERE/'validation_queue.json').read_text())['variants'][1:]
 for key in queue:
  c=next(x for x in archive['candidates'] if x['id']==key);result=json.loads((HERE/f'{phase}_{key}.json').read_text())
  assert result['status']=='complete' and result['data_sha256']==HASH and result['patch_sha256']==c['patch_sha256']
  assert result['code_hashes']==base['code_hashes'] and result['protocol']==base['protocol'] and result['parent_checkpoint_sha256']==base['parent_checkpoint_sha256']
  c[phase]={k:result[k] for k in ['tasks_passed','tests_passed','total','control_bits','anchor_nll']}
  c['passes_'+phase]=c['promotion_allowed'] and improved(result,base)
  if c['passes_'+phase]:eligible.append(c)
 eligible.sort(key=lambda c:(-c[phase]['tasks_passed'],-c[phase]['tests_passed'],c['changed_bf16_values'],c['id']))
 save('archive.json',archive)
 if phase=='development':
  save('validation_queue.json',{'variants':['parent']+[c['id'] for c in eligible[:2]],'heldout_used':False})
  state(status='awaiting_validation');pub.publish('save localized intervention results and transfer queue');export('shortlist',True)
 else:
  selected=eligible[0]['id'] if eligible else 'parent'
  save('frozen.json',{'selected':selected,'patch_sha256':eligible[0]['patch_sha256'] if eligible else None,
   'final_variants':['original','parent']+([selected] if selected!='parent' else []),'data_sha256':HASH,'selection_used_heldout':False,'frozen_unix':time.time()})
  state(status='frozen_for_final',selected=selected);pub.publish('freeze localized coding edit before final test');export('frozen',True)

def report():
 frozen=json.loads((HERE/'frozen.json').read_text());scores={}
 for v in frozen['final_variants']:
  parts=[json.loads((HERE/f'final_{v}_{i}.json').read_text()) for i in range(2)]
  for p in parts:assert p['status']=='complete' and p['frozen_sha256']==cr.file_hash(HERE/'frozen.json') and p['data_sha256']==HASH
  for k in ['variant','patch_sha256','protocol','code_hashes']:assert parts[0].get(k)==parts[1].get(k),k
  rows=parts[0]['rows']+parts[1]['rows'];assert len(rows)==len(DATA['heldout']) and {r['id'] for r in rows}=={r['id'] for r in DATA['heldout']}
  scores[v]={'tasks_passed':sum(r['all_passed'] for r in rows),'total':len(rows),'tests_passed':sum(r['passed'] for r in rows),'tests_total':sum(r['total'] for r in rows),'controls_correct':sum(parts[0]['control_bits'])}
 archive=json.loads((HERE/'archive.json').read_text())
 effects={}
 base=json.loads((HERE/'development_parent.json').read_text())
 for layer in LAYERS:
  target=next(c for c in archive['candidates'] if c['id']==f'ablate_target_{layer}')['development']
  control=next(c for c in archive['candidates'] if c['id']==f'ablate_control_{layer}')['development']
  effects[str(layer)]={'target_task_drop':base['tasks_passed']-target['tasks_passed'],
   'control_task_drop':base['tasks_passed']-control['tasks_passed'],
   'target_general_controls':sum(target['control_bits']),'control_general_controls':sum(control['control_bits'])}
 summary={'status':'complete','selected':frozen['selected'],'scores':scores,'ablation_effects':effects,'data_sha256':HASH,'backward_passes':0,'reference_answers_in_prompts':False,'coding_module_identified':False}
 save('summary.json',summary)
 archive=json.loads((HERE/'archive.json').read_text());lines=['# Edição localizada para programação','',
  'Este piloto identifica grupos candidatos por atividade, aplica intervenções diretas e compara com controles de atividade semelhante. Não identifica um módulo isolado de programação.','',
  f"Escolha após validação: {frozen['selected']}. Sem melhoria aprovada, preservar o pai congelado da busca de 100 rodadas.",'',
  '| Modelo | Tarefas completas | Testes individuais | Controles |','|---|---:|---:|---:|']
 for v,s in scores.items():lines.append(f"| {v} | {s['tasks_passed']}/{s['total']} | {s['tests_passed']}/{s['tests_total']} | {s['controls_correct']}/{len(DATA['controls']['test'])} |")
 lines+=['','## Intervenções em desenvolvimento','', '| Variante | Canal/grupo | Tarefas completas | Testes individuais | Elegível |','|---|---|---:|---:|---|']
 for c in archive['candidates']:
  d=c['development'];lines.append(f"| {c['id']} | 64 canais na camada {c['layer']} | {d['tasks_passed']}/{d['total']} | {d['tests_passed']} | {c['passes_development']} |")
 lines+=['','Seleção por diferença de ativação no último token do prompt, em quatro camadas físicas. Prompts de código e prosa não são perfeitamente pareados em tamanho ou assunto; os grupos são hipóteses. '
  'Ablatar grupos-alvo e controles não prova uma função exclusiva, e melhorar aparência de código não demonstra correção algorítmica.','',
  'Somente amplificação/atenuação podem ser promovidas; ablações são controles diagnósticos. Cada patch sobrescreve colunas existentes da MLP via index_copy_, sem adaptador ou gradientes. '
  'Convoluções Liquid, mHC e loops ativos do pai permanecem presentes. Validação e teste são tarefas novas; oito funções finais não permitem alegar liderança.','',
  'A análise manual dos erros foi registrada para auditoria e nunca fornecida como solução ao modelo. O conjunto observado de 16 funções é desenvolvimento, não teste final. '
  'Pesos do pai foram importados da seleção congelada RSI100, sem consultar suas pontuações de teste para escolher pesos.','',
  'Estado: concluído e parado. Referências e limites em code_focus/PROTOCOL.md.']
 (ROOT/'CODE_FOCUS_REPORT.md').write_text('\n'.join(lines)+'\n');state(status='complete',model_process_active=False,final_test_evaluated=True,selected=frozen['selected']);export('report')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['collect','development','shortlist','validation','freeze','final','report','matrix']);p.add_argument('--variant');p.add_argument('--shard',type=int);a=p.parse_args()
 if a.phase=='collect':collect()
 elif a.phase in ['development','validation','final']:evaluate(a.variant,a.phase,a.shard)
 elif a.phase=='shortlist':select('development')
 elif a.phase=='freeze':select('validation')
 elif a.phase=='report':report()
 else:
  print(json.dumps(json.loads((HERE/'frozen.json').read_text())['final_variants'] if (HERE/'frozen.json').exists() else json.loads((HERE/'validation_queue.json').read_text())['variants'] if (HERE/'validation_queue.json').exists() else VARIANTS))
