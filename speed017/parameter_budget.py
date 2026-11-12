"""Auditable text-only dimensional budget; no initialized/trained weights."""
import json
from pathlib import Path
h=256;i=1024;vocab=248320;kv=128
embedding=vocab*h
mlp=3*h*i
linear={'qkv':3*kv*h,'z':kv*h,'ab':2*4*h,'conv7':3*kv*7,'decay_and_bias':8,'gated_norm':32,'out':h*kv,'layernorms':2*h}
full={'q_and_gate':2*h*h,'key_value':2*64*h,'out':h*h,'qk_norm':2*64,'layernorms':2*h}
mhc=24*2*(8*(2*h)+8)
parts={'tied_embedding_and_readout':embedding,'24_linear_layers':24*(sum(linear.values())+mlp),'8_full_attention_layers':8*(sum(full.values())+mlp),'48_mhc_routers':mhc,'24_two_visit_gains':48,'final_norm':h}
report={'status':'dimensional_design_only_not_trained','text_only':True,'hidden_size':h,'intermediate_size':i,'vocab_size':vocab,'full_attention_heads':4,'full_attention_head_dim':64,'full_attention_kv_heads':1,'linear_heads':4,'linear_key_value_dim_per_head':32,'physical_layers':32,'executions':56,'loop_block':[4,28],'mhc_streams':2,'conv_kernel':7,'sliding_window':256,'rope_partial_factor':0.25,'mrope_section':[3,3,2],'parts':parts,'unique_text_parameters':sum(parts.values()),'embedding_fraction':embedding/sum(parts.values()),'linear_layer_detail':linear,'full_attention_layer_detail':full,'weight_bytes_bf16_lower_bound':2*sum(parts.values()),'limits':['Budget includes every proposed text parameter and tied vocabulary projection once; excludes vision and MTP.','Existing native Rust shapes are fixed at1024 and must be generalized before this design can run.','No initialized model, trained checkpoint, measured quality or speed.','A standalone95M model cannot promise retained0.8B quality. A compatible verified drafter is a different use.']}
assert report['unique_text_parameters']==94832240
Path('speed017/reports/parameter_budget.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(parts));print(report['unique_text_parameters'])
