"""Completed epoch comparisons and honest promotion decision."""
import json,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parent

def read(p):return json.loads((H/p).read_text())
def save(p,v):(H/p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def main():
    from decide import compare
    selection=read('selection.json');names=['original','parent']+[f'epoch{i:02d}' for i in range(1,5)]
    reports={v:read('reports/validation_'+v+'.json') for v in names}
    assert all(r['status']=='complete' for r in reports.values())
    with (ROOT/'rsi100/checkpoints/best.pt').open('rb') as f:parent=hashlib.file_digest(f,'sha256').hexdigest()
    assert parent==read('config.json')['parent_sha256']
    steps=[json.loads(x) for x in (H/'steps.jsonl').read_text().splitlines()];assert [s['step'] for s in steps]==list(range(1,193));assert steps[-1]['sft_target_tokens']==10796
    selected=selection['selected'];final=None;promote=False
    if selected:
        fs={v:read('reports/final_'+v+'.json') for v in ['original','parent',selected]};assert all(r['status']=='complete' for r in fs.values())
        final={'comparison':compare(fs['parent'],fs[selected]),'summaries':{v:r['summary'] for v,r in fs.items()}};promote=final['comparison']['eligible']
    else:assert not list((H/'reports').glob('final_*.json'))
    out={'status':'complete','new_epochs':4,'updates':192,'target_token_presentations':10796,
        'starting_checkpoint':'rsi100/checkpoints/best.pt','parent_sha256':parent,
        'principal_file_unchanged':True,'apk_changed':False,'all_model_workers_closed':True,
        'selected_validation_epoch':selected,'validated_research_candidate':selected if promote else None,
        'final_queried':selected is not None,'final':final,'selection':selection,
        'fresh_validation':{v:r['summary'] for v,r in reports.items()},'scope':'small custom pilot; not general intelligence or4B comparison'}
    save('summary.json',out)
    lines=['# Native029 — quatro épocas do melhor checkpoint geral','',
        'Resultado: '+('candidato passou os dois gates do piloto.' if promote else 'nenhuma candidata promovida; checkpoint geral anterior mantido.'),'',
        'O melhor selecionado era o pai geral46f6697, não uma das versões028rejeitadas. Foram quatro épocas NOVAS, com otimizador novo; não seis épocas acumuladas numa versão inferior. Nenhum experimento antigo foi reiniciado.','',
        '## Treino real','',
        '192atualizações,10796apresentações de tokens-alvo sobre48problemas em duas formas(com/semthinking). Os mesmos150fatores de baixo posto(rank8,5111808valores) e276controladores nativos(2202864valores), compartilhados nas duas visitas reais, foram treinados juntos.32camadas/56execuções,mHC2,conv7 e janelas256 preservados. Embeddings/head,camadas externas e visão congelados.','',
        'Para reduzir a regressão028, lr dos fatores5e-5/controladores1.25e-5(um quarto) e KLdo pai1.0(antes0.3). Essas mudanças foram fixadas antes do treino; não é uma comparação que isola apenas o número de épocas. Sem PPO. Toda época preserva otimizador,RNG e699hashes nativos fundidos.','',
        '## Validação inédita','',
        'Quatro famílias novas/20casos. Semthinking128tokens código/48gerais; comthinking192tokens totais. Oito gerais no primeiro modo,primeiros quatro no segundo. Greedy,BF16nativo,cache,4threads e mesmos prompts em todas as versões. As duas formas de uma pergunta não são problemas independentes. Nenhuma solução ou caso oculto entrou nos prompts.','',
        '| Versão | Código sem thinking | Casos | Gerais | Código com thinking | Casos | Gerais |','|---|---:|---:|---:|---:|---:|---:|']
    for v,r in reports.items():
        a=r['summary']['False'];b=r['summary']['True'];lines.append(f'| {v} | {a["code_tasks"]}/4 | {a["cases"]}/20 | {a["general_correct"]}/8 | {b["code_tasks"]}/4 | {b["cases"]}/20 | {b["general_correct"]}/4 |')
    lines+=['','## Preservação dos acertos conhecidos','',
        'As4tarefas e8controles028já observados foram avaliados separadamente como LEGACY. Não são ganho independente. A repetição do pai neste estudo '+('coincidiu' if selection['historical_parent_reference_match'] else 'NÃO coincidiu')+' com os IDs e acertos históricos. Os gates exigem preservar cada caso/controle correto, além de aumentar tarefas completas na validação nova; NLL ou fechamento de pensamento não podem selecionar pesos.','',
        '| Época | Elegível | Casos/controles novos perdidos | Casos/controles conhecidos perdidos |','|---|---:|---:|---:|']
    for v,c in selection['checks'].items():lines.append(f'| {v} | {c["eligible"]} | {len(c["fresh"]["lost_parent_correct_cases_or_controls"])} | {len(c["known_retention"]["lost_parent_correct_cases_or_controls"])} |')
    lines+=['','O teste final028, nunca consultado ao modelo, foi preservado como final reservado029. '+('Foi aberto somente para o vencedor congelado; ver summary.json.' if selected else 'Continuou fechado porque nenhuma época passou os gates.'),'',
        '## Limites e preservação','',
        'Piloto curto e pequeno, não demonstra ganho geral de inteligência, superioridade4B, raciocínio extenso do app ou velocidade sem perda. Terminar respostas mais cedo não basta. Artefatos e resultados negativos preservados; o pai e o APK não foram sobrescritos. Workers encerrados.']
    (H/'REPORT.md').write_text('\n'.join(lines)+'\n')
    s=read('status.json');s.update(status='complete',model_process_active=False,validated_research_candidate=out['validated_research_candidate'],selected_validation_epoch=selected,final_set_queried=selected is not None,parent_weights_changed=False,optimizer_updates=192);save('status.json',s)
    print('REPORT029_COMPLETE',out['validated_research_candidate'])
if __name__=='__main__':main()
