"""Task-level public pilot statistics and complete research evidence report."""
import json
import math
from pathlib import Path

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]


def wilson(correct,n):
    z=1.959963984540054;p=correct/n;d=1+z*z/n
    center=(p+z*z/(2*n))/d
    half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return [center-half,center+half]


def paired(old,new):
    a={r['id']:r for r in old};b={r['id']:r for r in new};assert a.keys()==b.keys()
    wins=[k for k in a if not a[k]['all_passed'] and b[k]['all_passed']]
    losses=[k for k in a if a[k]['all_passed'] and not b[k]['all_passed']]
    n=len(wins)+len(losses)
    prob=min(1.,2*sum(math.comb(n,i) for i in range(min(len(wins),len(losses))+1))/2**n) if n else 1.
    casewins=[];caselosses=[]
    for k in a:
        assert len(a[k]['case_passed'])==len(b[k]['case_passed'])
        for i,(x,y) in enumerate(zip(a[k]['case_passed'],b[k]['case_passed'])):
            if y and not x:casewins.append([k,i])
            if x and not y:caselosses.append([k,i])
    return {'task_wins':wins,'task_losses':losses,'case_wins':casewins,'case_losses':caselosses,
            'exact_two_sided_task_p':prob,'unit':'task; private cases are correlated'}


