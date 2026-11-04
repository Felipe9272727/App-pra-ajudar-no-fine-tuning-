"""One bounded outcome-only coding improvement cycle, controller-defined."""
import argparse
import gc
import shutil
from runtime import *
from loop_protocol import eligibility,validation_passes
from publish import publish

OUT=ROOT/'code_ci_output'
def export(stage,paths):
    dest=OUT/stage
    for path in paths:
        path=Path(path)
        if path.exists():
            target=dest/path.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target)

def export_json(stage):
    export(stage,list(HERE.glob('*.json'))+list((HERE/'checkpoints').glob('*.pt')))


@torch.inference_mode()
def collect():
    assert not (HERE/'frozen.json').exists()
    model,meta=load('baseline');tok=tokenizer();state(status='collecting_outcome_feedback',model_process_active=True)
    meta['cache_diagnostic']=cache_check(model,tok,2)
    records=[];features=[];rewards=[];tasks=DATA['train'];repairs=0
    for row in tasks:
        out=generate(model,tok,row['prompt'],capture=True)
        trace=out.pop('trace');feature=trace.pop('mlp_mean_abs_input')
        score=evaluate(out['output'],row)
        record={'id':row['id'],'attempt':'initial',**out,**score,'visit_diagnostics':trace}
        records.append(record);features.append(feature);rewards.append(score['passed']/score['total'])
        if not score['all_passed'] and repairs<DATA['protocol']['repair_budget']:
            repairs+=1
            feedback=f"Execution feedback: {score['category']}; {score['passed']} of {score['total']} tests passed. Expected values and reference code are withheld. Re-check your logic and edge cases."
            repair_prompt=row['prompt']+'\nYour previous attempt:\n'+extract_code(out['output'])+'\n'+feedback+'\nReturn a corrected complete function only.'
            repaired=generate(model,tok,repair_prompt,capture=True)
            trace=repaired.pop('trace');feature=trace.pop('mlp_mean_abs_input');rscore=evaluate(repaired['output'],row)
            records.append({'id':row['id'],'attempt':'feedback_repair','feedback':feedback,**repaired,**rscore,'visit_diagnostics':trace})
            features.append(feature);rewards.append(rscore['passed']/rscore['total'])
        atomic_json(HERE/'training_diagnostics.json',{'metadata':meta,'data_sha256':DATA_HASH,'records':records,'reference_code_supplied':False,'target_token_supervision':False})
        print('DIAG',row['id'],score['category'],score['passed'],score['total'],flush=True)
    x=torch.stack(features);r=torch.tensor(rewards)
    xc=x-x.mean(0);rc=r-r.mean()
    correlation=(xc*rc[:,None]).mean(0)/(xc.square().mean(0).sqrt()*rc.square().mean().sqrt()).clamp_min(1e-6)
    informative=bool(rc.square().sum()>1e-8 and correlation.square().sum()>1e-8)
    if informative:direction=correlation-correlation.mean()
    else:
        # Explicit exploratory probe, not a claim of learning from constant rewards.
        torch.manual_seed(DATA['seed']);direction=torch.randn(x.shape[1])
    direction=(direction/direction.square().mean().sqrt().clamp_min(1e-6)).clamp(-2,2)
    torch.save({'mean_abs_mlp_inputs':x,'execution_rewards':r,'direction':direction,
        'data_sha256':DATA_HASH,'informative_rewards':informative},HERE/'checkpoints/activation_summary.pt')
    prior=model.model.language_model.layers[31].mlp.down_proj.weight.detach().clone()
    archive=[]
    for name,spec in VARIANTS.items():
        if name=='baseline':continue
        sign=1 if spec['edit']=='plus' else -1
        fraction=DATA['protocol']['channel_edit_fraction']
        written=(prior.float()*(1+sign*fraction*direction)[None,:]).to(prior.dtype)
        path=HERE/'checkpoints'/f'{name}.pt'
        patch={'dense_weight':written,'passes':spec['passes'],'loop_gain_weights':visit_gains(spec['passes']),
            'data_sha256':DATA_HASH,'backward_passes':0,'runtime_adapter':False,
            'method':'outcome-correlated neuron-column rescaling; paired signs; no target token labels',
            'exploratory_direction':not informative}
        torch.save(patch,path)
        archive.append({'id':name,'patch':str(path.relative_to(ROOT)),'patch_sha256':file_hash(path),
            'passes':spec['passes'],'changed_bf16_values':int((written.view(torch.int16)!=prior.view(torch.int16)).sum()),
            'relative_frobenius':float((written.float()-prior.float()).norm()/prior.float().norm()),
            'status':'awaiting_development'})
        atomic_json(HERE/'archive.json',{'data_sha256':DATA_HASH,'candidates':archive,'selection_used_heldout':False})
        state(status='saving_experimental_checkpoint',model_process_active=True,candidates_saved=len(archive))
        publish('save '+name+' direct weights')
    # Small explicit-thinking diagnostic, never used for candidate selection.
    thinking=[]
    for row in tasks[:2]:
        out=generate(model,tok,row['prompt'],max_tokens=DATA['protocol']['thinking_probe_tokens'],thinking=True,seed=DATA['seed'])
        out.pop('trace');scored=evaluate(out['output'],row)
        # Persist outcome, length and final code only, not intermediate thinking text.
        thinking.append({'id':row['id'],'new_tokens':out['new_tokens'],'hit_limit':out['hit_limit'],
            'final_code':scored.pop('code'),'evaluation':scored})
    atomic_json(HERE/'thinking_diagnostic.json',{'rows':thinking,'used_for_selection':False,
        'note':'160-token thinking probe on training only; no claim that this budget measures reasoning capability'})
    categories=dict(collections.Counter(r['category'] for r in records if r['attempt']=='initial'))
    atomic_json(HERE/'diagnosis_summary.json',{'categories':categories,'informative_reward_variation':informative,
        'repairs_attempted':repairs,'repairs_passed':sum(r['all_passed'] for r in records if r['attempt']=='feedback_repair'),
        'causal_status':'Activation correlations are hypotheses. Development interventions isolate weight edits and extra loop passes. They do not identify a unique internal cause.',
        'prior_limit':'Earlier 12-token tests did not evaluate full code generation. Old dense edits changed teacher-forced likelihood but did not improve development exact answers.',
        'model_received_reference_answers':False})
    state(status='awaiting_development',model_process_active=False,process_continues_in_background=False)
    publish('save diagnosis and bounded thinking probe');export_json('collection')


