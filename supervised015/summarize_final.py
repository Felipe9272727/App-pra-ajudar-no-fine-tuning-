"""Select an experimental taught-benchmark specialist; never promote the principal."""
import json,hashlib,statistics,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;sys.path.insert(0,str(ROOT))
from supervised014.summarize import paired
from supervised014.judge import extract

def read(p):return json.loads(Path(p).read_text())
def metrics(directory):
    reports={r:read(directory/(r+'_specialist.json')) for r in ['target','transfer','controls']}
    assert all(r['status']=='complete' for r in reports.values());model={}
    for role,r in reports.items():
        if role=='controls':m={'correct':r['correct'],'total':r['total'],'nll':r['anchor_nll']['mean_nll']}
        else:m={'solved':r['tasks_passed'],'total':r['total'],'test_groups_passed':r['test_groups_passed'],'test_groups_total':r['test_groups_total'],'truncations':sum(x['hit_limit'] for x in r['rows']),'tokens':sum(x['new_tokens'] for x in r['rows']),'seconds':sum(x['seconds'] for x in r['rows'])}
        model['taught' if role=='target' else role]=m
    return reports,model

def main():
    b=HERE/'attempt_b';c=HERE/'attempt_c';br,bm=metrics(b);cr,cm=metrics(c)
    bc={role:paired(br[role]['rows'],cr[role]['rows']) for role in ['target','transfer']}
    accept=cm['taught']['solved']>bm['taught']['solved'] and not bc['target']['task_losses']
    selected='attempt_c' if accept else 'attempt_b';directory=HERE/selected
    bt=read(b/'training_complete.json');ct=read(c/'training_complete.json');training=ct if accept else bt
    models={k:v for k,v in read(b/'summary.json')['models'].items() if k!='specialist'}
    models.update(specialist_b=bm,specialist_c=cm,specialist=cm if accept else bm)
    references={role:read(ROOT/('supervised014/'+('taught' if role=='target' else role)+'_parent.json'))['rows'] for role in ['target','transfer']}
    cp={role:paired(references[role],cr[role]['rows']) for role in ['target','transfer']}
    training_view={'eligible_tensors':546,'eligible_parameters':919659696,'changed_text_tensors':ct['changed_tensors_vs_original_parent'] if accept else bt['changed_text_tensors'],
      'changed_scalar_values':ct['changed_values_vs_original_parent'] if accept else bt['changed_scalar_values'],'checkpoint_stream_sha256':training['checkpoint_stream_sha256'],
      'optimizer_steps':training['optimizer_steps'],'vision_tensors_unchanged':153}
    decision={'status':'experimental_benchmark_specialist_c_preserved' if accept else 'refinement_c_rejected_b_specialist_retained','selected_specialist':selected,
      'specialist_path':'supervised015/'+selected+'/checkpoints/final/manifest.json','checkpoint_promoted':False,'principal_unchanged':True,
      'selected_general_checkpoint':'rsi100/checkpoints/best.pt','parent_sha256':bt['parent_sha256'],
      'c_target_gain_required':True,'c_no_loss_of_b_correct_target_required':True,'c_selection_rule_passed':accept,
      'target_intentionally_taught':True,'mbpp_previously_observed_in_014_and_b':True,'mbpp_used_for_refitting':False,'general_or_4b_superiority_demonstrated':False}
    controls_parent={r['id']:r for r in read(ROOT/'supervised014/controls_parent.json')['rows']}
    cl={label:[r['id'] for r in report['controls']['rows'] if controls_parent[r['id']]['correct'] and not r['correct']] for label,report in [('b',br),('c',cr)]}
    result={'models':models,'training':training_view,'decision':decision,'c_vs_b':bc,'c_vs_principal':cp,'control_losses_vs_principal':cl,
      'b_training':{k:bt[k] for k in ['optimizer_steps','changed_text_tensors','changed_scalar_values','checkpoint_compressed_bytes','checkpoint_stream_sha256']},
      'c_training':{k:ct[k] for k in ['optimizer_steps_added','optimizer_steps','changed_text_tensors_vs_b','changed_values_vs_b','changed_tensors_vs_original_parent','changed_values_vs_original_parent','checkpoint_compressed_bytes','checkpoint_stream_sha256','parent_specialist_stream_sha256']}}
    (HERE/'final_summary.json').write_text(json.dumps(result,indent=2)+'\n');(HERE/'selection.json').write_text(json.dumps(decision,indent=2)+'\n')
    labels={'original':'Qwen original','parent':'Liquid Sense principal','edited':'Edição014 rejeitada','specialist_b':'SFT B: todos os pesos de texto','specialist_c':'SFT C: refinamento de tokens críticos'}
    lines=['# Liquid Sense — especialização supervisionada dos pesos de texto','',f'Especialista selecionado: **{selected}**. O checkpoint principal geral permanece preservado e selecionado. Os resultados abaixo vêm de geração livre sem soluções/gabaritos nos prompts de avaliação.','',
      '| Modelo | HumanEval ensinado | MBPP diagnóstico | Controles exatos | NLL linguagem |','|---|---:|---:|---:|---:|']
    for key,label in labels.items():
        m=models[key];lines.append(f'| {label} | {m["taught"]["solved"]}/8 | {m["transfer"]["solved"]}/8 | {m["controls"]["correct"]}/12 | {m["controls"]["nll"]:.6f} |')
    lines+=['','Os oito problemas HumanEval foram ensinados deliberadamente e já eram observados. Isso é ajuste/especialização, possivelmente memorização, e não uma pontuação limpa de HumanEval, validação independente ou inteligência geral. Não são benchmarks completos. MBPP ficou fora do treino, mas já era observado no014 e em B; não é um teste final inédito. Os conjuntos reservados anteriores permanecem fechados.','',
      f'Com autorização explícita para gradientes, foram treinados546 tensores/919.659.696 parâmetros ativos de texto. A comparação binária do especialista escolhido contra o principal encontrou mudança em {training_view["changed_text_tensors"]} tensores/{training_view["changed_scalar_values"]:,} valores; não se somam contagens de etapas que podem alterar as mesmas coordenadas. Não existe uma partição conhecida exclusivamente dedicada à programação. Os153 tensores de visão permaneceram idênticos em valores; sua capacidade funcional visual não foi testada.','',
      'A base nominal é Qwen3.5-0.8B e o híbrido ampliado carrega1.020.252.592 parâmetros únicos. Mantém32 camadas físicas,56 execuções,24 camadas centrais visitadas duas vezes, mHC com dois fluxos, convoluções7 e atenção local256. Os ganhos de visita continuam positivos/normalizados e os roteadores foram treinados. Presença ou alteração de um mecanismo não prova pensamento melhor nem benefício causal do segundo loop.','',
      'A tentativa A com taxa relativa .01 foi interrompida após11 atualizações completas e forte aumento da perda de treino. Seus logs/fontes foram preservados, mas seus pesos em memória não foram salvos. A tentativa B partiu do principal, com taxa .001 e32 atualizações/8épocas: alterou476.003.334 valores em546 tensores e acertou6/8 alvos. B permanece integralmente salvo. A revisão da taxa foi declarada no protocolo.','',
      f'C partiu do snapshot exato B, com taxa .0005 e {ct["optimizer_steps_added"]} atualizações adicionais. Todos546 tensores de texto continuaram elegíveis. A supervisão se concentrou no primeiro token canônico divergente por tarefa, com prefixo truncado: inicialmente poly em vez de True, e temp em vez de if. Cada decisão, margem antes do ajuste e atualização está nos logs. Prefixos corretos apareceram no treino; a avaliação recebeu apenas os enunciados. Identificar uma divergência ou seguir seu gradiente não identifica um peso único causador do erro.','',
      f'A regra congelada aceita C somente com ganho de tarefas completas e nenhuma perda das tarefas corretas de B. Resultado: {decision["status"]}. Comparação C/B no alvo: {bc["target"]}. Resultados MBPP/controles não escolheram as atualizações. Os testes/gabaritos não foram corrigidos nem os programas reparados.','',
      'A especialização teve regressões mensuráveis. Em B, parte das falhas de controle contém a resposta correta seguida de repetições ou tags: Sb, Santiago, heart,56,Ana e água. Há também erros de conteúdo:17 menos5 virou15 e o passado simples de go virou have gone/have been. O gabarito exato e a nota2/12 permanecem. A NLL de linguagem ligeiramente menor coexistiu com pior comportamento de geração; ela não comprova retenção geral. Os textos C e as perdas de controles estão nos resultados completos.','',
      f'Controles anteriormente corretos perdidos: {cl}. Nenhum especialista é promovido como substituto geral; o principal permanece rsi100/checkpoints/best.pt, SHA256 {bt["parent_sha256"]}. Não há comparação executada contra4B nem evidência de superioridade sobre modelos maiores.','',
      'Condições iguais para os modelos: mesmos enunciados/contexto, tokenizer, BF16/eager/cache, geração gulosa/seed0, thinking desligado, quatro threads,320 tokens para código e64 para controles. Originais/pai foram reutilizados do014 com hashes verificados; não foram repetidos. Qwen original executa24 camadas, os híbridos56: não há igualdade de FLOPs. Os tempos entre sessões não provam aceleração.','',
      'HumanEval:32,39,75,114,119,129,132,147. MBPP:129,239,245,247,306,392,407,463. Exemplos públicos já pertencentes aos enunciados permanecem; soluções privadas/testes não são entradas da geração. Usam-se o executor isolado e testes oficiais selecionados do014. O contraexemplo conhecido de quadrado mágico é diagnóstico separado, sem alterar os três testes oficiais. Atribuições/licenças estão em supervised014/NOTICE.md.','',
      'Cada snapshot foi restaurado a frio com todos546 hashes de texto conferidos,699 tensores finitos e153 tensores de visão inalterados. B é um XOR comprimido contra o principal; C é um XOR contra B. C precisa de TODAS as partes de ambos os snapshots, nessa ordem. Os manifests têm hashes por tensor/parte e do stream. O formato preserva os bits exatos; o otimizador/RNG também estão salvos. Não chame make_native/configure_loops após a restauração.','',
      f'Pesos selecionados: [manifest]({decision["specialist_path"]}). [Reprodução C](supervised015/attempt_c/REPRODUCE.md), [reprodução B](supervised015/attempt_b/REPRODUCE.md), [relatório completo B](supervised015/attempt_b/REPORT.md), [resultados e seleção](supervised015/final_summary.json), [método](supervised015/METHOD.md). As verificações remotas por Git blobs e refs ficam em supervised015/artifact_verification.json.','',
      '![Curvas de B/A: apenas os oito exemplos ensinados](supervised015/attempt_b/training_curve.svg)']
    (ROOT/'SUPERVISED_TEXT_REPORT.md').write_text('\n'.join(lines)+'\n')
    for d in [b,c]:
        x=read(d/'status.json');x.update(status='complete_pending_durable_publication',model_process_active=False,process_continues_in_background=False);(d/'status.json').write_text(json.dumps(x,indent=2)+'\n')
    (HERE/'status.json').write_text(json.dumps({'status':'complete_pending_durable_publication','active_directory':None,'selected_specialist':selected,'model_process_active':False,'checkpoint_promoted':False,'principal_unchanged':True,'process_continues_in_background':False},indent=2)+'\n')
    print(json.dumps({'models':models,'decision':decision,'training':training_view}))
if __name__=='__main__':main()
