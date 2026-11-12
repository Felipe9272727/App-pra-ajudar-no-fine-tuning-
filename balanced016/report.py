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
    return {'taught':t['tasks_passed'],'transfer':b['tasks_passed'],'transfer_groups':b['test_groups_passed'],'control':c['correct'],'anchor_nll':c['anchor_nll']['mean_nll']}
def main():
    gate=read('balanced016/gate.json');training=read('balanced016/training_complete.json');manifest=read('balanced016/checkpoints/final/manifest.json')
    scores={'Qwen original':oldscore('supervised014','original'),'Principal geral':oldscore('supervised014','parent'),'Especialista 015E':oldscore('supervised015/attempt_e','specialist'),'Candidata 016':oldscore('balanced016','candidate')}
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
        elif n=='model.language_model.layers.31.mlp.down_proj.weight':f='last_mlp_projection'
        else:f='frozen_other'
        if s['changed_values']:
            d=byfamily.setdefault(f,{'changed_tensors':0,'changed_values':0});d['changed_tensors']+=1;d['changed_values']+=s['changed_values']
    audit=read('balanced016/weight_audit.json');gains=[x for x in audit['selected_details'] if x['family']=='loop_visit_gain'];gain_stats={'mean_second_visit_before':sum(x['before'][1] for x in gains)/len(gains),'mean_second_visit_after':sum(x['after'][1] for x in gains)/len(gains),'second_visit_gain_increased_layers':sum(x['after'][1]>x['before'][1] for x in gains),'second_visit_gain_decreased_layers':sum(x['after'][1]<x['before'][1] for x in gains),'mechanical_weighting_not_causal_quality_gain':True}
    result={'status':'complete','decision':decision,'historical_scores':scores,'gates':gate,'fresh_validation':fresh,'paired_custom_pilot_comparisons':comparisons,'actual_changes_by_family':byfamily,'joint_gradient_training':True,'loop_gain_audit':gain_stats,'final_max_relative_parameter_displacement':max(x['relative_displacement'] for x in audit['selected_details']),'post_projection_gain_normalization_above_radius_tensors':audit['actual_above_fp32_radius_tensors'],'selected_tensors':330,'selected_parameters':6345904,'changed_tensors':manifest['changed_tensors'],'changed_values':manifest['changed_values'],'optimizer_steps':16,'general_principal_promoted':False,'general_principal_preserved_sha256':'46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8','prior_specialist_E_preserved':True,'candidate_stream_sha256':manifest['stream_sha256'],'model_process_active':False,'process_continues_in_background':False}
    write('balanced016/summary.json',result);write('balanced016/status.json',{k:result[k] for k in ['status','decision','general_principal_promoted','model_process_active','process_continues_in_background']})
    lines=['# Liquid Sense — adaptação conjunta balanceada, estudo 016','',('**Candidata rejeitada por falha na retenção.**' if not gate['passed'] else f'Decisão: {decision}.')+' O checkpoint geral principal foi preservado.','',
      'Partimos do checkpoint 015E íntegro e preservado. Executamos uma candidata de 16 atualizações supervisionadas: 330 tensores e 6.345.904 parâmetros elegíveis, incluindo ganhos do Loop, roteamento mHC, operadores temporais inspirados na Liquid, normalizações e a última projeção MLP. Gradientes percorrem as duas visitas compartilhadas; isso não prova que o loop melhora a qualidade.','',
      '| Modelo | Programas ensinados /8 | MBPP observado /8 | Grupos MBPP /24 | Controles /12 | NLL âncoras |','|---|---:|---:|---:|---:|---:|']
    for label,s in scores.items():lines.append(f"| {label} | {s['taught']} | {s['transfer']} | {s['transfer_groups']} | {s['control']} | {s['anchor_nll']:.9f} |")
    lines+=['','Os oito programas foram ensinados deliberadamente; pontuação nesse conjunto mede especialização/memorização. O MBPP e os 12 controles são diagnósticos antigos já observados. Baselines anteriores foram reutilizados sem repetir experimentos. Mesma inferência: BF16/eager/cache, greedy, seed 0, thinking=False, quatro threads, 320 tokens de código e 64 para controles. Nenhuma solução/gabarito entra na geração de avaliação.','',
      'A candidata recuperou a ordenação Ana/Bia/Caio e o formato exigido para “frio” e “went”. Em contrapartida, perdeu a multiplicação 7 × 8: antes respondia 56, agora 7. A subtração 17 − 5 continuou produzindo 15; plural de animal e tradução em uma única palavra também falharam. São três controles recuperados e um perdido contra E; nenhuma resposta de controle foi ensinada nesta etapa.', '',
      'O único grupo MBPP novo aprovado não demonstra avanço algorítmico: em MBPP/407 o programa retorna sempre 0. Passa no caso sem próxima permutação porque o assert usa 0 == False, mas falha nos dois casos que exigem construir a permutação. Os testes e a pontuação oficial permanecem intactos; ver mbpp_partial_case_audit.json.', '',
      f"Mudanças reais em relação a E: {manifest['changed_tensors']} tensores, {manifest['changed_values']:,} valores; stream `{manifest['stream_sha256']}`. Todos os 369 tensores congelados preservados, incluindo 153 de visão. Restauração integral verificada pelos hashes dos 546 tensores de texto; 699 tensores finitos. Família de mudanças e cobertura de gradientes constam em summary/training_complete/steps.",'',
      'Critérios fixados antes dos resultados: 8/8 programas ensinados, pelo menos 10/12 controles sem perder nenhum acerto do principal, nenhuma perda MBPP de E e NLL no máximo igual ao principal + 0,005.','']
    for k,v in gate['gates'].items():lines.append(f'- {k}: {v}')
    if not gate['passed']:lines+=['','A auditoria de novidade encontrou quatro controles v1 já existentes em estudos antigos. O conjunto inicial ficou preservado sem uso, e a versão v2 foi registrada antes de qualquer consulta nova; ver NOVELTY_AMENDMENT.md.', '',
          'A candidata falhou na retenção e foi rejeitada. Os oito problemas novos de programação e oito controles novos ficaram sem consulta pelo modelo. As referências dos oito programas foram verificadas previamente por execução isolada e rejeição de mutantes, o que não constitui avaliação de modelo. Nenhum ajuste adicional usou esses testes.']
    else:
        lines+=['','Após passar o gate, comparação única congelada em oito problemas próprios novos, com 24 grupos de asserts, e oito controles novos:','', '| Variante | Código /8 | Controles /8 |','|---|---:|---:|']
        for k,s in fresh.items():lines.append(f"| {k} | {s['code_tasks']} | {s['controls']} |")
        lines+=['','Antes de qualquer inferência de validação, a auditoria de novidade identificou quatro controles v1 já presentes em estudos antigos. V1 foi preservada sem uso; a versão v2 e suas fontes foram registradas com os pesos já fixos, sem observar respostas novas e sem alterar critérios. Ver NOVELTY_AMENDMENT.md. Os oito problemas de código não mudaram.', '',
          'São testes autorais, não escores oficiais HumanEval/MBPP. Há sobreposição de famílias comuns de algoritmos. Comparações pareadas e intervalos exploratórios estão em summary.json; uma amostra de oito tarefas não estabelece inteligência geral nem superioridade a modelos de 4B. Nenhum reajuste foi feito a partir dessas saídas.']
    lines+=['',f"O ganho médio da segunda visita passou de {gain_stats['mean_second_visit_before']:.9f} para {gain_stats['mean_second_visit_after']:.9f}. A direção foi aprendida pela perda conjunta, sem obrigação de aumentar a segunda visita. Isso não demonstra mais pensamento. A projeção FP32 tem raio de 0,5%; a normalização posterior levou três vetores de ganhos a deslocamento relativo final até 0,521908%, conforme weight_audit.json.",'',
      'A arquitetura mantém 32 camadas físicas e 56 execuções, duas visitas no bloco 4–27, mHC com dois fluxos, convolução de tamanho 7 e janela local 256. Usa dimensões Qwen e operadores inspirados na Liquid, não uma reprodução completa do modelo Liquid AI. Treino conjunto e mudanças internas são fatos mecânicos; benefício causal do loop permanece não demonstrado.','',
      'Todos os pesos, logs e relatórios anteriores são preservados. O principal geral continua best.pt com SHA256 `46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8`; 015E continua separado como especialista no conjunto ensinado.','',
      'Reprodução: ambiente sem credenciais, offline, quatro threads; restaurar balanced016.restore.load_candidate() verifica a cadeia B→C→E→016. Protocolo, congelamento inicial e configuração registrados no commit 4bb01a00eed3fc19ede62906751d421a4979a680 antes de carregar a candidata. Rastreio da publicação em balanced016/artifact_manifest.json, artifact_verification.json, publication_receipt.json. Nenhum processo de modelo continua entre turnos.','']
    (ROOT/'BALANCED_JOINT_REPORT.md').write_text('\n'.join(lines));print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
