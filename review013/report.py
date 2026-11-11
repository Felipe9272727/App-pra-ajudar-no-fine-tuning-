"""Summarize immutable outputs without altering prompts, golds or selection."""
import collections,hashlib,json,math,random,statistics
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
def read(p):return json.loads((HERE/p).read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def paired(parent,child):
    p={r['id']:r for r in parent};g=[];l=[];cg=cl=0;changes=[];byfamily=collections.defaultdict(list)
    for r in child:
        b=p[r['id']];d=int(r['all_passed'])-int(b['all_passed']);byfamily[r['family']].append(d)
        if d>0:g.append(r['id'])
        if d<0:l.append(r['id'])
        cg+=sum(not a and b0 for a,b0 in zip(b['case_passed'],r['case_passed']))
        cl+=sum(a and not b0 for a,b0 in zip(b['case_passed'],r['case_passed']))
        if r['output']!=b['output']:changes.append(r['id'])
    n=len(g)+len(l);pvalue=sum(math.comb(n,k) for k in range(len(g),n+1))/(2**n) if n else 1.
    families=list(byfamily.values());rng=random.Random(20261111);boot=[]
    for _ in range(10000):
        sample=[x for _ in families for x in rng.choice(families)];boot.append(100*sum(sample)/len(sample))
    boot.sort()
    return {'task_gains':g,'task_losses':l,'case_gains':cg,'case_losses':cl,'output_text_changed':changes,
      'task_delta_pp':100*(len(g)-len(l))/len(parent),'paired_task_exact_one_sided_p':pvalue,
      'family_cluster_bootstrap_95_ci_pp':[boot[250],boot[9750]],'families':len(families),
      'limitations':'Four families, two correlated parameter variants each. Degenerate CI does not establish equivalence. Cases are not independent tasks.'}

def main():
    variants=['original','parent','loop','joint'];result={'models':{},'comparisons_vs_parent':{}}
    selection=read('selection.json');fit=read('fit.json');teach=read('teaching_progress.json');mechanism=read('mechanism.json')
    base=read('screen_parent.json');pc=read('controls_parent.json');baseline_controls={r['id']:r for r in pc['rows']}
    train_baseline=[r for r in teach['rows'] if r['id'].endswith(('_0','_9'))]
    result['parent_training_diagnostic']={'examples':len(train_baseline),'mean_task_nll':statistics.mean(r['nll'] for r in train_baseline),
                 'mean_task_token_accuracy':statistics.mean(r['teacher_forced_top1'] for r in train_baseline),'source':'same completed teaching captures; no repeated model calls'}
    for kind in variants:
        s=read('screen_'+kind+'.json');c=read('controls_'+kind+'.json');assert s['status']==c['status']=='complete'
        result['models'][kind]={'tasks_passed':s['tasks_passed'],'tasks_total':s['total'],'cases_passed':s['cases_passed'],
             'cases_total':s['cases_total'],'controls_correct':c['correct'],'controls_total':c['total'],
             'anchor_nll':c['language_anchor_nll']['mean_nll'],'new_tokens':sum(r['new_tokens'] for r in s['rows']),
             'generation_seconds':sum(r['seconds'] for r in s['rows']),'truncations':sum(r['hit_limit'] for r in s['rows']),
             'failure_categories':dict(collections.Counter(r['category'] for r in s['rows'])),
             'control_losses_vs_parent':[r['id'] for r in c['rows'] if baseline_controls[r['id']]['correct'] and not r['correct']]}
        if kind in ['loop','joint']:
            result['comparisons_vs_parent'][kind]=paired(base['rows'],s['rows'])
            d=read('learning_diagnostic_'+kind+'.json');result['models'][kind]['training_diagnostic']={k:d[k] for k in ['mean_task_nll','mean_task_token_accuracy']}
    result['selection']=selection;result['fit']=fit
    (HERE/'comparison.json').write_text(json.dumps(result,indent=2)+'\n')
    labels={'original':'Qwen original','parent':'Liquid Sense anterior','loop':'Adaptador de loop','joint':'Adaptador de loop + temporal'}
    lines=['# Aprendizagem supervisionada do loop — estudo 013','',
      'Usei soluções corretas na aprendizagem, conforme a nova orientação do usuário. '
      'O teste de programação recebeu apenas os enunciados, sem soluções, casos de teste ou feedback. '
      'Este relatório compara saídas reais; o ajuste interno, sozinho, não comprova ganho de capacidade.','',
      '## O que foi implementado','',
      'Foram criados 200 problemas parametrizados em 20 famílias: 120 para ensino, 40 para validação '
      'e 40 para teste final. Todos os programas de referência passaram nos 4.000 casos executados '
      'no sandbox. A divisão é por família; não há AST de solução idêntica entre conjuntos. '
      'São apenas 20 famílias customizadas, com variantes correlacionadas, não 200 algoritmos independentes.','',
      f'Os 120 programas de ensino forneceram {teach["total_tokens"]} tokens de solução/EOS. '
      f'Foram amostradas {fit["sampled_decisions"]} decisões, das quais {fit["targets_nonzero"]} '
      'tinham um token previsto diferente do token correto. Os programas foram escritos pelo pesquisador '
      'e verificados por oráculos executáveis; não houve API professora externa nem custo de API registrado.','',
      'Dois adaptadores de posto 16 foram ajustados por PCA e regressão ridge, sem gradientes, '
      'backward, otimizador ou SFT/LoRA. Um usa a diferença entre as duas passagens; o outro também '
      'usa um filtro causal de sete posições. Ambos atuam somente na saída da segunda visita da '
      'camada física 27. A direção-alvo vem dos embeddings do token correto e do token produzido. '
      'Transportá-la para esse ponto aproxima as quatro camadas restantes por uma identidade: '
      'essa é uma hipótese local e pode estar errada.','',
      'O modelo mantém 32 camadas físicas, 56 execuções, mHC de duas vias e os operadores DeltaNet '
      'e janelas locais anteriores. Os 699 tensores do pai não foram alterados; os novos parâmetros '
      'são 32.768 e 49.152, respectivamente. Os pesos dos roteadores e convoluções anteriores '
      'não foram treinados neste piloto. O filtro novo é uma adaptação temporal inspirada em Liquid, '
      'não uma reprodução integral da arquitetura Liquid AI.','',
      '## Comparação por geração livre','',
      'A triagem congelada contém oito problemas novos de quatro famílias da validação. '
      'Ela já está observada e não pode ser reapresentada como teste final. Todas as variantes '
      'usaram os mesmos enunciados, tokenizer, limite de 160 tokens, geração gulosa, seed 0, '
      'thinking desativado, cache, kernels eager e quatro threads. Pai e candidatas compartilham '
      'a mesma profundidade; o Qwen original executa 24 camadas, portanto não há igualdade de FLOPs.','',
      '| Modelo | Tarefas completas | Casos corretos | Controles | NLL de linguagem |',
      '|---|---:|---:|---:|---:|']
    for kind in variants:
        r=result['models'][kind];lines.append(f'| {labels[kind]} | {r["tasks_passed"]}/{r["tasks_total"]} | {r["cases_passed"]}/{r["cases_total"]} | {r["controls_correct"]}/{r["controls_total"]} | {r["anchor_nll"]:.6f} |')
    lines+=['','Os controles incluem quatro questões anteriores e oito questões novas de linguagem e '
       'raciocínio. As 12 âncoras de NLL são antigas e servem apenas à retenção. Os gabaritos e '
       'o extrator de código permaneceram iguais. Código com sintaxe inválida ou variável não '
       'definida foi contado como erro, sem reparo automático.','']
    for kind in ['loop','joint']:
        p=result['comparisons_vs_parent'][kind];d=result['models'][kind]['training_diagnostic'];f=fit['candidates'][kind]
        lines.append(f'{labels[kind]} versus pai: {len(p["task_gains"])} tarefas ganhas, '
          f'{len(p["task_losses"])} perdidas; {p["case_gains"]} casos ganhos e {p["case_losses"]} perdidos. '
          f'{len(p["output_text_changed"])} textos mudaram. NLL nos mesmos 24 exemplos de ensino: '
          f'{result["parent_training_diagnostic"]["mean_task_nll"]:.6f} → {d["mean_task_nll"]:.6f}. '
          f'O MSE do alvo local caiu {100*(1-f["fit_mse"]/f["zero_predictor_mse"]):.2f}%; '
          'isso mede ajuste ao sinal de ensino, não acerto em problemas novos.')
        lines.append('')
    lines+=['## Decisão e limites','',
        f'Decisão registrada: `{selection["status"]}`. Checkpoint principal preservado: '
        '`rsi100/checkpoints/best.pt`, SHA256 '
        '`46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8`. '
        'As candidatas, seus estados de construção e as saídas foram preservados como experimentos.','',
        'A geração é determinística; repetir a mesma resposta não cria novas amostras independentes. '
        'A comparação pareada, p-valor por tarefa e bootstrap por família estão em review013/comparison.json. '
        'Há apenas quatro famílias na triagem; intervalos degenerados não provam equivalência. '
        'O conjunto foi criado pelo mesmo pesquisador que propôs a edição, sem auditoria cega externa. '
        'Não se pode garantir novidade perante o pré-treino ou generalização ampla.','',
        'Alterar estados ou usar duas passagens não demonstra revisão semântica de erros. '
        'O adaptador aprendeu uma aproximação de correção de tokens em prefixos corretos; '
        'isso não elimina a diferença entre esses prefixos e os erros que ele próprio gera. '
        'Não foi adicionada terceira passagem neste estudo: o protocolo exige ganho na segunda antes '
        'de ampliar o custo. Não foi feita comparação executada com 4B ou implementado DSpine.','',
        'Ver STATUS_RECUPERACAO.md, PLANO_DSPINE.md e review013/PROTOCOL.md. '
        'O programa review013/run_study.py é limitado e serial; não é um processo permanente.']
    if selection['status']=='complete_both_rejected_screen':
        lines+=['','Os 40 problemas finais e os outros 32 problemas de validação não foram executados '
            'para seleção após a falha da triagem. Os conjuntos antigos reservados também continuam fechados.']
    (ROOT/'EXPERIMENTOS_CAPACIDADE.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(result['models'],indent=2))

if __name__=='__main__':main()
