"""Capture all tensor participation during seven actual autoregressive responses."""
import argparse,json,sys,time,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'reasoning'))
from runtime_helpers import load,e,torch,PARENT_HASH,tensor_checkpoint,tasks
from diagnostic011.instrument import Observer,ParameterAccess,COLS
from native010.native_runtime import tensor_hash
from diagnostic011.metric import summarize,compare

ERRORS=['prefix_sums','overlap_count','run_lengths','rotate_right','longest_run'];GUARDS=['sum_abs','binary_search']
MARKERS={'prefix_sums':'sum([x for x in xs])','overlap_count':'i += len(sub)',
 'run_lengths':'result.append(len(s[i:i+1]))','rotate_right':'xs[k:] + xs[:k]',
 'longest_run':'return max_len if current_len > 0 else 0'}
PROTOCOL={'max_new_tokens':160,'greedy':True,'thinking':False,'cpu_threads':4,'precision':'bfloat16_backbone_fp32_routes',
 'data_sha256':e.DATA_HASH,'judge_sha256':e.cr.file_hash(ROOT/'local_cpu/sandbox.py'),'gold_in_model_input':False}

def save(name,obj):e.cr.atomic_json(HERE/name,obj)
def state(phase,active=False):save('status.json',{'status':phase,'model_process_active':active,'parent_sha256':PARENT_HASH,'weights_changed':False,'backward_passes':0,'independent_validation_consumed':False})
def reference_rows():return {r['id']:r for r in json.loads((ROOT/'reasoning/cycle2/trial_006_parent_full.json').read_text())['rows']}
def verify():
    f=json.loads((HERE/'frozen.json').read_text())
    for p,h in f['files'].items():assert e.cr.file_hash(ROOT/p)==h,p

def initialize():
    assert not (HERE/'frozen.json').exists()
    paths=['diagnostic011/PROTOCOL.md','diagnostic011/run.py','diagnostic011/instrument.py','diagnostic011/metric.py',
      'diagnostic011/reference_4b.json','reasoning/runtime_helpers.py','reasoning/cycle2/trial_006_parent_full.json',
      'native010/parameters.jsonl','native010/row_column_norms.pt','rsi100/checkpoints/best.pt','rsi100/engine.py',
      'rsi100/data.json','code_rsi/runtime.py','code_rsi/sandbox.py','local_cpu/sandbox.py',
      'v2_adaptation/native_runtime.py','modeling_sensenova_loop.py','upstream/tokenizer_config.json']
    save('frozen.json',{'files':{p:e.cr.file_hash(ROOT/p) for p in paths},'error_ids':ERRORS,'guard_ids':GUARDS,
      'protocol':PROTOCOL,'fresh_evaluation':False,'reference_solution_used':False,'new_weight_candidate':False})
    state('registered_not_started')
    parent=json.loads((ROOT/'reasoning/cycle2/trial_006_parent_full.json').read_text())
    save('metric_current.json',{**compare({'rows':parent['rows'],'protocol':PROTOCOL}),
      'scope':'observed internal 16-task development; NOT LiveCodeBench or independent validation',
      'target_reference':json.loads((HERE/'reference_4b.json').read_text()),
      'promotion_allowed':False,'goal':'Positive task-level Delta4B on fresh frozen benchmark pairs, with retention'})

def suspect_index(tok,task_id,old):
    text=old['output'];char=text.index(MARKERS[task_id]) if task_id in MARKERS else 0
    encoded=tok(text,add_special_tokens=False,return_offsets_mapping=True)
    idx=next((i for i,(a,b) in enumerate(encoded['offset_mapping']) if a<=char<b),0)
    return {'char_offset':char,'estimated_token_index':idx,'marker':MARKERS.get(task_id),'only_a_suspected_error_span':task_id in MARKERS}

def actual_token_index(tok,raw,char):
    lengths=[len(tok.decode(raw[:i],skip_special_tokens=True)) for i in range(len(raw)+1)]
    return next((i for i,(a,b) in enumerate(zip(lengths,lengths[1:])) if a<=char<b),None)