@torch.inference_mode()
def evaluate_variant(variant,phase,shard=None):
    model,meta=load(variant);tok=tokenizer()
    passes=VARIANTS[variant]['passes'] if variant!='original' else 1
    if variant!='original':meta['cache_diagnostic']=cache_check(model,tok,passes)
    split={'development':'development','validation':'validation','final':'heldout'}[phase]
    rows=DATA[split]
    if phase=='final':
        frozen=json.loads((HERE/'frozen.json').read_text())
        assert not frozen['selection_used_heldout'] and variant in frozen['final_variants']
        assert shard in [0,1];rows=rows[shard::2]
        if variant==frozen['selected']:assert meta['patch_sha256']==frozen['selected_patch_sha256']
        meta.update(shard=shard,shards=2,frozen_sha256=file_hash(HERE/'frozen.json'))
    suffix=variant+(f'_shard{shard}' if phase=='final' else '')
    path=HERE/f'{phase}_{suffix}.json'
    report=evaluate_rows(model,tok,rows,path,fresh_report(variant,split,meta))
    if phase!='final' or shard==0:
        controlsplit={'development':'dev','validation':'val','final':'test'}[phase]
        c=controls(model,tok,controlsplit);report.update(controls_correct=c['correct'],controls=c)
        # Generic texts measure distribution preservation; no code answer labels.
        anchors=likelihood(model,tok,DATA['anchors'],anchors=True)
        report.update(anchor_nll=anchors['mean_nll'])
    atomic_json(path,report);export(f'{phase}-{suffix}',[path])
    print('SCORE',variant,phase,report['tasks_passed'],report['total'],report.get('controls_correct'),flush=True)


