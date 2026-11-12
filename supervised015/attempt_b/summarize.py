"""Report trained-target fit separately from diagnostic transfer and retention."""
import json,hashlib,statistics,sys,collections
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT))
from supervised014.summarize import paired
from supervised014.judge import extract

def read(p):return json.loads(Path(p).read_text())
def sh(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    for file,h in read(HERE/'evaluation_frozen.json').items():assert sh(ROOT/file)==h,file
    training=read(HERE/'training_complete.json');integrity=read(HERE/'integrity.json')
    models={k:v for k,v in read(ROOT/'supervised014/summary.json')['models'].items()}
    current={};reports={}
    for role in ['target','transfer','controls']:
        r=read(HERE/(role+'_specialist.json'));assert r['status']=='complete';reports[role]=r
        if role=='controls':m={'correct':r['correct'],'total':r['total'],'nll':r['anchor_nll']['mean_nll']}
        else:m={'solved':r['tasks_passed'],'total':r['total'],'test_groups_passed':r['test_groups_passed'],
          'test_groups_total':r['test_groups_total'],'truncations':sum(x['hit_limit'] for x in r['rows']),
          'tokens':sum(x['new_tokens'] for x in r['rows']),'seconds':sum(x['seconds'] for x in r['rows']),
          'categories':dict(collections.Counter(x['category'] for x in r['rows']))}
        current['taught' if role=='target' else role]=m
    models['specialist']=current
    comparisons={role:paired(read(ROOT/('supervised014/'+('taught' if role=='target' else role)+'_parent.json'))['rows'],reports[role]['rows']) for role in ['target','transfer']}
    controls={r['id']:r for r in read(ROOT/'supervised014/controls_parent.json')['rows']}
    control_losses=[r['id'] for r in reports['controls']['rows'] if controls[r['id']]['correct'] and not r['correct']]
    control_gains=[r['id'] for r in reports['controls']['rows'] if not controls[r['id']]['correct'] and r['correct']]
    rows={r['id']:r for r in read(HERE/'train.json')}
    exact=[r['id'] for r in reports['target']['rows'] if extract(r['output'])==rows[r['id']]['solution'].strip()]
    tf=lambda items:{'mean_task_nll':statistics.mean(r['nll'] for r in items),'correct_tokens':sum(r['correct_tokens'] for r in items),'total_tokens':sum(r['tokens'] for r in items),'minimum_gold_margin':min(r['minimum_gold_margin'] for r in items)}
    gain=current['taught']['solved']>models['parent']['taught']['solved']
    decision={'status':'experimental_target_specialist_preserved' if gain else 'specialist_failed_target_gain_parent_retained',
      'checkpoint_promoted':False,'principal_unchanged':True,'specialist_path':'supervised015/attempt_b/checkpoints/final/manifest.json',
      'selected_general_checkpoint':'rsi100/checkpoints/best.pt','parent_sha256':training['parent_sha256'],
      'target_is_intentionally_trained_on':True,'transfer_previously_observed':True,'transfer_used_for_refitting':False,
      'general_or_larger_model_superiority_demonstrated':False,'control_losses':control_losses,'control_gains':control_gains,
      'language_nll_delta':current['controls']['nll']-models['parent']['controls']['nll']}
    result={'models':models,'comparisons_vs_parent':comparisons,'decision':decision,'teacher_forcing':{'initial':tf(training['initial_teacher_forcing']),'final':tf(training['final_teacher_forcing'])},
      'exact_reference_program_reproductions':exact,'training':{k:training[k] for k in ['eligible_tensors','eligible_parameters','optimizer_steps','epochs','changed_text_tensors','changed_scalar_values','checkpoint_compressed_bytes','checkpoint_stream_sha256','vision_tensors_unchanged']},
      'interrupted_attempt_a':read(HERE.parent/'attempt_a_stop.json'),'checkpoint_cold_restore_verified':integrity['status'],'known_counterexample':read(HERE/'known_counterexample.json')}
    (HERE/'summary.json').write_text(json.dumps(result,indent=2)+'\n');(HERE/'selection.json').write_text(json.dumps(decision,indent=2)+'\n')
    labels={'original':'Qwen original','parent':'Liquid Sense principal','edited':'Edição014 (rejeitada)','specialist':'Liquid Sense SFT015 especialista'}
    lines=['# Treino supervisionado de todos os pesos de texto — estudo015','',
      'A autorização explícita do usuário para gradientes/backpropagation permitiu ajustar todos os pesos ativos de texto. O objetivo deste estudo é especializar o modelo nos oito problemas HumanEval já escolhidos no014. Isso não produz uma avaliação independente do HumanEval nem evidencia superioridade sobre modelos maiores.','',
      '| Modelo | HumanEval ensinado | MBPP diagnóstico | Controles | NLL linguagem |','|---|---:|---:|---:|---:|']
    for k,m in models.items():lines.append(f'| {labels[k]} | {m["taught"]["solved"]}/8 | {m["transfer"]["solved"]}/8 | {m["controls"]["correct"]}/12 | {m["controls"]["nll"]:.6f} |')
    t=result['training'];lines+=['',f'Foram elegíveis {t["eligible_tensors"]} tensores/{t["eligible_parameters"]:,} parâmetros de texto. Na tentativa B, {len(training["ever_nonzero_gradient_tensors"])} tensores receberam gradientes não nulos; a comparação binária confirmou mudança em {t["changed_text_tensors"]} tensores e {t["changed_scalar_values"]:,} valores. Os153 tensores de visão permaneceram idênticos. Isso não significa que exista um subconjunto conhecido dedicado exclusivamente à programação.','',
      f'Tentativa B: Adafactor com taxa relativa .001, batch2, {t["optimizer_steps"]} atualizações/{t["epochs"]} épocas. A tentativa A com .01 foi interrompida após11 atualizações e degradação da perda de treino; seus logs/fontes estão preservados, mas seus pesos intermediários em memória não foram salvos e não receberam nota de geração. A mudança de taxa constitui uma revisão declarada do protocolo inicial.','',
      f'Teacher forcing: {result["teacher_forcing"]}. Programas gerados literalmente iguais às soluções ensinadas: {len(exact)}/8. Esses diagnósticos medem ajuste aos exemplos; a pontuação na tabela vem da execução dos programas gerados livremente.','',
      'A arquitetura mantém32 camadas físicas,56 execuções por token,24 camadas intermediárias visitadas duas vezes, mHC com dois fluxos, convoluções de sete posições e atenção local256. Os ganhos de visita continuam positivos e normalizados. A auditoria registra ganhos e normas dos roteadores; presença ou mudança desses mecanismos não prova raciocínio melhor.','',
      'Condições: mesmos enunciados, tokenizer, BF16, cache, kernels eager, geração gulosa/seed0, thinking desligado, quatro threads e limite320 tokens para código/64 para controles. Nenhuma solução privada ou teste foi inserido nos prompts de avaliação. Exemplos públicos dos enunciados continuam presentes. Os programas não foram reparados; o extrator e os gabaritos são os mesmos do014. Não há igualdade de FLOPs entre original e híbrido. As referências original/pai foram reutilizadas do014 e seus hashes foram verificados; tempos entre sessões não demonstram aceleração.','',
      'HumanEval:32,39,75,114,119,129,132,147. MBPP:129,239,245,247,306,392,407,463. São subconjuntos de oito tarefas, não benchmarks completos. MBPP ficou fora do treino, mas seus resultados já tinham sido observados no014; não é um teste final inédito e não foi usado para selecionar estes pesos. Os antigos conjuntos reservados continuam fechados.','',
      f'Comparações pareadas: {comparisons}. Os intervalos/p-valores são apenas descritivos destes pequenos conjuntos. Significância no conjunto ensinado não comprova generalização.','',
      f'Controles perdidos: {control_losses}; ganhos: {control_gains}; variação da NLL de linguagem: {decision["language_nll_delta"]:+.6f}. Os textos completos preservam a distinção entre falha de formato e falha semântica; o gabarito exato não foi ajustado.','',
      'O contraexemplo de quadrado mágico já conhecido foi avaliado separadamente. Seu resultado está em known_counterexample.json e não altera os três testes oficiais do MBPP.','',
      f'Decisão: `{decision["status"]}`. O principal continua `rsi100/checkpoints/best.pt`; o especialista é experimental e separado. Todos os pesos do especialista são recuperáveis por XOR binário sem perdas contra o pai imutável, com hashes por tensor/parte e verificação de restauração a frio. Não se infere melhoria geral, aprendizado de pensamento ou desempenho contra4B a partir desta especialização.','',
      'Reprodução, estado e hashes: supervised015/attempt_b/REPRODUCE.md, summary.json, integrity.json e checkpoints/final/manifest.json. Todos os relatórios e checkpoints anteriores foram preservados.']
    (ROOT/'SUPERVISED_TEXT_REPORT.md').write_text('\n'.join(lines)+'\n')
    (HERE/'status.json').write_text(json.dumps({'status':'complete_pending_durable_publication','model_process_active':False,'checkpoint_promoted':False,'parent_unchanged':True,'process_continues_in_background':False},indent=2)+'\n')
    print(json.dumps({'models':models,'decision':decision,'training':t}))
if __name__=='__main__':main()
