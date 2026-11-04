"""Write the experimental V3 report after every final generation is saved."""
import json
import statistics
from runtime import *


def main():
    frozen=json.loads((HERE/'frozen.json').read_text())
    reports={v:json.loads((HERE/f'heldout_{v}.json').read_text()) for v in ['qwen_original','v2_parent','v3_ncm']}
    assert all(r['status']=='complete' and r['data_sha256']==DATA_HASH for r in reports.values())
    expected=[r['id'] for r in fresh_heldout()]
    assert all([r['id'] for r in report['rows']]==expected for report in reports.values())
    assert reports['v3_ncm']['head_sha256']==frozen['checkpoint_sha256']
    summary={}
    for key,r in reports.items():
        summary[key]={k:r[k] for k in ['exact_correct','content_correct','total','loaded_parameters','byte_accuracy','peak_rss_mib']}
        summary[key]['total_generation_seconds']=sum(row['seconds'] for row in r['rows'])
        summary[key]['mean_generation_seconds']=statistics.mean(row['seconds'] for row in r['rows'])
        summary[key]['empty_outputs']=sum(not row['output'].strip() for row in r['rows'])
        summary[key]['by_family']={}
        for family in sorted({row['family'] for row in r['rows']}):
            rows=[row for row in r['rows'] if row['family']==family]
            summary[key]['by_family'][family]={'exact_correct':sum(row['exact_correct'] for row in rows),'total':len(rows)}
        for group in ['id','ood']:
            rows=[row for row in r['rows'] if row['ood']==(group=='ood')]
            summary[key][group]={'exact_correct':sum(row['exact_correct'] for row in rows),'total':len(rows)}
    v3=summary['v3_ncm'];original=summary['qwen_original'];parent=summary['v2_parent']
    conclusion=('A V3 teve mais acertos neste conjunto restrito; isso não prova melhora geral.' if v3['exact_correct']>original['exact_correct'] else
        'A V3 não superou o Qwen de referência neste conjunto. Não promover como melhoria geral.')
    recovery=json.loads((HERE/'reference_verification.json').read_text())
    overall={'status':'EXPERIMENTO_COMPLETE','model_name':frozen['model_name'],
        'scores':summary,'data_sha256':DATA_HASH,'selected_head':frozen['selected_head'],
        'selection_used_test':False,'reference_reconstructed':True,'reference_probe':recovery,
        'conclusion':conclusion,'backward_passes':0,'automatic_promotion':False}
    atomic_json(HERE/'results.json',overall)
    names={'qwen_original':'Qwen: tensores reconstruídos','v2_parent':'Pai V2 candidata 2: SenseNova + Liquid',
           'v3_ncm':'V3 NCM adaptado — EXPERIMENTO'}
    lines=['# V3 NCM — EXPERIMENTO: resultados reais','',conclusion,'',
        f'## Comparação em {len(expected)} perguntas novas','',
        '| Modelo | Acerto exato | Conteúdo | Tempo médio por resposta | Parâmetros carregados |',
        '|---|---:|---:|---:|---:|']
    for k,s in summary.items():
        lines.append(f"| {names[k]} | {s['exact_correct']}/{s['total']} | {s['content_correct']}/{s['total']} | {s['mean_generation_seconds']:.3f} s | {s['loaded_parameters']:,} |")
    lines+=['','Todos os resultados são de geração real; respostas incorretas ou vazias foram conservadas. '
        'O conjunto é customizado e pequeno, com aritmética, saída de Python e transformação de strings. '
        'Não é uma medida de capacidade geral de conversa ou de inteligência.','',
        f"A V3 produziu {v3['empty_outputs']} respostas vazias em {v3['total']} casos. O codec sozinho reconstruiu as respostas de treino, mas o gerador condicionado não reproduziu essa capacidade na geração livre.",'',
        '## Por família e distribuição','',
        '| Família | Qwen reconstruído | Pai V2 | V3 |','|---|---:|---:|---:|']
    for family in summary['v3_ncm']['by_family']:
        values=[f"{summary[v]['by_family'][family]['exact_correct']}/{summary[v]['by_family'][family]['total']}" for v in reports]
        lines.append('| '+family+' | '+' | '.join(values)+' |')
    for group in ['id','ood']:
        values=[f"{summary[v][group]['exact_correct']}/{summary[v][group]['total']}" for v in reports]
        lines.append('| '+group+' | '+' | '.join(values)+' |')
    archive=json.loads((HERE/'archive.json').read_text())
    lines+=['','## Seleção antes do teste','',
        '| Candidata de cabeça NCM | Ridge | Desenvolvimento: acertos | Acurácia de bytes |',
        '|---|---:|---:|---:|']
    for h in archive['heads']:
        lines.append(f"| {h['id']} | {h['ridge']} | {h['exact_correct']}/{h['total']} | {h['byte_accuracy']:.4f} |")
    lines+=['',f"Cabeça selecionada: **{frozen['selected_head']}**, congelada em `frozen.json` antes do teste.",
        'O teste não escolhe pesos e não promove a V3. O pai é a candidata 2 ainda experimental da V2.','',
        '## O que esta V3 efetivamente contém','',
        '- Backbone SenseNova/Liquid ativo: 32 camadas físicas, 56 execuções, mHC de duas vias, ganho da segunda visita 0,05, convolução de sete posições e SWA256.',
        '- Autoencoder linear de bytes aprendido: PCA no encoder, codebooks RVQ do código oficial NCM aprendidos por k-means e decoder por ridge.',
        '- Quatro níveis de códigos: 1, 2, 4 e 8 posições. Cada nível prevê todos os seus códigos em uma passagem do híbrido.',
        '- Matrizes de previsão de códigos aprendidas por solução fechada em 128 exemplos, com 10% de corrupção dos conceitos anteriores no treino.',
        '- Zero backward passes. Não há calculadora, gabarito ou modelo externo na inferência da V3; não há fallback autoregressivo escondido.',
        '- Limite: oito bytes de resposta. O modelo oficial NCM usa um VQ-VAE e um gerador treinados de outra forma; esta é uma adaptação estrutural e não sua reprodução completa.','',
        '## Limites da referência e da comparação','',
        'O download grande do upstream não ficou disponível neste ambiente. Recuperamos o port v1 salvo e sem treino, '
        'invertendo as escalas de saída, todas potências de dois, para reconstruir os 24 conjuntos de tensores Qwen. '
        'As cópias duplicadas coincidem bit a bit. O arquivo safetensors resultante tem hash diferente do upstream.','',
        f"Uma sonda histórica teve NLL {recovery['original_recorded_nll']:.6f}; a referência recuperada teve {recovery['recovered_nll']:.6f}.",
        'Não atribuímos essa diferença automaticamente ao hardware ou ao formato. A referência é identificada como reconstruída; '
        'esta limitação impede tratar a execução como uma reprodução byte a byte do checkpoint oficial. '
        'Todas as variantes foram medidas novamente no mesmo ambiente.','',
        'O Qwen e o pai geram até oito tokens BPE; a V3 usa quatro níveis, um prefill e 15 consultas de byte, '
        'com todos os gabaritos cabendo nas duas formas. Computação e unidades de saída não são iguais. '
        'Os tempos são medidos junto da qualidade, sem extrapolar os ganhos do artigo NCM em H100.','',
        '## Respostas completas','',
        '| ID | Esperado | Qwen reconstruído | Pai V2 | V3 |','|---|---|---|---|---|']
    def esc(s):return s.replace('|','\\|').replace('\n',' / ').replace('\r',' ')
    for i,row in enumerate(fresh_heldout()):
        texts=[esc(reports[k]['rows'][i]['output']) for k in reports]
        lines.append('| '+row['id']+' | '+row['answer']+' | '+' | '.join(texts)+' |')
    lines+=['','Os JSONs preservam tempos, traços dos níveis NCM, perguntas, gabaritos e hashes. '
        'Estado final: EXPERIMENTO concluído e salvo, sem promoção automática ou processo permanente de treino.']
    (HERE/'RESULTADOS.md').write_text('\n'.join(lines)+'\n')
    checkpoint={**frozen,'status':'EXPERIMENTO_COMPLETE','results':'v3_experiment/results.json',
        'report':'v3_experiment/RESULTADOS.md','loaded_parameters':v3['loaded_parameters'],
        'base_revision':'2fc06364715b967f1860aea9cf38778875588b17',
        'ncm_source_revision':'c70274273f489abc73832b2b98584a8483b6b203',
        'original_recovery':'v3_experiment/original_recovery.json','automatic_promotion':False}
    atomic_json(ROOT/'checkpoints/v3_ncm_experiment.json',checkpoint)
    status(status='EXPERIMENTO_COMPLETE',model_process_active=False,evaluating=None,
        results='v3_experiment/results.json',automatic_promotion=False)
    print(json.dumps(overall,indent=2),flush=True)


if __name__=='__main__':main()
