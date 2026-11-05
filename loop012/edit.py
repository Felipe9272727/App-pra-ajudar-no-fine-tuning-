"""One closed-form protected specialization of shared temporal gate weights."""
import sys,argparse,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from loop012.core import *
from transformers import LogitsProcessor,LogitsProcessorList

class ForceStudentPrefix(LogitsProcessor):
 def __init__(self,prefix,prompt_length):self.prefix=prefix;self.start=prompt_length
 def __call__(self,input_ids,scores):
  step=input_ids.shape[1]-self.start
  if step<len(self.prefix):
   out=torch.full_like(scores,-torch.inf);out[:,int(self.prefix[step])]=0.;return out
  return scores

@torch.inference_mode()
def collect_parent():
 verify();assert not (HERE/'ordinary_parent.pt').exists();state('collect_unlabelled_gate_inputs',True)
 m,t,p,meta=load();states={i:[] for i in LAYERS};handles=[]
 for i in LAYERS:
  def hook(module,args,i=i):states[i].append(args[0][0,-1].detach().float().clone())
  handles.append(m.model.language_model.layers[i].linear_attn.in_proj_a.register_forward_pre_hook(hook))
 for episode in json.loads((ROOT/'reasoning/multi008/inputs.json').read_text())['episodes']:
  if episode['kind']!='ordinary':continue
  m(input_ids=t(episode['input'],return_tensors='pt',add_special_tokens=False)['input_ids'],use_cache=False,logits_to_keep=1)
 for h in handles:h.remove()
 assert all(len(x)==24 for x in states.values())
 tensor_checkpoint(states,HERE/'ordinary_parent.pt')
 tensor_checkpoint({str(i):m.model.language_model.layers[i].linear_attn.in_proj_a.weight.detach().clone() for i in LAYERS},HERE/'parent_gate_weights.pt')
 state('unlabelled_gate_inputs_complete')

@torch.inference_mode()
def collect_teacher():
 verify();assert not (HERE/'teacher_gates.pt').exists();state('collect_original_gate_targets',True)
 m,t,meta=load_variant('original');payload={}
 for task in tasks(TARGETS):
  data=torch.load(ROOT/'diagnostic011/activations'/f"{task['id']}.pt",weights_only=True);step=data['suspected_point']['actual_token_index'];own=data['own_generated_token_ids'];found={};calls=[-1];handles=[]
  def rootpre(module,args,kwargs):calls[0]+=1
  handles.append(m.register_forward_pre_hook(rootpre,with_kwargs=True))
  for physical in LAYERS:
   def hook(module,args,out,physical=physical):
    if calls[0]==step:found[physical]={'output':out[0,-1].detach().float().clone(),'input':args[0][0,-1].detach().float().clone()}
   handles.append(m.model.language_model.layers[SOURCE_LAYERS[physical]].linear_attn.in_proj_a.register_forward_hook(hook))
  try:
   ids=e.cr.prompt(t,task['prompt']);m.generate(input_ids=ids,max_new_tokens=step+1,use_cache=True,do_sample=False,pad_token_id=t.eos_token_id,
    logits_processor=LogitsProcessorList([ForceStudentPrefix(own[:step],ids.shape[1])]))
  finally:
   for h in handles:h.remove()
  assert set(found)==set(LAYERS);payload[task['id']]=found;print('TEACHER_INTERNAL_GATE',task['id'],step,flush=True)
 tensor_checkpoint(payload,HERE/'teacher_gates.pt');save('teacher_gates.json',{'status':'complete','targets':TARGETS,'forced_prefix_source':'student own previously emitted wrong response only','new_reference_program_generated':False,'correct_target_token_used':False})
 state('original_gate_targets_complete')

@torch.inference_mode()
def protected_fit(W,P,X,D):
 u,s,vh=torch.linalg.svd(P,full_matrices=False);rank=int((s>s[0]*1e-5).sum())
 basis=vh[:rank];R=X-(X@basis.T)@basis
 ratios=R.norm(dim=1)/X.norm(dim=1).clamp_min(1e-12)
 info={'protected_rows':len(P),'protected_rank':rank,'target_residual_ratios':ratios.tolist()}
 if bool((ratios<.05).any()):return None,info|{'abort':'target residual below .05'}
 gram=R@R.T;ridge=.01*gram.diagonal().mean();update=D.T@torch.linalg.solve(gram+ridge*torch.eye(len(R)),R)
 norm=W.float().norm();update*=min(1.,float(.02*norm/update.norm().clamp_min(1e-12)))
 return update,info|{'requested_relative_frobenius':float(update.norm()/norm),'ridge':float(ridge)}