def main():
    frozen=json.loads((HERE/'frozen.json').read_text())
    reports={v:json.loads((HERE/f'results_{v}.json').read_text()) for v in frozen['variants']}
    assert all(r['status']=='complete' and len(r['rows'])==36 for r in reports.values())
    scores={};comparisons={}
    names=['LiveCodeBench-v6-subset','GSM8K-zero-shot-subset','IFEval-filtered-subset']
    for variant,report in reports.items():
        scores[variant]={}
        for benchmark in names:
            rows=[r for r in report['rows'] if r['benchmark']==benchmark]
            total=len(rows);correct=sum(r['all_passed'] for r in rows)
            entry={'correct':correct,'total':total,'wilson_95pct':wilson(correct,total),
                   'cases_passed':sum(r['passed'] for r in rows),'cases_total':sum(r['total'] for r in rows),
                   'hit_limit':sum(r['hit_limit'] for r in rows),'new_tokens':sum(r['new_tokens'] for r in rows),
                   'generation_seconds':sum(r['seconds'] for r in rows)}
            if benchmark.startswith('IFEval'):entry['loose_correct']=sum(r['loose_all_passed'] for r in rows)
            scores[variant][benchmark]=entry
    for variant in reports:
        if variant=='original':continue
        comparisons[variant+'_vs_original']={name:paired([r for r in reports['original']['rows'] if r['benchmark']==name],
            [r for r in reports[variant]['rows'] if r['benchmark']==name]) for name in names}
    if 'parent' in reports:
        comparisons['liquid_vs_parent']={name:paired([r for r in reports['parent']['rows'] if r['benchmark']==name],
            [r for r in reports['liquid']['rows'] if r['benchmark']==name]) for name in names}
    selection=json.loads((ROOT/'reasoning/selection.json').read_text())
    summary={'status':'complete','scores':scores,'comparisons':comparisons,'selected':selection,
             'full_vendor_benchmarks_reproduced':False,'benchmarks_used_for_weight_edits':False,
             'backward_passes':0,'identity_excluded_from_scores':True}
    (HERE/'summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n')
    lines=['# Liquid Sense — pesos, profundidade de loop e benchmarks públicos','',
        'Continuação de 2026-11-05 a partir do pai preservado. A hipótese 002 anterior continuou arquivada. '
        'Não foram usados gradientes, otimizadores ou soluções de referência nas entradas de programação.','',
        '## Ativações e intervenções diretas','',
        'Na geração real, o contraste entre erros e tarefas corretas selecionou as camadas 25, 27 e 26. '
        'Foram preservados estados de tokens, coordenadas mais ativas e deriva entre visitas. '
        'Essas associações não identificam neurônios exclusivos de pensamento.','',
        '| Hipótese | Intervenção | Resultado |','|---|---|---|']
    for number in [3,4,5]:
        trial=json.loads((ROOT/f'reasoning/trial_{number:03d}.json').read_text())
        intervention={3:'Pesos de visita [0,95;0,05]→[0,925;0,075] nas três camadas selecionadas',
                      4:'Edição negativa de posto 1 na MLP final; dose 0,006; preservação de 137 ativações',
                      5:'Terceira visita seletiva: 80 execuções de camada, com cache independente'}[number]
        outcome=trial['stage']+'; '+trial.get('reason','')
        lines.append(f'| {number:03d} | {intervention} | {outcome} |')
    parent=json.loads((ROOT/'reasoning/trial_004_parent_full.json').read_text())
    dense=json.loads((ROOT/'reasoning/trial_004_target_full.json').read_text())
    diff=paired(parent['rows'],dense['rows'])
    lines += ['',f"A edição 004 fez {sum(r['passed'] for r in parent['rows'])}→{sum(r['passed'] for r in dense['rows'])} casos de desenvolvimento, "
        f"com {len(diff['case_wins'])} ganhos e {len(diff['case_losses'])} perdas por identidade de caso. "
        f"Controles: {sum(parent['control_bits'])}→{sum(dense['control_bits'])}/4. "
        f"NLL de linguagem: {parent['anchor_nll']:.9f}→{dense['anchor_nll']:.9f}. "
        'A piora da NLL violou o gate predefinido; não foi escondida nem compensada pelo acerto de programação. '
        'NLL é uma medida auxiliar e não equivale a uma avaliação completa de fluência.','',
        'A terceira visita foi tratada como um experimento de computação adicional. Seus pesos e os do grupo '
        'de controle ficaram arquivados; mais visitas ou texto de raciocínio não demonstram melhor raciocínio. '
        'O teste técnico de cache passou em duas, três e quatro visitas (56/80/104 execuções).','',
        '## Comparação externa independente','',
        'Fontes: [LFM3 oficial](https://huggingface.co/LiquidAI/LFM3-1.7B), que publica LiveCodeBench v6 e IFEval; '
        '[LFM2.5-Thinking oficial](https://www.liquid.ai/blog/lfm2-5-1-2b-thinking-on-device-reasoning-under-1gb), que publica GSM8K. '
        'Os conjuntos locais são subconjuntos fixados antes das saídas; não reproduzem os protocolos completos do fornecedor.','',
        '| Subconjunto | Modelo | Acertos completos | Casos | Truncamentos |','|---|---|---:|---:|---:|']
    for name in names:
        for variant in reports:
            s=scores[variant][name]
            lines.append(f"| {name} | {variant} | {s['correct']}/{s['total']} | {s['cases_passed']}/{s['cases_total']} | {s['hit_limit']} |")
    lines += ['', 'LiveCodeBench: oito problemas fáceis de stdin/stdout do incremento test6 da release_v6, '
        'sem os exemplos de entrada/saída no prompt, com até 16 casos privados originais por problema; '
        'comparação de stdout normalizada em espaços. GSM8K: 16 questões zero-shot, sem raciocínios de referência. '
        'IFEval: 12 instruções filtradas, com verificadores oficiais estritos e flexíveis preservados. '
        'Estas restrições e amostras impedem comparação direta com percentuais de leaderboard.','',
        'Mesmas entradas, contexto, tokenizer, BF16/eager, cache, seed 0 e quatro threads. Limites de saída: '
        '384/64/192 tokens por família. Identidade e prompts de marca ficam fora das avaliações. '
        'O híbrido ampliado tem aproximadamente 1,02B parâmetros e maior custo interno que o Qwen original '
        'de aproximadamente 0,87B; isto não é uma comparação com FLOPs iguais. '
        'Intervalos Wilson e comparações pareadas por tarefa estão em summary.json. '
        'As amostras são pequenas e convenientes, com viés de seleção documentado; não estabelecem superioridade geral '
        'ou ausência de contaminação pelo pré-treino.','',
        '## Seleção e identidade','',
        'Seleção: '+json.dumps(selection,ensure_ascii=False)+'.','',
        'O chat e o perfil apresentam Liquid Sense como um projeto independente conduzido por um desenvolvedor, '
        'com origem no Qwen e adaptações inspiradas em SenseNova/Liquid. O crédito ao projeto não apaga a origem '
        'da base pré-treinada. A identidade é uma configuração de aplicação; não foi atribuída a aprendizado de pesos '
        'nem somada aos resultados de capacidade. O teste real está em reasoning/identity_probe.json.','',
        'Pesos anteriores, candidatas, ativações, hipóteses, fontes e decisões permanecem no GitHub. '
        'Os resultados destes benchmarks não serão usados para ajustar outra candidata neste ciclo. '
        'Execução encerrada ao término do relatório; nenhum serviço local contínuo é prometido.']
    (ROOT/'REASONING_BENCHMARK_REPORT.md').write_text('\n'.join(lines)+'\n')
    print('PUBLIC_REPORT_COMPLETE',json.dumps(scores),flush=True)


if __name__=='__main__':main()
