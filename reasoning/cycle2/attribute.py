"""Linear contribution audit, explicitly short of unique causal attribution."""
import json
from pathlib import Path
import torch
from safetensors import safe_open

torch.set_num_threads(4)
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
meta=json.loads((HERE/'trial_006.json').read_text())['metadata']
directions=torch.load(HERE/'directions_006.pt',weights_only=True)
before=torch.load(ROOT/'rsi100/checkpoints/best.pt',weights_only=True)['dense_weight'].float()
after=torch.load(HERE/'checkpoints/trial_006_target.pt',weights_only=True)['dense_weight'].float()
with safe_open(ROOT/'upstream/model.safetensors-00001-of-00001.safetensors',framework='pt',device='cpu') as f:
    row=f.get_slice('model.language_model.embed_tokens.weight')[meta['bad_token']:meta['bad_token']+1].float()[0]
h=directions['target_state']
contribution=(row@before)*h
order=contribution.topk(20).indices
result={'definition':'c_j=h_j * dot(unembedding[own_bad_token], W[:,j])',
    'interpretation':'linear contribution to an unnormalised readout proxy of this MLP branch; residual stream and final RMSNorm omitted; not token probability or unique cause',
    'bad_token':meta['bad_token'],'bad_piece':meta['bad_piece'],
    'top_positive_input_coordinates':[{'column':int(j),'input':float(h[j]),'contribution_proxy':float(contribution[j])} for j in order],
    'linear_proxy_sum_before':float(row@(before@h)),
    'linear_proxy_sum_after':float(row@(after@h)),
    'unit_direction_proxy_delta':float(directions['negative_output_direction']@((after-before)@h)),
    'note_on_trial_metadata':'target_direct_bad_logit_delta is the unit-direction proxy delta, NOT an observed model logit delta',
    'weight_indices_and_actual_values':'trial_006.json metadata.largest_actual_changes; full exact matrix in checkpoints/trial_006_target.pt'}
(HERE/'attribution.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='top_positive_input_coordinates'},indent=2))