def shortlist():
    base=json.loads((HERE/'development_baseline.json').read_text());assert base['status']=='complete'
    archive=json.loads((HERE/'archive.json').read_text())
    eligible=[]
    for c in archive['candidates']:
        p=HERE/f"development_{c['id']}.json";result=json.loads(p.read_text())
        assert result['status']=='complete' and result['data_sha256']==DATA_HASH
        assert result['patch_sha256']==c['patch_sha256']
        assert result['protocol']==base['protocol'] and result['inference_code_sha256']==base['inference_code_sha256']
        c.update(status='development_complete',development={k:result[k] for k in ['tasks_passed','tests_passed','total','controls_correct','anchor_nll']},
            eligible=eligibility(result,base,DATA['protocol']['anchor_nll_ratio_cap']))
        if c['eligible']:eligible.append(c)
    eligible.sort(key=lambda c:(-c['development']['tasks_passed'],-c['development']['tests_passed'],c['passes']))
    queue=[c['id'] for c in eligible[:2]]
    atomic_json(HERE/'archive.json',archive);atomic_json(HERE/'validation_queue.json',{'variants':['baseline']+queue,'selection_used_heldout':False})
    state(status='awaiting_validation',validation_queue=queue,model_process_active=False)
    publish('development decisions and shortlist');export_json('shortlist')


def freeze():
    assert not (HERE/'frozen.json').exists()
    base=json.loads((HERE/'validation_baseline.json').read_text());assert base['status']=='complete'
    queue=json.loads((HERE/'validation_queue.json').read_text())['variants'][1:]
    archive=json.loads((HERE/'archive.json').read_text());passed=[]
    for key in queue:
        c=next(x for x in archive['candidates'] if x['id']==key)
        result=json.loads((HERE/f'validation_{key}.json').read_text())
        assert result['status']=='complete' and result['data_sha256']==DATA_HASH and result['patch_sha256']==c['patch_sha256']
        assert result['protocol']==base['protocol'] and result['inference_code_sha256']==base['inference_code_sha256']
        c.update(validation={k:result[k] for k in ['tasks_passed','tests_passed','total','controls_correct','anchor_nll']},
            passes_validation=validation_passes(result,base) and result['anchor_nll']<=base['anchor_nll']*DATA['protocol']['anchor_nll_ratio_cap'])
        if c['passes_validation']:passed.append(c)
    passed.sort(key=lambda c:(-c['validation']['tasks_passed'],-c['validation']['tests_passed'],c['passes']))
    selected=passed[0]['id'] if passed else None
    frozen={'data_sha256':DATA_HASH,'selected':selected,'selection_used_heldout':False,
        'final_variants':['original','baseline']+([selected] if selected else []),
        'selected_patch_sha256':next(c['patch_sha256'] for c in archive['candidates'] if c['id']==selected) if selected else None,
        'frozen_unix':time.time(),'architecture_required':'SenseNova loop/mHC + Liquid-inspired active',
        'reason':'passed development and validation' if selected else 'no weight edit demonstrated transferable gain; keep incumbent'}
    atomic_json(HERE/'archive.json',archive);atomic_json(HERE/'frozen.json',frozen)
    state(status='frozen_before_final_test',selected_candidate=selected,model_process_active=False)
    publish('freeze model before final test');export_json('frozen')


