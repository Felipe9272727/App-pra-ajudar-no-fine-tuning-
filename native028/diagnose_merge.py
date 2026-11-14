"""Exploratory arithmetic audit; same saved factors, no training or selection."""
import argparse
from inference import *


def main(stage):
    verify_stage('evaluation')
    freeze=read('frozen_arithmetic_audit.json');assert all(file_hash(ROOT/p)==s for p,s in freeze.items())
    assert read('status.json').get('status')=='running_arithmetic_audit'
    name='reports/arithmetic_'+stage+'.json';path=H/name
    report=read(name) if path.exists() else {'stage':stage,'rows':[],
        'scope':'exploratory after validation; never a promotion or independent accuracy gate',
        'new_weight_updates':0,'inference_form':'unmerged additive FP32 factors with BF16 backbone',
        'questions':'first2 validation code tasks, nonthinking,128tokens; folded rows reused, never rerun'}
    if report.get('status')=='complete':return
    folded=read('reports/validation_'+stage+'.json');assert folded['status']=='complete'
    model,tok,meta,before,descriptors,native,factors,baseline,masters,wrapper=load_trainable()
    assert before==read('reports/preflight.json')['all699_parent_hashes']
    data,manifest=load_parts(H/'checkpoints'/stage)
    with torch.no_grad():
        for name_,p in native.items():p.copy_(data['native'][name_]);assert tensor_hash(p)==tensor_hash(data['native'][name_])
        for name_,p in factors.items():p.copy_(data['factors'][name_]);assert tensor_hash(p)==tensor_hash(data['factors'][name_])
    report['archive_sha256']=manifest['compressed_sha256'];report['all576_saved_native_factor_tensors_exact']=True
    del data,masters,baseline;wrapper.close();model.eval();model.requires_grad_(False);torch.set_grad_enabled(False);torch.set_num_threads(4);gc.collect()
    assert all(not p.requires_grad for p in model.parameters())
    for row in read('data/validation_code.json')[:2]:
        if row['id'] in {x['id'] for x in report['rows']}:continue
        out=score(generate(model,tok,row,False,128),row,'code')
        old=next(x for x in folded['rows'] if x['id']==row['id'] and not x['thinking'])
        out.update(id=row['id'],folded_cases=old['passed'],folded_total=old['total'],folded_all_passed=old['all_passed'],
            same_token_ids_as_folded=out['ids']==old['ids'],same_case_bits_as_folded=out['case_passed']==old['case_passed'])
        report['rows'].append(out);save(name,report);print('ARITHMETIC028',stage,row['id'],out['passed'],old['passed'],out['same_token_ids_as_folded'],flush=True)
    report['status']='complete';save(name,report)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('stage',choices=['sft_final','policy_final']);a=ap.parse_args();main(a.stage)
