"""Only report a complete fresh test after selection is frozen."""
import math
from common import *


def main():
    frozen=json.loads((HERE/'frozen.json').read_text())
    variants=['original','baseline']+(['selected'] if frozen['patch'] else [])
    reports={v:json.loads((HERE/f'heldout_{v}.json').read_text()) for v in variants}
    assert all(r['status']=='complete' and r['data_sha256']==DATA_HASH for r in reports.values())
    archive=json.loads((HERE/'archive.json').read_text())
    names={'original':'Qwen3.5-0.8B original','baseline':'Híbrido ativo antes do ciclo 2','selected':'Híbrido após edição aceita'}
    summary={}
    for v,r in reports.items():
        numeric=[x for x in r['rows'] if x['numeric']];controls=[x for x in r['rows'] if not x['numeric']]
        summary[v]={'exact':r['exact_correct'],'content':r['content_correct'],'total':r['total'],
            'numeric_content':sum(x['content_correct'] for x in numeric),'numeric_total':len(numeric),
            'controls_exact':sum(x['exact_correct'] for x in controls),'controls_total':len(controls),
            'loaded_parameters':r['loaded_parameters'],'seconds':sum(x['amortized_seconds'] for x in r['rows'])}
    final='selected' if frozen['patch'] else 'baseline'
    comparisons={}
    for other in ['original','baseline']:
        pairs=list(zip(reports[other]['rows'],reports[final]['rows']))
        assert all(a['id']==b['id'] for a,b in pairs)
        w=sum(not a['exact_correct'] and b['exact_correct'] for a,b in pairs)
        l=sum(a['exact_correct'] and not b['exact_correct'] for a,b in pairs)
        n=w+l;p=min(1.,2*sum(math.comb(n,i) for i in range(min(w,l)+1))/2**n) if n else 1.
        comparisons[other]={'wins':w,'losses':l,'exact_binomial_two_sided_p':p}
    overall={'model_name':'liquid sense 0.8 b LOOP','cycle':2,'status':'complete','data_sha256':DATA_HASH,
        'selected_candidate':frozen['candidate_id'],'scores':summary,'paired_exact_vs':comparisons,
        'selection_used_final_test':False,'backward_passes':0,'autonomous_rsi':False}
    atomic_json(HERE/'summary.json',overall)
    lines=['# liquid sense 0.8 b LOOP — RSI ciclo 2','',
        'Três etapas sequenciais de edição direta da matriz MLP existente, sem gradientes. '
        'O programa definido pelo assistente recalculou erros depois de cada edição. Não é RSI autônomo.','',
        ('Edição promovida: '+frozen['candidate_id']) if frozen['patch'] else 'Nenhuma edição nova passou; o híbrido ativo foi preservado.','',
        '## Teste final novo','',
        '| Modelo | Exato | Conteúdo | Numérico/código | Controles | Parâmetros carregados | Tempo geração |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for v,s in summary.items():
        lines.append(f"| {names[v]} | {s['exact']}/{s['total']} | {s['content']}/{s['total']} | {s['numeric_content']}/{s['numeric_total']} | {s['controls_exact']}/{s['controls_total']} | {s['loaded_parameters']:,} | {s['seconds']:.1f}s |")
    lines+=['','| Família | '+' | '.join(names[v] for v in variants)+' |','|---|'+'---:|'*len(variants)]
    for family in sorted({r['family'] for r in DATA['heldout']}):
        counts=[]
        for v in variants:
            rows=[r for r in reports[v]['rows'] if r['family']==family]
            counts.append(f"{sum(r['exact_correct'] for r in rows)}/{len(rows)}")
        lines.append('| '+family+' | '+' | '.join(counts)+' |')
    lines+=['','## Edições e seleção','',
        '| Etapa | Valores BF16 alterados | Desenvolvimento exato | NLL âncoras | Validação exata | Promovível |',
        '|---|---:|---:|---:|---:|---|']
    for c in archive['candidates']:
        d=c['development_generation'];val=c.get('validation');vt=f"{val['exact_correct']}/{val['total']}" if val else 'Não elegível'
        lines.append(f"| {c['step']} | {c['weight_write']['changed_bf16_values']} | {d['exact_correct']}/{d['total']} | {c['anchor']['mean_nll']:.5f} | {vt} | {c.get('passes_validation',False)} |")
    lines+=['','As duas melhores candidatas elegíveis em desenvolvimento foram à validação. '
        'Promoção exige mais respostas exatas e nenhuma perda agregada nos controles não numéricos. '
        'As âncoras limitam especialização, mas não provam preservação geral. O teste final foi aberto somente após congelar a escolha.','',
        '## Arquitetura e limites','',
        'SenseNova: 32 camadas físicas, 56 execuções, mHC de duas vias e segunda visita ativa. '
        'Liquid: convoluções de sete posições com histórico não nulo e janela local 256 em três camadas. '
        'São componentes compatíveis inspirados nessas arquiteturas sobre pesos Qwen; não são os modelos completos. '
        'Roteadores mHC continuam na inicialização e oito camadas inseridas têm saída neutra. '
        'A base é nominalmente 0,8B; o híbrido carrega cerca de 1,02B parâmetros, incluindo visão não avaliada.','',
        'Os primeiros erros são calculados com prefixos de resposta correta. A regressão usa uma aproximação local do RMSNorm; '
        'somente a geração completa decide elegibilidade. Cada checkpoint contém a matriz BF16 densa escrita, sem adaptador extra.','',
        'Mesmo conjunto, greedy sem thinking, 12 tokens, quatro threads CPU, duas partições iguais por modelo. '
        'O híbrido usa mais computação que o original. Tempos em runners distintos são aproximados. '
        'O teste customizado de 80 questões compartilha templates com o currículo; não mede inteligência geral. '
        'Resultados anteriores (39/64 contra 34/64) são históricos em history/ e não são diretamente comparáveis.','',
        'Comparações pareadas exatas: `'+json.dumps(comparisons,ensure_ascii=False)+'`. '
        'Os p-valores são descritivos; há dependência entre templates.','',
        'Estado: concluído e parado. Checkpoints das três etapas e escolha final salvos em commits.','',
        '## Todas as respostas','',
        '| ID | Esperado | Original | Híbrido inicial | Final |','|---|---|---|---|---|']
    by={v:{r['id']:r for r in report['rows']} for v,report in reports.items()}
    def esc(x):return x.replace('|','\\|').replace('\n',' / ')
    for row in DATA['heldout']:
        lines.append('| '+row['id']+' | '+esc(row['answer'])+' | '+' | '.join(esc(by[v][row['id']]['output']) for v in ['original','baseline',final])+' |')
    (ROOT/'LAB_REPORT.md').write_text('\n'.join(lines)+'\n')
    atomic_json(ROOT/'checkpoints/liquid_sense_loop.json',{**frozen,'status':'complete',
        'loaded_parameters':reports[final]['loaded_parameters'],'report':'LAB_REPORT.md',
        'summary':'lab_rsi/summary.json','replay':'python lab_rsi/replay.py --question YOUR_QUESTION',
        'base_revision':'2fc06364715b967f1860aea9cf38778875588b17','source_manifest':'model_identity.json'})
    update_status(status='complete',phase='checkpointed',evaluating_variant=None,
        final_test_evaluated=True,selected_candidate=frozen['candidate_id'],process_continues_in_background=False)
    print(json.dumps(overall,indent=2,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
