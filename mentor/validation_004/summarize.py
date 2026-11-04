"""Paired task-level statistics and immutable-checkpoint decision."""
import json
import math
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def score(report, group=None):
    rows = [r for r in report['rows'] if group is None or r['group'] == group]
    return {'tasks_passed':sum(r['all_passed'] for r in rows),'tasks_total':len(rows),
            'cases_passed':sum(r['passed'] for r in rows),'cases_total':sum(r['total'] for r in rows),
            'hit_token_limit':sum(r['hit_limit'] for r in rows)}


def compare(a, b, group=None):
    old = {r['id']:r for r in a['rows'] if group is None or r['group']==group}
    new = {r['id']:r for r in b['rows'] if group is None or r['group']==group}
    assert old.keys() == new.keys()
    wins = [k for k in old if not old[k]['all_passed'] and new[k]['all_passed']]
    losses = [k for k in old if old[k]['all_passed'] and not new[k]['all_passed']]
    n = len(wins)+len(losses)
    p = min(1., 2*sum(math.comb(n,i) for i in range(min(len(wins),len(losses))+1))/2**n) if n else 1.
    diffs = [int(new[k]['all_passed'])-int(old[k]['all_passed']) for k in old]
    rng = random.Random(20261104004)
    boot = sorted(sum(rng.choices(diffs,k=len(diffs)))/len(diffs) for _ in range(10000))
    case_wins, case_losses = [], []
    for k in old:
        assert len(old[k]['case_passed'])==len(new[k]['case_passed'])
        for i,(x,y) in enumerate(zip(old[k]['case_passed'],new[k]['case_passed'])):
            if x and not y:
                case_losses.append([k,i])
            if y and not x:
                case_wins.append([k,i])
    return {'task_wins':wins,'task_losses':losses,
        'case_wins':case_wins,'case_losses':case_losses,
        'output_changed_tasks':[k for k in old if old[k]['output']!=new[k]['output']],
        'paired_task_delta':sum(diffs)/len(diffs),'task_bootstrap_95pct':[boot[249],boot[9749]],
        'exact_two_sided_mcnemar_p':p,'independent_unit':'task, not individual case',
        'bootstrap_limit':'Empirical bootstrap cannot establish equivalence when all observed deltas are zero.'}