@torch.inference_mode()
def construct():
 verify();assert not (HERE/'construction.json').exists();teacher=torch.load(HERE/'teacher_gates.pt',weights_only=True);ordinary=torch.load(HERE/'ordinary_parent.pt',weights_only=True);weights=torch.load(HERE/'parent_gate_weights.pt',weights_only=True)
 payload={k:{'parent_sha256':PARENT_HASH,'weights':{},'parent_tensor_hashes':{},'written_tensor_hashes':{}} for k in ['target','inverse']};states={};diagnostic={};abort=False
 for i in LAYERS:
  key=f'model.language_model.layers.{i}.linear_attn.in_proj_a';P=[];X={};current={}
  for task in SCREEN:
   data=torch.load(ROOT/'diagnostic011/activations'/f'{task}.pt',weights_only=True);target_step=data['suspected_point']['actual_token_index']
   for step,snap in data['snapshots'].items():
    for visit in [0,1]:
     x=snap[(key,visit)]['input'].float().flatten()
     if task in TARGETS and step==target_step and visit==1:X[task]=x;current[task]=snap[(key,visit)]['output'].float().flatten()
     else:P.append(x)
  P=torch.stack(P+ordinary[i]);X=torch.stack([X[k] for k in TARGETS]);Y=torch.stack([current[k] for k in TARGETS]);T=torch.stack([teacher[k][i]['output'] for k in TARGETS])
  D=(T-Y).clamp(-.125,.125);D*=torch.minimum(torch.ones(len(D)),.05*Y.norm(dim=1)/D.norm(dim=1).clamp_min(1e-12))[:,None]
  W=weights[str(i)];update,info=protected_fit(W,P,X,D);states[i]={'P':P,'X':X,'parent_a':Y,'teacher_a':T,'bounded_target_delta':D}
  if update is None:abort=True;diagnostic[str(i)]=info;continue
  info['variants']={}
  for kind,sign in [('target',1.),('inverse',-1.)]:
   written=(W.float()+sign*update).to(W.dtype);delta=written.float()-W.float();protected_delta=P@delta.T;denom=(P@W.float().T).norm(dim=1).clamp_min(.1)
   rel=float(delta.norm()/W.float().norm());protectrel=float((protected_delta.norm(dim=1)/denom).max());protectabs=float(protected_delta.square().mean(1).sqrt().max())
   valid=bool(torch.isfinite(written).all()) and rel<=.025 and protectrel<=.01 and protectabs<=.01
   if not valid:abort=True
   row={'changed_values':int((written!=W).sum()),'relative_frobenius_after_bf16':rel,'max_protected_relative_l2':protectrel,'max_protected_output_rms_delta':protectabs,'guard_passed':valid,
     'target_requested_delta_mse':float(D.square().mean()),'target_delta_mse':float((X@delta.T-D).square().mean())}
   info['variants'][kind]=row;payload[kind]['weights'][str(i)]=written;payload[kind]['parent_tensor_hashes'][str(i)]=tensor_hash(W);payload[kind]['written_tensor_hashes'][str(i)]=tensor_hash(written)
  diagnostic[str(i)]=info;states[i]['update']=update
 tensor_checkpoint(states,HERE/'construction_states.pt')
 if not abort:
  for kind,obj in payload.items():tensor_checkpoint(obj,HERE/'checkpoints'/f'{kind}.pt')
 save('construction.json',{'status':'aborted' if abort else 'complete','layers':diagnostic,'parent_sha256':PARENT_HASH,'new_weight_candidate_saved':not abort,'correct_solution_or_token_supplied':False,'backward_passes':0})
 print('CONSTRUCTION','aborted' if abort else 'complete',diagnostic,flush=True);state('construction_aborted' if abort else 'candidate_constructed')

@torch.inference_mode()
def evaluate(kind,full=False):
 verify();assert json.loads((HERE/'construction.json').read_text())['status']=='complete';state(('full_' if full else 'screen_')+kind,True)
 m,t,meta=load_variant(kind);path=HERE/f'{"full" if full else "screen"}_{kind}.json';assert not path.exists();report={'status':'running','rows':[],'controls':[],'variant':kind,'model':meta}
 for task in (e.DATA['search']+e.DATA['guard'] if full else tasks(SCREEN)):
  report['rows']+=e.coding(m,t,[task]);save(path.name,report)
 if full:
  report['controls']=e.quality(m,t,e.DATA['search_controls']);report['anchor_nll']=e.cr.likelihood(m,t,e.DATA['anchors'],anchors=True)['mean_nll']
 report.update(status='complete',tasks_passed=sum(r['all_passed'] for r in report['rows']),cases_passed=sum(r['passed'] for r in report['rows']));save(path.name,report);state(path.stem+'_complete')

def decide():
 from policy import flatten
 construction=json.loads((HERE/'construction.json').read_text());decision={'selected':'parent','checkpoint_promoted':False,'validation_consumed':False,'eligible_full':False}
 if construction['status']!='complete':decision['reason']='construction stability gate failed'
 else:
  old=[r for r in parent_rows() if r['id'] in SCREEN];new=json.loads((HERE/'screen_target.json').read_text())['rows'];a=flatten(new);b=flatten(old);assert set(a)==set(b)
  wins=sum(a[k] and not b[k] for k in b);losses=sum(b[k] and not a[k] for k in b)
  complete_gain=sum(r['all_passed'] for r in new)>sum(r['all_passed'] for r in old)
  decision.update(case_wins=wins,case_losses=losses,complete_task_gain=complete_gain,eligible_full=bool(complete_gain and losses==0),reason='full gate required' if complete_gain and losses==0 else 'no complete-task gain with retention on screen')
 save('decision.json',decision);print('DECISION',decision,flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['collect_parent','collect_teacher','construct','screen','full','decide']);p.add_argument('variant',nargs='?');a=p.parse_args()
 if a.phase in ['screen','full']:evaluate(a.variant,a.phase=='full')
 else:globals()[a.phase]()
