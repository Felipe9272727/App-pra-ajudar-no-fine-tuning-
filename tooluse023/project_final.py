"""Enforce the already-declared1%factor trust bound using FP64 audit.

The FP32 reduction underestimated its norm. Preserve original32-step artifacts;
apply one deterministic constraint projection before any candidate inference.
No new optimizer update or evaluation-dependent dose/target change.
"""
import hashlib,json,sys
from pathlib import Path
import torch
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'tooluse023'
def main():
 torch.set_num_threads(4);assert not (HERE/'results/screen_candidate.json').exists();dest=HERE/'checkpoints/projected';assert not dest.exists();dest.mkdir()
 state=torch.load(HERE/'checkpoints/latest.pt',weights_only=True);old=torch.load(ROOT/'rsi100/checkpoints/best.pt',weights_only=True)['dense_weight'];a=state['A'];b=state['B'];norm=old.double().norm();before=float((b.double()@a.double()).norm()/norm)
 factor=min(1.,.01*(1.-1e-6)/before);b=(b*factor).contiguous();after=float((b.double()@a.double()).norm()/norm);assert after<=.01
 merged=(old.float()+b@a).to(torch.bfloat16).contiguous();raw=merged.view(torch.uint8).numpy().tobytes();(dest/'down_proj.bf16.bin').write_bytes(raw);torch.save({'A':a,'B':b,'parent':'46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8'},dest/'factors.pt');state['B']=b;state['final_constraint_projection_scale']=factor;torch.save(state,dest/'training_state.pt')
 m=json.loads((HERE/'checkpoints/final.json').read_text());m.update(sha256=hashlib.sha256(raw).hexdigest(),merged_changed_values=int((merged.view(torch.int16)!=old.view(torch.int16)).sum()),FP64_relative_factor_update=after,actual_BF16_relative_weight_update=float((merged.double()-old.double()).norm()/norm),constraint_projection={'reason':'FP32 norm reduction underestimation','original_factors_relative_norm_FP64':before,'scale':factor,'no_new_gradient_steps':True,'no_candidate_outputs_seen':True,'original_weights_factors_optimizer_retained':True});(dest/'final.json').write_text(json.dumps(m,indent=2)+'\n')
 (HERE/'candidate_artifact.json').write_text(json.dumps({'metadata':'checkpoints/projected/final.json','weights':'checkpoints/projected/down_proj.bf16.bin','selection_reason':'deterministic enforcement of preregistered factor trust bound, no validation selection'},indent=2)+'\n');print('CONSTRAINT_PROJECTED',json.dumps(m['constraint_projection']),after,flush=True)
if __name__=='__main__':main()