def main():
    reports = {k:json.loads((HERE/('results_'+k+'.json')).read_text()) for k in ['original','parent','candidate']}
    for r in reports.values():
        assert r['status']=='complete' and len(r['rows'])==24 and len(r['controls'])==12
        assert all(x['identical'] for x in r['repeats']) and len(r['repeats'])==4
    assert len({r['frozen_sha256'] for r in reports.values()})==1
    scores = {k:{'all':score(r),'far':score(r,'far'),'near':score(r,'near'),
                  'controls_correct':sum(x['correct'] for x in r['controls']),
                  'controls_total':len(r['controls']),'anchor_nll':r['anchor']['mean_nll']}
              for k,r in reports.items()}
    pairs = {'candidate_vs_parent':compare(reports['parent'],reports['candidate']),
             'candidate_vs_parent_far':compare(reports['parent'],reports['candidate'],'far'),
             'candidate_vs_parent_near':compare(reports['parent'],reports['candidate'],'near'),
             'parent_vs_original':compare(reports['original'],reports['parent']),
             'candidate_vs_original':compare(reports['original'],reports['candidate'])}
    old_controls = {x['id']:x for x in reports['parent']['controls']}
    new_controls = {x['id']:x for x in reports['candidate']['controls']}
    lost_controls = [k for k in old_controls if old_controls[k]['correct'] and not new_controls[k]['correct']]
    gain_controls = [k for k in old_controls if not old_controls[k]['correct'] and new_controls[k]['correct']]
    dev = json.loads((ROOT/'mentor/recovery_004/development_gate.json').read_text())
    primary = pairs['candidate_vs_parent']
    checks = {'development_gates':dev['eligible_for_fresh_validation'],
        'no_fresh_case_loss':not primary['case_losses'], 'no_fresh_control_loss':not lost_controls,
        'far_task_gain':bool(pairs['candidate_vs_parent_far']['task_wins']) and not pairs['candidate_vs_parent_far']['task_losses'],
        'paired_task_p_le_0_05':primary['exact_two_sided_mcnemar_p']<=.05,
        'new_anchor_preserved':scores['candidate']['anchor_nll']<=scores['parent']['anchor_nll']+1e-6}
    promoted = all(checks.values())
    summary = {'status':'complete','scores':scores,'comparisons':pairs,
        'control_losses':lost_controls,'control_gains':gain_controls,
        'promotion_checks':checks,'candidate_validated':promoted,'checkpoint_promoted':promoted,
        'selected_checkpoint':'mentor/checkpoints/negative_002_recovered.pt' if promoted else 'rsi100/checkpoints/best.pt',
        'decision':'validated_candidate_preserved' if promoted else 'generalization_not_confirmed_keep_parent',
        'legacy_search_restarted':False,'additional_weight_hypotheses_run':0,'backward_passes':0,
        'reconstructed_candidate_not_bitwise_original':True,'frozen_sha256':reports['parent']['frozen_sha256']}
    (HERE/'summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n')
    lines=['# Liquid Sense 0.8B LOOP — retomada e validação independente','',
        'A base nominal é Qwen3.5-0.8B; o híbrido preservado carrega 1.020.252.592 parâmetros. '
        'Loop/mHC e operadores inspirados em Liquid permaneceram ativos. Zero gradientes, otimizadores ou fine-tuning.','',
        '## Recuperação','',
        'O commit 45b5152 preservou somente a triagem da hipótese 002 (pai 2/5, aleatório 2/5, candidata 5/5). '
        'O checkpoint final e o resultado completo não foram encontrados nas branches e artefatos acessíveis do GitHub. Foram preservados 31 descartes antigos, '
        'a rejeição da hipótese 001 e a V3 NCM como experimento não promovido. Não se reiniciou a busca automática.','',
        'A reconstrução usa a dose já fixada de 0,012 e as ativações do próprio modelo na geração real. '
        'Altera somente model.language_model.layers.31.mlp.down_proj.weight (1024×3584, BF16): '
        'subtrai um produto externo de posto 1 residualizado contra as 54 ativações anteriores, na direção negativa '
        'do token produzido incorretamente (` len`, id 2343). Nenhuma substituição correta foi fornecida.','',
        'O pai teve todos os textos e acertos de desenvolvimento reproduzidos. A reconstrução altera 2.025.354 '
        'valores; o registro antigo indicava 2.029.223. Portanto, não se afirma igualdade bit a bit com pesos que '
        'não foram salvos. O arquivo avaliado tem SHA256 '
        '8fd291019b20f7d327e775c05a30f5b991395718040e4ad2fe52ed986ff748ef.','',
        '## Desenvolvimento observado (recuperação, não generalização)','',
        '| Modelo | Tarefas completas | Casos | Controles | NLL âncora |',
        '|---|---:|---:|---:|---:|']
    for k in ['parent','candidate']:
        r=json.loads((ROOT/('mentor/recovery_004/development_'+k+'.json')).read_text())
        lines.append(f"| {k} | {sum(x['all_passed'] for x in r['rows'])}/16 | {sum(x['passed'] for x in r['rows'])}/81 | {sum(r['control_bits'])}/4 | {r['anchor_nll']:.9f} |")
    lines += ['', '## Validação independente congelada','',
        '| Modelo | Tarefas | Casos | Fora da família de sobreposição | Próximas à hipótese | Controles estritos | Limite de tokens |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for k,s in scores.items():
        lines.append(f"| {k} | {s['all']['tasks_passed']}/24 | {s['all']['cases_passed']}/192 | {s['far']['tasks_passed']}/20 | {s['near']['tasks_passed']}/4 | {s['controls_correct']}/12 | {s['all']['hit_token_limit']} |")
    lines += ['',f"Candidata versus pai: {len(primary['task_wins'])} tarefas ganhas, {len(primary['task_losses'])} perdidas; "
        f"{len(primary['case_wins'])} casos ganhos, {len(primary['case_losses'])} perdidos. "
        f"McNemar exato bilateral por tarefa: p={primary['exact_two_sided_mcnemar_p']:.6g}. "
        f"Diferença de pass@1: {100*primary['paired_task_delta']:.2f} pontos percentuais; "
        f"IC bootstrap empírico 95%: [{100*primary['task_bootstrap_95pct'][0]:.2f}, {100*primary['task_bootstrap_95pct'][1]:.2f}].",'',
        f"Controles perdidos: {lost_controls}; ganhos: {gain_controls}. NLL nova: pai {scores['parent']['anchor_nll']:.9f}, candidata {scores['candidate']['anchor_nll']:.9f}.",'',
        f"Candidata versus Qwen original: {len(pairs['candidate_vs_original']['task_wins'])} tarefas ganhas e {len(pairs['candidate_vs_original']['task_losses'])} perdidas; {len(pairs['candidate_vs_original']['case_wins'])} casos ganhos e {len(pairs['candidate_vs_original']['case_losses'])} perdidos. Diferenças herdadas da arquitetura não são atribuídas à edição.",'',
        'Quatro tarefas repetidas por variante tiveram textos e acertos idênticos. Como a geração é gulosa, '
        'essas repetições verificam estabilidade, sem criar novas amostras independentes. A comparação usa '
        'o mesmo contexto, limite, tokenizer, BF16, kernels eager, cache, seed e quatro threads. '
        'Os híbridos têm 32 camadas físicas, 56 execuções de camada por passo e aproximadamente 1,02B parâmetros; '
        'o Qwen original usa suas 24 camadas e aproximadamente 0,87B parâmetros. A comparação com o original '
        'não equaliza FLOPs ou latência; a comparação pai/candidata mantém a mesma arquitetura e computação. '
        'Casos, gabaritos e implementações de referência ficaram fora das entradas do modelo. '
        'Os hashes e o protocolo foram publicados antes das saídas desta validação.','',
        '## Decisão','',
        ('Os critérios registrados foram atendidos; preservar a candidata validada, sem alegar inteligência geral.' if promoted else
         'A generalização não foi confirmada pelos critérios registrados. Manter o checkpoint pai como melhor versão; '
         'preservar a candidata reconstruída e os resultados como experimento, sem promoção.'),'',
        'Critérios: '+json.dumps(checks,ensure_ascii=False)+'.','',
        'Limites: suíte customizada pequena, criada pelo mesmo assistente que conhece a hipótese; não é auditoria cega. '
        'O controle de tradução contém um falso negativo conhecido: “Necessitamos de água limpa” é semanticamente '
        'válido, mas não consta dos aliases congelados. Os escores automáticos e o gabarito não foram alterados; '
        'uma mudança entre sinônimos válidos não demonstra ganho linguístico. '
        'Ausência de regressão nestes controles não prova preservação geral. Não é possível garantir novidade '
        'perante o pré-treino. Ganhos próximos ao problema editado podem ser especialização. Casos de uma mesma '
        'tarefa não são 192 observações independentes. Um IC bootstrap degenerado com todos os deltas zero '
        'não prova equivalência. Os conjuntos antigos reservados permaneceram fechados. '
        'Novas edições exigirão outro teste ainda não observado.','',
        'Detalhes e saídas completas: mentor/recovery_004/ e mentor/validation_004/. '
        'Estado final: avaliação concluída, nenhum processo de pesquisa prometido em segundo plano.']
    (ROOT/'MENTOR002_VALIDATION_REPORT.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(summary,indent=2),flush=True)


if __name__=='__main__':
    main()
