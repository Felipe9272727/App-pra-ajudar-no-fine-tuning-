"""Paired in-sample versus transfer report, without model calls or retuning."""
import collections,hashlib,json,math,random,statistics
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
def read(n):return json.loads((HERE/n).read_text())
def paired(base,new):
    b={r['id']:r for r in base};g=[];l=[];lost_groups=0;changed=[];d=[]
    for r in new:
        old=b[r['id']];delta=int(r['all_passed'])-int(old['all_passed']);d.append(delta)
        if delta>0:g.append(r['id'])
        if delta<0:l.append(r['id'])
        lost_groups+=sum(x and not y for x,y in zip(old['case_passed'],r['case_passed']))
        if old['output']!=r['output']:changed.append(r['id'])
    n=len(g)+len(l);p=sum(math.comb(n,k) for k in range(len(g),n+1))/2**n if n else 1.
    rng=random.Random(20261111);boot=sorted(100*sum(rng.choice(d) for _ in d)/len(d) for _ in range(10000))
    return {'task_gains':g,'task_losses':l,'lost_test_groups':lost_groups,'output_changed':changed,
            'delta_pass_at_1_pp':100*sum(d)/len(d),'exact_one_sided_p':p,'paired_bootstrap_95_ci_pp':[boot[250],boot[9750]]}

