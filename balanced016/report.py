"""Postprocessing only; never changes weights, prompts, tests or eligibility gates."""
import json,math,random
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'balanced016'
def read(p):return json.loads((ROOT/p).read_text())
def write(p,x):(ROOT/p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def paired(a,b):
    byid={r['id']:r for r in a['rows']};wins=[];losses=[];diff=[]
    for r in b['rows']:
        old=bool(byid[r['id']]['all_passed']);new=bool(r['all_passed']);diff.append(int(new)-int(old))
        if new and not old:wins.append(r['id'])
        if old and not new:losses.append(r['id'])
    n=len(wins)+len(losses);p=sum(math.comb(n,k) for k in range(len(wins),n+1))/2**n if n else 1.
    rng=random.Random(20261112);boot=sorted(100*sum(rng.choice(diff) for _ in diff)/len(diff) for _ in range(10000))
    return {'gains':wins,'losses':losses,'delta_pp':100*sum(diff)/len(diff),'exact_one_sided_p':p,'paired_bootstrap_95_ci_pp':[boot[249],boot[9749]],'small_custom_pilot_not_general_superiority':True}
def oldscore(prefix,suffix):
    t=read(prefix+'/target_'+suffix+'.json') if suffix!='parent' and suffix!='original' else read('supervised014/taught_'+suffix+'.json')
    b=read(prefix+'/transfer_'+suffix+'.json');c=read(prefix+'/controls_'+suffix+'.json')
    return {'taught':t['tasks_passed'],'transfer':b['tasks_passed'],'control':c['correct'],'anchor_nll':c['anchor_nll']['mean_nll']}
def main():
    gate=read('balanced016/gate.json');training=read('balanced016/training_complete.json');manifest=read('balanced016/checkpoints/final/manifest.json')
    scores={'Qwen original':oldscore('supervised014','original'),'General principal':oldscore('supervised014','parent'),'Specialist015E':oldscore('supervised015/attempt_e','specialist'),'Candidate016':oldscore('balanced016','candidate')}
    fresh={};comparisons={}
    if gate['passed']:
        for v in ['original','principal','E','candidate']:
            code=read('balanced016/fresh_code_'+v+'.json');control=read('balanced016/fresh_controls_'+v+'.json');assert code['status']==control['status']=='complete'
            fresh[v]={'code_tasks':code['correct'],'code_total':code['total'],'controls':control['correct'],'control_total':control['total']}
        new=read('balanced016/fresh_code_candidate.json')
        for v in ['original','principal','E']:comparisons[v]=paired(read('balanced016/fresh_code_'+v+'.json'),new)
        qualified=all(not comparisons[v]['losses'] and comparisons[v]['gains'] for v in ['principal','E']) and fresh['candidate']['controls']==8
        decision='promising_research_candidate_only' if qualified else 'no_validated_research_gain'
    else:decision='rejected_on_retention_screen_new_validation_unqueried'
    byfamily={}
    for n,s in manifest['tensors'].items():
        if '.mhc_' in n:f='mhc_routing'
        elif 'native_visit_gain' in n:f='loop_visit_gain'
        elif any(x in n for x in ['.linear_attn.in_proj_a.','.linear_attn.in_proj_b.','.linear_attn.A_log','.linear_attn.dt_bias','.linear_attn.conv1d.']):f='liquid_temporal'
        elif 'layernorm' in n or '.norm.' in n:f='normalization'
        else:f='other'
        if s['changed_values']:
            d=byfamily.setdefault(f,{'changed_tensors':0,'changed_values':0});d['changed_tensors']+=1;d['changed_values']+=s['changed_values']
    result={'status':'complete','decision':decision,'historical_scores':scores,'gates':gate,'fresh_validation':fresh,'paired_custom_pilot_comparisons':comparisons,'actual_changes_by_family':byfamily,'joint_gradient_training':True,'selected_tensors':330,'selected_parameters':6345904,'changed_tensors':manifest['changed_tensors'],'changed_values':manifest['changed_values'],'optimizer_steps':16,'general_principal_promoted':False,'general_principal_preserved_sha256':'46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8','prior_specialist_E_preserved':True,'candidate_stream_sha256':manifest['stream_sha256'],'model_process_active':False,'process_continues_in_background':False}
    write('balanced016/summary.json',result);write('balanced016/status.json',{k:result[k] for k in ['status','decision','general_principal_promoted','model_process_active','process_continues_in_background']})
    lines=['# Liquid Sense: adaptação conjunta balanceada016','',f'Decisão: **{decision}**. Nenhuma substituição do checkpoint geral principal.','',
      'Partimos do checkpoint015E íntegro e preservado. Executamos uma candidata de16atualizações supervisionadas:330tensores/6.345.904parâmetros elegíveis, incluindo ganhos do Loop, roteamento mHC, operadores temporais inspirados na Liquid, normalizações e a última projeção MLP. Gradientes percorrem as duas visitas compartilhadas; isso não prova que o loop melhora a qualidade.','',
      '| Modelo | Programas ensinados /8 | MBPP observado /8 | Controles /12 | NLL âncoras |','|---|---:|---:|---:|---:|']
    for label,s in scores.items():lines.append(f"| {label} | {s['taught']} | {s['transfer']} | {s['control']} | {s['anchor_nll']:.9f} |")
    lines+=['','Os oito programas foram ensinados deliberadamente; pontuação nesse conjunto mede especialização/memorização. O MBPP e os12controles são diagnósticos antigos já observados. Baselines anteriores foram reutilizados sem repetir experimentos. Mesma inferência: BF16/eager/cache,greedy,seed0,thinking=False,quatro threads,320tokens de código/64controles. Nenhuma solução/gabarito entra na geração de avaliação.','',
      f"Mudanças reais em relação a E: {manifest['changed_tensors']}tensores, {manifest['changed_values']:,}valores; stream`{manifest['stream_sha256']}`. Todos369tensores congelados preservados, incluindo153visão. Restauração integral verificada pelos hashes dos546tensores de texto;699tensores finitos. Família de mudanças e cobertura de gradientes constam em summary/training_complete/steps.",'',
      'Gate fixado antes dos resultados:8/8programas ensinados,>=10/12controles sem perder nenhum acerto do principal, nenhuma perda MBPP de E e NLL<=principal+.005.','']
    for k,v in gate['gates'].items():lines.append(f'- {k}: {v}')
    if not gate['passed']:lines+=['','A candidata falhou na retenção e foi rejeitada. Os oito problemas novos de programação e oito controles novos ficaram sem consulta pelo modelo. Seus gabaritos foram verificados previamente por execução isolada das referências e mutantes, o que não constitui avaliação de modelo. Nenhum ajuste adicional usou esses testes.']
    else:
        lines+=['','Após passar o gate, comparação única congelada em oito problemas próprios novos, com24grupos de asserts, e oito controles novos:','', '| Variante | Código /8 | Controles /8 |','|---|---:|---:|']
        for k,s in fresh.items():lines.append(f"| {k} | {s['code_tasks']} | {s['controls']} |")
        lines+=['','São testes autorais, não escores oficiais HumanEval/MBPP. Há sobreposição de famílias comuns de algoritmos. Comparações pareadas e intervalos exploratórios estão em summary.json; uma amostra de oito tarefas não estabelece inteligência geral nem superioridade a4B. Nenhum reajuste foi feito a partir dessas saídas.']
    lines+=['','A arquitetura mantém32camadas físicas/56execuções,duas visitas no bloco4..27,mHC2,conv7 e janela local256. Usa dimensõesQwen e operadores inspirados na Liquid, não uma reprodução completa do modeloLiquidAI. Treino conjunto e mudanças internas são fatos mecânicos; benefício causal do loop permanece não demonstrado.','',
      'Todos os pesos, logs e relatórios anteriores são preservados. O principal geral continua best.pt com SHA256`46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8`;015E continua separado como especialista no conjunto ensinado.','',
      'Reprodução: env-i/offline/quatro threads; restaurar balanced016.restore.load_candidate() verifica a cadeia B→C→E→016. PROTOCOL.md/frozen.json/config.json fixados no commit4bb01a00eed3fc19ede62906751d421a4979a680 antes de carregar a candidata. Rastreio da publicação em balanced016/artifact_manifest.json,artifact_verification.json,publication_receipt.json. Nenhum worker continua entre turnos.','']
    (ROOT/'BALANCED_JOINT_REPORT.md').write_text('\n'.join(lines));print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
