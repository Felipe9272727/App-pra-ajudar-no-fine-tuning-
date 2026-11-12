"""Inspect frozen zero exits from exact bundled weights; no model forward/training."""
import array,json,struct,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'reasoning018';loc=json.load(open(ROOT/'speed017/model_locator.json'));audit=json.load(open(HERE/'training_complete.json'));neutral=[8,9,10,11,20,21,22,23];matrices=[]
with open(loc['path'],'rb') as f:
 f.seek(loc['offset']);assert f.read(8)==b'LSENSE01';length=struct.unpack('<Q',f.read(8))[0];manifest=json.loads(f.read(length))
 for i in neutral:
  for suffix in [('self_attn.o_proj.weight' if i%4==3 else 'linear_attn.out_proj.weight'),'mlp.down_proj.weight']:
   name=f'layers.{i}.{suffix}';spec=manifest['tensors'][name];assert spec['kind']=='bf16';f.seek(loc['offset']+spec['offset']);left=spec['bytes'];nonzero=0
   while left:
    data=f.read(min(1024*1024,left));assert data;bits=array.array('H');bits.frombytes(data);nonzero+=sum(bool(v & 0x7fff) for v in bits);left-=len(data)
   assert nonzero==0,name
   full='model.language_model.'+name;assert full not in audit['parameters'] and audit['all_699_before'][full]==audit['all_699_after'][full]
   matrices.append({'name':name,'shape':spec['shape'],'elements':spec['bytes']//2,'numerical_nonzero':0,'frozen_and_hash_identical_after018':True})
expected=[];family_counts=collections.Counter()
for n,info in audit['parameters'].items():
 if '.layers.' in n and int(n.split('.layers.')[1].split('.')[0]) in neutral and '.mhc_' not in n:
  assert info['changed_values']==0;expected.append(n);family_counts[info['family']]+=1
assert len(expected)==60
eligible=collections.Counter(v['family'] for v in audit['parameters'].values());predicted={f:eligible[f]-family_counts[f] for f in eligible};observed=[json.loads(s)['nonzero_by_family'] for s in (HERE/'steps.jsonl').read_text().splitlines()]
assert all(row==predicted for row in observed)
out={'status':'structural_limit_verified','physical_neutral_layers':neutral,'frozen_zero_exit_matrices':matrices,'zero_exit_values':sum(r['elements'] for r in matrices),'selected_parameters_mathematically_blocked_by_zero_exits':expected,'predicted_zero_gradient_tensor_count':60,'predicted_zero_gradients_by_family':dict(family_counts),'predicted_nonzero_tensors_by_family':predicted,'each_of_eight_steps_nonzero_family_counts_match_prediction':True,'names_of_actual_nonzero_gradient_union_not_saved':True,'interpretation':'If a frozen output projection W is exactly zero, dL/dx=W^T dL/dy is zero for its upstream branch parameters. Temporal state may evolve but cannot affect model output through that projection. This limits the018scope; it does not prove the sole cause of decoding failures (original Qwen also fails the256-token thinking probes).','next_hypothesis':'A separately registered pilot must train the zero exit projections or merged low-rank residuals alongside Loop/mHC/temporal weights, with general replay/retention. Current018cannot activate these frozen exits. No further weights changed in this diagnostic.'}
(HERE/'structural_diagnosis.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ['zero_exit_values','predicted_zero_gradient_tensor_count','predicted_zero_gradients_by_family','each_of_eight_steps_nonzero_family_counts_match_prediction']}))