def main():
    audit=read('teaching.json');models={};comparisons={}
    for kind in ['original','parent','edited']:
        model={}
        for role in ['taught','transfer','controls']:
            r=read(role+'_'+kind+'.json');assert r['status']=='complete'
            assert r['frozen_sha256']==hashlib.sha256((HERE/'frozen.json').read_bytes()).hexdigest()
            if role=='controls':model[role]={'correct':r['correct'],'total':r['total'],'nll':r['anchor_nll']['mean_nll']}
            else:model[role]={'solved':r['tasks_passed'],'total':r['total'],
                'test_groups_passed':r['test_groups_passed'],'test_groups_total':r['test_groups_total'],
                'truncations':sum(x['hit_limit'] for x in r['rows']),
                'tokens':sum(x['new_tokens'] for x in r['rows']),'seconds':sum(x['seconds'] for x in r['rows']),
                'categories':dict(collections.Counter(x['category'] for x in r['rows']))}
        models[kind]=model
    for role in ['taught','transfer']:
        comparisons[role]=paired(read(role+'_parent.json')['rows'],read(role+'_edited.json')['rows'])
    pc={r['id']:r for r in read('controls_parent.json')['rows']};ec=read('controls_edited.json')['rows']
    losses=[r['id'] for r in ec if pc[r['id']]['correct'] and not r['correct']]
    nll_delta=models['edited']['controls']['nll']-models['parent']['controls']['nll']
    gates={'transfer_task_gain':bool(comparisons['transfer']['task_gains']),
      'no_transfer_task_loss':not comparisons['transfer']['task_losses'],
      'no_transfer_group_loss':not comparisons['transfer']['lost_test_groups'],
      'no_taught_task_or_group_loss':not comparisons['taught']['task_losses'] and not comparisons['taught']['lost_test_groups'],
      'no_parent_correct_control_loss':not losses,'language_nll_retained':nll_delta<=.005,
      'paired_transfer_p_le_05':comparisons['transfer']['exact_one_sided_p']<=.05}
    eligible=all(gates.values())
    decision={'status':'pilot_passed_requires_explicit_promotion_record' if eligible else 'complete_candidate_rejected_parent_retained',
      'checkpoint_promoted':False,'parent_retained':True,'gates':gates,'control_losses':losses,'anchor_nll_delta':nll_delta,
      'candidate_sha256':audit['candidate_sha256'],'candidate_path':'supervised014/checkpoints/candidate.pt',
      'selected_checkpoint':'rsi100/checkpoints/best.pt','parent_sha256':audit['parent_sha256'],
      'taught_set_is_contaminated':True,'transfer_used_for_refitting':False}
    before=statistics.mean(r['before']['mean_nll'] for r in audit['diagnostics']);after=statistics.mean(r['after']['mean_nll'] for r in audit['diagnostics'])
    ac_before=statistics.mean(r['before']['token_accuracy'] for r in audit['diagnostics']);ac_after=statistics.mean(r['after']['token_accuracy'] for r in audit['diagnostics'])
    result={'models':models,'comparisons_edited_vs_parent':comparisons,'decision':decision,
       'teacher_forced_taught_only':{'mean_task_nll_before':before,'mean_task_nll_after':after,'mean_task_token_accuracy_before':ac_before,'mean_task_token_accuracy_after':ac_after}}
    (HERE/'summary.json').write_text(json.dumps(result,indent=2)+'\n');(HERE/'selection.json').write_text(json.dumps(decision,indent=2)+'\n')
    labels={'original':'Qwen original','parent':'Liquid Sense anterior','edited':'Liquid Sense com edição direta'}
    lines=['# Respostas corretas nos pesos — estudo 014','',
      'Oito soluções corretas do HumanEval foram usadas para editar uma matriz existente. '
      'Depois, os três modelos geraram programas para esses mesmos oito problemas e para '
      'oito problemas diferentes do MBPP, sem receber referências ou testes na geração.','',
      '**O resultado do HumanEval ensinado é ajuste aos exemplos, não generalização.** '
      'As pontuações abaixo são subconjuntos de um piloto, não escores completos dos benchmarks.','',
      '## O que mudou nos pesos','',
      f'Foi alterado apenas `{audit["changed_tensors"][0]}`, matriz BF16 de 1024 × 3584: '
      f'{audit["changed_bf16_values"]:,} valores diferentes. A variação de norma Frobenius foi '
      f'{100*audit["actual_relative_frobenius"]:.4f}%. Os {audit["parent_tensors_checked"]} '
      'tensores originais foram comparados; todos os demais permaneceram iguais. Não há novo '
      'adaptador, tabela de respostas ou solução inserida no prompt.','',
      'O ajuste usa projeções geométricas para margens de tokens corretos, levando em conta '
      'o RMSNorm final, e uma solução ridge por álgebra linear. Não houve gradientes, backward '
      'ou otimizador. Foram preservados o loop de duas passagens, 32 camadas físicas/56 execuções, '
      'mHC e os operadores inspirados em Liquid. A última matriz fica depois do loop; este '
      'experimento não ensina um novo controlador de passagens nem modifica os operadores temporais.','',
      f'No diagnóstico com prefixos corretos dos oito exemplos ensinados, a NLL média por problema '
      f'foi {before:.6f} → {after:.6f}; a precisão média de tokens foi '
      f'{100*ac_before:.2f}% → {100*ac_after:.2f}%. Esses valores não substituem a geração livre.','',
      '## Resultados de geração livre','',
      '| Modelo | HumanEval ensinado | MBPP diferente | Controles | NLL de linguagem |',
      '|---|---:|---:|---:|---:|']
    for kind,m in models.items():lines.append(f'| {labels[kind]} | {m["taught"]["solved"]}/8 | {m["transfer"]["solved"]}/8 | {m["controls"]["correct"]}/12 | {m["controls"]["nll"]:.6f} |')
    lines+=['','HumanEval: IDs 32, 39, 75, 114, 119, 129, 132, 147. MBPP sanitizado: '
      'IDs 129, 239, 245, 247, 306, 392, 407, 463, dentro do intervalo oficial de teste. '
      'Os números iguais entre os dois datasets não identificam os mesmos problemas. '
      'Todos os 16 programas de referência passaram nos testes originais; todos os 16 '
      'mutantes que retornam None foram rejeitados. Não há AST de solução idêntica entre os conjuntos.','',
      'Foi usado o mesmo pedido de código completo, tokenizer, BF16, cache, kernels eager, '
      'geração gulosa, seed 0, thinking desativado, quatro threads e limite de 320 tokens. '
      'As referências selecionadas têm de 94 a 221 tokens. O enunciado HumanEval mantém seus '
      'exemplos e auxiliares públicos; o MBPP recebe descrição e assinatura exigida. '
      'Isso difere dos protocolos canônicos de completion/three-shot; não há igualdade de '
      'FLOPs entre Qwen original (24 execuções) e híbridos (56).','']
    for role in ['taught','transfer']:
        c=comparisons[role];lines.append(f'{role}: {len(c["task_gains"])} tarefas ganhas e '
          f'{len(c["task_losses"])} perdidas contra o pai; p unilateral pareado '
          f'{c["exact_one_sided_p"]:.6f}; IC bootstrap descritivo de 95% para a diferença em '
          f'pontos percentuais: {c["paired_bootstrap_95_ci_pp"]}. Os IDs e grupos perdidos '
          'estão em supervised014/summary.json.');lines.append('')
    lines+=['## Decisão e limites','',f'Estado: `{decision["status"]}`. O checkpoint principal '
      'permanece `rsi100/checkpoints/best.pt`. A matriz anterior e a nova candidata foram '
      'salvas separadamente. Nenhuma saída do MBPP foi usada para mudar a edição.','',
      'Oito problemas não medem competência geral. Os datasets são públicos e antigos; '
      'contaminação de pré-treino é desconhecida. O HumanEval está descontinuado a montante, '
      'e o MBPP é em geral básico, embora este recorte escolha tarefas maiores de programação '
      'dinâmica/combinatória. Três asserts do MBPP e os checks do HumanEval não provam correção '
      'em toda entrada possível. O ganho no conjunto ensinado pode ser memorização ou especialização.','',
      'Não foram usados os 40 testes finais/32 validações restantes do estudo 013, nem os '
      'conjuntos reservados do RSI100. Não houve comparação com 4B ou aceleração DSpine. '
      'Ver supervised014/PROTOCOL.md, NOTICE.md, frozen.json, teaching.json e as saídas por ID.']
    (ROOT/'DIRECT_BENCHMARK_REPORT.md').write_text('\n'.join(lines)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