@torch.inference_mode()
def capture():
    verify();old=reference_rows();model,tok,parent,meta=load()
    expected={r['name']:r['sha256_values'] for r in map(json.loads,(ROOT/'native010/parameters.jsonl').read_text().splitlines())}
    before={n:tensor_hash(p) for n,p in model.named_parameters()};assert before==expected
    rows=[]
    for task in tasks(ERRORS+GUARDS):
        name=task['id'];dest=HERE/f'capture_{name}.json'
        if dest.exists():
            r=json.loads(dest.read_text());assert r['status']=='complete'
            assert e.cr.file_hash(HERE/'activations'/f'{name}.pt')==r['activations_sha256'];rows.append(r);continue
        state('capturing_'+name,True);plan=suspect_index(tok,name,old[name]);n=old[name]['new_tokens']
        selected={plan['estimated_token_index'],n//2,n-1};observer=Observer(model,selected);start=time.monotonic()
        try:
            with ParameterAccess(observer):
                generated=e.cr.generate(model,tok,task['prompt']);generated.pop('trace')
            payload=observer.payload()
        finally:observer.close()
        assert generated['output']==old[name]['output'],'Instrumented generation drift; do not use as a paired trace'
        raw=[int(x['top_ids'][0]) for x in payload['next_token_statistics']]
        # Greedy generation is checked against decoding actual per-step model logits,
        # not an old answer teacher-forced through the model.
        assert tok.decode(raw,skip_special_tokens=True)==generated['output'],'Raw greedy token capture mismatch'
        assert len(raw)==generated['new_tokens']==len(payload['per_frame_module_statistics'])
        scored=e.cr.evaluate(generated['output'],task);assert scored['case_passed']==old[name]['case_passed']
        actual=actual_token_index(tok,raw,plan['char_offset']);plan.update(actual_token_index=actual,
            actual_suspected_point_snapshot_present=actual in selected if actual is not None else False)
        payload.update(own_generated_token_ids=torch.tensor(raw),selected_steps=sorted(selected),suspected_point=plan,
           parent_sha256=PARENT_HASH,protocol=PROTOCOL,feedback_to_model=False)
        path=HERE/'activations'/f'{name}.pt';tensor_checkpoint(payload,path)
        counts=payload['raw_parameter_access_counts'].sum((0,1));observed=int((counts>0).sum())
        frame_stats=payload['per_frame_module_statistics'];nonfinite=float(frame_stats[:,:,4].sum()+frame_stats[:,:,10].sum())
        r={'status':'complete','id':name,'group':'error' if name in ERRORS else 'guard',**generated,**scored,
          'actual_forward_calls':len(raw),'parameter_tensors_total':len(before),'observed_parameter_tensors':observed,
          'unobserved_parameter_tensors':len(before)-observed,'profiled_call_slots_per_token':len(payload['slots']),
          'profile_shape':list(frame_stats.shape),'recorded_nonfinite_activation_values':nonfinite,
          'selected_snapshot_steps':sorted(selected),'suspected_point':plan,'activations_sha256':e.cr.file_hash(path),
          'tensor_archive_bytes':path.stat().st_size,'old_output_and_case_bits_identical':True,'seconds_instrumented':time.monotonic()-start}
        save(dest.name,r);rows.append(r)
        print('CAPTURE_COMPLETE',name,observed,len(raw),path.stat().st_size,flush=True)
    after={n:tensor_hash(p) for n,p in model.named_parameters()};assert after==before
    save('capture_complete.json',{'status':'complete','parent_sha256':PARENT_HASH,'all_699_parameter_hashes_unchanged':True,
      'old_outputs_and_cases_identical':True,'rows':rows,'total_actual_decisions':sum(r['actual_forward_calls'] for r in rows),
      'error_responses':len(ERRORS),'guard_responses':len(GUARDS),'model':meta,'protocol':PROTOCOL,'weights_changed':False})
    state('capture_complete')

@torch.inference_mode()
def analyze():
    verify();report=json.loads((HERE/'capture_complete.json').read_text());assert report['status']=='complete'
    weight_rows={r['name']:r for r in map(json.loads,(ROOT/'native010/parameters.jsonl').read_text().splitlines())}
    norms=torch.load(ROOT/'native010/row_column_norms.pt',weights_only=True)
    bank={name:{'name':name,'shape':r['shape'],'dtype':r['dtype'],'numel':r['numel'],'weight_all_zero':r['all_zero'],
      'weight_rms':r['rms'],'weight_sha256':r['sha256_values'],'groups':{'error':[],'guard':[]},'read_kinds':[0,0,0],'operators':{},'reader_slots':set()} for name,r in weight_rows.items()}
    moments_by_group={'error':{},'guard':{}};sample=[]
    for row in report['rows']:
        p=torch.load(HERE/'activations'/f"{row['id']}.pt",weights_only=True);group=row['group'];frames=p['per_frame_module_statistics'];slots=p['slots'];idx={tuple(s):i for i,s in enumerate(slots)}
        counts=p['raw_parameter_access_counts'].sum(0);reader=p['parameter_reader_slot']
        for j,name in enumerate(p['parameter_names']):
            b=bank[name];b['read_kinds']=[a+int(z) for a,z in zip(b['read_kinds'],counts[:,j])]
            uses=p['parameter_reader_uses'].get(name,[]);b['reader_slots'].update(tuple(v) for v in uses)
            available=sorted({idx[tuple(v)] for v in uses if tuple(v) in idx})
            # Read slots can include a parent module's view access as well as its
            # actual owning module. Keep the relationship explicit, do not invent
            # parameter-specific causal activations.
            rms=float(frames[:,available,6].mean()) if available else None
            b['groups'][group].append({'task':row['id'],'observed':bool(counts[:,j].sum()),'mean_reader_output_rms':rms,'reader_slot_count':len(available)})
            for op,n in p['parameter_operator_counts'].get(name,{}).items():b['operators'][op]=b['operators'].get(op,0)+n
        for slot,m in p['coordinate_moments'].items():
            mean=m['sum_square']/m['observations'];key=(m['parameter'],tuple(slot))
            moments_by_group[group].setdefault(key,[]).append(mean)
        # Selection of a semantic suspicion is checked against ACTUAL token IDs.
        sample.append({'id':row['id'],'suspected_point':row['suspected_point'],'selected_steps':row['selected_snapshot_steps']})
    all_rows=[]
    for name,b in bank.items():
        b['reader_slots']=[list(v) for v in sorted(b['reader_slots'])]
        er=[x['mean_reader_output_rms'] for x in b['groups']['error'] if x['mean_reader_output_rms'] is not None]
        gr=[x['mean_reader_output_rms'] for x in b['groups']['guard'] if x['mean_reader_output_rms'] is not None]
        a=sum(er)/len(er) if er else None;c=sum(gr)/len(gr) if gr else None
        b.update(observed_in_errors=any(x['observed'] for x in b['groups']['error']),observed_in_guards=any(x['observed'] for x in b['groups']['guard']),
          error_reader_output_rms=a,guard_reader_output_rms=c,error_guard_log_rms_ratio=float(torch.log(torch.tensor((a+1e-12)/(c+1e-12)))) if a is not None and c is not None else None,
          interpretation='Raw access and observed reader activation, not causal blame or an edit direction')
        all_rows.append(b)
    vector_summary={};energy=[]
    for key in set(moments_by_group['error'])|set(moments_by_group['guard']):
        name,slot=key;record={'parameter':name,'slot':slot}
        for group in ['error','guard']:
            values=moments_by_group[group].get(key,[])
            if values:record[group+'_second_moment']=torch.stack(values).mean(0)
        vector_summary[str(key)]=record
        if name in norms:
            column=norms[name]['column_norms'].double();r=weight_rows[name]
            if len(r['shape'])==2:
                out={'parameter':name,'slot':slot,'proxy':'diagonal input energy; excludes cross-covariances, not causal importance'}
                for group in ['error','guard']:
                    x=record.get(group+'_second_moment')
                    if x is not None and x.shape==column.shape:out[group+'_diag_output_rms']=float((column.square().dot(x)/r['shape'][0]).sqrt())
                energy.append(out)
    tensor_checkpoint(vector_summary,HERE/'all_coordinate_moments.pt')
    with (HERE/'all_tensors.jsonl').open('w') as f:
        for row in all_rows:f.write(json.dumps(row,ensure_ascii=False,allow_nan=False)+'\n')
    ranking=sorted([r for r in all_rows if r['error_guard_log_rms_ratio'] is not None],key=lambda r:abs(r['error_guard_log_rms_ratio']),reverse=True)
    save('analysis.json',{'status':'complete','unique_parameter_tensors':len(bank),'observed_during_wrong_responses':sum(r['observed_in_errors'] for r in all_rows),
      'observed_during_correct_responses':sum(r['observed_in_guards'] for r in all_rows),
      'unobserved_parameter_names':[r['name'] for r in all_rows if not r['observed_in_errors']],
      'observed_all_zero_tensors':[r['name'] for r in all_rows if r['observed_in_errors'] and r['weight_all_zero']],
      'observed_only_on_errors':[r['name'] for r in all_rows if r['observed_in_errors'] and not r['observed_in_guards']],
      'top_activity_contrasts':[{'name':r['name'],'log_rms_ratio':r['error_guard_log_rms_ratio'],'error_rms':r['error_reader_output_rms'],'guard_rms':r['guard_reader_output_rms']} for r in ranking[:30]],
      'linear_energy_proxies':energy,'suspected_token_coverage':sample,
      'all_parameter_statistics_path':'diagnostic011/all_tensors.jsonl','snapshots_are_actual_forward_activations':True,
      'causal_error_attribution_established':False,'new_weight_edit_justified_by_activity_alone':False,'independent_validation_consumed':False})
    state('analysis_complete')
    print('ALL_TENSORS_ANALYZED',len(bank),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['initialize','capture','analyze']);a=p.parse_args();globals()[a.phase]()