def report():
    frozen=json.loads((HERE/'frozen.json').read_text());variants=frozen['final_variants'];scores={}
    expected={r['id'] for r in DATA['heldout']}
    for variant in variants:
        parts=[json.loads((HERE/f'final_{variant}_shard{i}.json').read_text()) for i in range(2)]
        a,b=parts
        for p in parts:
            assert p['status']=='complete' and p['data_sha256']==DATA_HASH and p['frozen_sha256']==file_hash(HERE/'frozen.json')
        for key in ['variant','protocol','inference_code_sha256','patch_sha256']:
            assert a.get(key)==b.get(key),key
        rows=a['rows']+b['rows'];assert len(rows)==len(expected) and {r['id'] for r in rows}==expected
        combined={**a,'rows':rows,'total':len(rows),'tasks_passed':sum(r['all_passed'] for r in rows),
            'tests_passed':sum(r['passed'] for r in rows),'tests_total':sum(r['total'] for r in rows),
            'generation_seconds':sum(r['seconds'] for r in rows)}
        atomic_json(HERE/f'final_{variant}.json',combined)
        scores[variant]={k:combined[k] for k in ['tasks_passed','total','tests_passed','tests_total','controls_correct','anchor_nll','generation_seconds']}
    summary={'status':'complete','data_sha256':DATA_HASH,'model_name':'liquid sense 0.8 b LOOP',
        'selected':frozen['selected'],'scores':scores,'backward_passes':0,'answer_supervision':False,
        'autonomous_rsi':False,'best_small_model_claim_supported':False}
    atomic_json(HERE/'summary.json',summary)
    diagnosis=json.loads((HERE/'diagnosis_summary.json').read_text())
    lines=['# liquid sense 0.8 b LOOP — programação e feedback de execução','',
        ('Edição promovida: '+frozen['selected']) if frozen['selected'] else 'Nenhuma nova edição passou. O híbrido anterior foi preservado.','',
        '## Teste final customizado novo','',
        '| Modelo | Tarefas com todos os testes | Testes individuais | Controles gerais | Tempo geração |',
        '|---|---:|---:|---:|---:|']
    for key,s in scores.items():lines.append(f"| {key} | {s['tasks_passed']}/{s['total']} | {s['tests_passed']}/{s['tests_total']} | {s['controls_correct']}/{len(DATA['controls']['test'])} | {s['generation_seconds']:.1f}s |")
    lines+=['','## Diagnóstico e limites','',json.dumps(diagnosis,ensure_ascii=False,indent=2),'',
        'As soluções esperadas não entraram nos prompts nem em perdas de tokens. A adaptação usou apenas ativações do código gerado e a fração de testes aprovados. '
        'As correlações de canais não identificam uma causa interna única. As intervenções em sinais opostos e em números de loops testam hipóteses.','',
        'Os checkpoints escrevem a matriz BF16 existente da última MLP; gates FP32 e configuração de cache ficam salvos. '
        'Passagens 2/3/4 executam 56/80/104 camadas, com parâmetros compartilhados e slots de cache independentes. '
        'Todas as variantes mantêm convoluções Liquid de sete posições com histórico aprendido e janelas locais. '
        'O corpo é Qwen; os roteadores mHC ainda não foram aprendidos e oito camadas inseridas têm saída neutra.','',
        'O teste é um piloto customizado de 24 funções Python, greedy pass@1 até 160 tokens, sem ferramentas ou feedback no modelo durante avaliação. '
        'Original e híbridos recebem o mesmo orçamento de resposta. Mais loops custam mais computação. '
        'Quatro/oito controles curtos e NLL de textos não demonstram qualidade geral excepcional. '
        'Não é HumanEval, MBPP ou LiveCodeBench completo e não permite chamar este modelo de melhor modelo pequeno em programação.','',
        'O ensaio de thinking é separado, só em treino, limitado a 160 tokens e não escolhe pesos. '
        'As referências, hipóteses e protocolo estão em code_rsi/PROTOCOL.md.','',
        'Estado: concluído e parado; checkpoints e resultados preservados no Git.']
    (ROOT/'CODE_REPORT.md').write_text('\n'.join(lines)+'\n')
    state(status='complete',model_process_active=False,final_test_evaluated=True,selected_candidate=frozen['selected'],process_continues_in_background=False)
    export_json('final');export('final',[ROOT/'CODE_REPORT.md']);print(json.dumps(summary,indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['collect','development','shortlist','validation','freeze','final','report','matrix']);p.add_argument('--variant');p.add_argument('--shard',type=int);a=p.parse_args()
    if a.phase=='collect':
        try:collect()
        except Exception:
            state(status='collection_failed',model_process_active=False);export_json('collection');raise
    elif a.phase in ['development','validation','final']:evaluate_variant(a.variant,a.phase,a.shard)
    elif a.phase=='shortlist':shortlist()
    elif a.phase=='freeze':freeze()
    elif a.phase=='report':report()
    else:
        f=HERE/'frozen.json';q=HERE/'validation_queue.json'
        print(json.dumps(json.loads(f.read_text())['final_variants'] if f.exists() else json.loads(q.read_text())['variants'] if q.exists() else list(VARIANTS)))
