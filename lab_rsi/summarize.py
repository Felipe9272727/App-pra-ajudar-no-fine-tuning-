"""Generate the report only after all frozen final evaluations are complete."""
import json
import math
from common import *


def main():
    frozen=json.loads((HERE/'frozen.json').read_text())
    variants=['original','baseline']+(['selected'] if frozen['patch'] else [])
    reports={v:json.loads((HERE/f'heldout_{v}.json').read_text()) for v in variants}
    assert all(r['status']=='complete' and r['data_sha256']==DATA_HASH for r in reports.values())
    archive=json.loads((HERE/'archive.json').read_text())
    fit=json.loads((HERE/'fit_metadata.json').read_text())
    devbase=json.loads((HERE/'development_baseline.json').read_text())
    names={'original':'Qwen3.5-0.8B original','baseline':'Híbrido SenseNova + Liquid antes do novo ajuste',
           'selected':'liquid sense 0.8 b LOOP após ajuste aceito'}
    summary={}
    for key,report in reports.items():
        rows=report['rows'];numeric=[r for r in rows if r['numeric']];controls=[r for r in rows if not r['numeric']]
        summary[key]={'exact':report['exact_correct'],'content':report['content_correct'],'total':report['total'],
            'numeric_exact':sum(r['exact_correct'] for r in numeric),
            'numeric_content':sum(r['content_correct'] for r in numeric),'numeric_total':len(numeric),
            'general_exact':sum(r['exact_correct'] for r in controls),'general_total':len(controls),
            'generation_limit_hits':sum(r['hit_limit'] for r in rows),
            'amortized_generation_seconds':sum(r['amortized_seconds'] for r in rows),
            'loaded_parameters':report['loaded_parameters']}
    final='selected' if frozen['patch'] else 'baseline'
    a=reports['original']['rows'];b=reports[final]['rows']
    wins=sum(not x['content_correct'] and y['content_correct'] for x,y in zip(a,b))
    losses=sum(x['content_correct'] and not y['content_correct'] for x,y in zip(a,b))
    discordant=wins+losses
    p=min(1.,2*sum(math.comb(discordant,i) for i in range(min(wins,losses)+1))/2**discordant) if discordant else 1.
    overall={'model_name':'liquid sense 0.8 b LOOP','status':'complete','data_sha256':DATA_HASH,
        'selected_candidate':frozen['candidate_id'],'scores':summary,
        'paired_content_vs_original':{'wins':wins,'losses':losses,'exact_binomial_two_sided_p':p},
        'selection_used_final_test':False,'backward_passes':0,
        'interpretation':'Small custom benchmark; no claim of general intelligence improvement or autonomous RSI'}
    atomic_json(HERE/'summary.json',overall)
    descriptor='Uma candidata passou pelos critérios de desenvolvimento e validação.' if frozen['patch'] else (
        'Nenhuma nova edição densa passou pelos critérios registrados. O checkpoint final mantém o híbrido com SenseNova e Liquid ativos.')
    lines=['# liquid sense 0.8 b LOOP — segundo piloto', '',descriptor,'',
        'Os pesos foram realmente ajustados e avaliados. Não houve backward/autograd nem calculadora na inferência. '
        'O assistente controlou os experimentos; isso não demonstra RSI autônomo geral.','',
        '## Comparação final nova — 64 perguntas','',
        '| Modelo | Formato exato | Conteúdo | Numérico/código (conteúdo) | Controles gerais |',
        '|---|---:|---:|---:|---:|']
    for key,s in summary.items():
        lines.append(f"| {names[key]} | {s['exact']}/64 | {s['content']}/64 | {s['numeric_content']}/48 | {s['general_exact']}/16 |")
    lines+=['','| Família | '+' | '.join(names[v] for v in variants)+' |',
        '|---|'+'---:|'*len(variants)]
    for family in ['addition','subtraction','multiplication','python','general_control']:
        entries=[]
        for v in variants:
            family_rows=[r for r in reports[v]['rows'] if r['family']==family]
            entries.append(f"{sum(r['content_correct'] for r in family_rows)}/{len(family_rows)}")
        lines.append('| '+family+' | '+' | '.join(entries)+' |')
    lines+=['',f'Comparação pareada de conteúdo, original → checkpoint final: {wins} melhora(s), {losses} regressão(ões). '
        f'Teste binomial exato nos pares discordantes: p={p:.4f}. As perguntas compartilham templates; '
        'esse número é descritivo e não estabelece significância em capacidades gerais.','',
        'O teste final não escolheu pesos. O checkpoint foi congelado antes de observar essas respostas. '
        'Os resultados anteriores de 24 perguntas estão em PILOT_REPORT.md e não são comparáveis diretamente a este conjunto.','',
        '## O que foi aprendido por edição direta','',
        f"- {fit['training_examples']} exemplos sintéticos com respostas verificadas por código.",
        f"- {fit['training_token_positions']} posições supervisionadas e {fit['anchor_positions']} posições de preservação.",
        f"- {fit['wrong_token_positions']} posições tinham o próximo token preferido diferente do alvo.",
        '- A matriz existente `layers.31.mlp.down_proj.weight` recebe um delta obtido por regressão ridge fechada.',
        '- Fatores de posto 32 comprimem o checkpoint; são multiplicados e escritos na matriz densa ao carregar. Não há adaptador adicional na inferência.',
        '- Correções conjuntas, correções de dígitos e controle só de parada foram definidos antes das avaliações.','',
        '## Arquivo das candidatas','',
        f"NLL de resposta da base híbrida ativa: {devbase['answer']['mean_answer_nll']:.6f}.",
        f"NLL dos textos de preservação: {devbase['anchors']['mean_nll']:.6f}.",
        '', '| Candidata | Família | Ridge | Força | NLL resposta | NLL preservação | Valores BF16 alterados | Validação conteúdo |',
        '|---|---|---:|---:|---:|---:|---:|---|']
    for c in archive['candidates']:
        val=c.get('validation');valtext=f"{val['content_correct']}/{val['total']}" if val else 'Não elegível'
        lines.append(f"| {c['id']} | {c['family']} | {c['ridge']} | {c['strength']} | "
            f"{c['development']['mean_answer_nll']:.6f} | {c['anchor']['mean_nll']:.6f} | "
            f"{c['weight_write']['changed_bf16_values']} | {valtext} |")
    lines+=['','O controle `stop_only` nunca pode ser promovido. Para promoção é necessário reduzir a NLL de resposta, '
        'preservar a NLL das âncoras e aumentar o conteúdo correto na validação sem reduzir o formato exato. '
        'Todos os motivos e hashes estão em `lab_rsi/archive.json`.','',
        '## As duas partes da arquitetura continuam presentes','',
        '- SenseNova: topologia de 32 camadas físicas, 56 execuções, mHC de duas vias e segunda visita ativa com ganho 0,05.',
        '- Liquid/LFM3: convolução de sete posições com coeficientes históricos aprendidos não nulos e atenção local de 256 tokens em três camadas.',
        '- Todas as novas candidatas passaram pela mesma verificação de arquitetura. Nenhuma desliga essas partes para melhorar a métrica.',
        '- O corpo continua com dimensões/pesos Qwen. Não são os pesos do SenseNova-Loop-9B nem o LFM3 completo. Roteadores mHC permanecem na inicialização; oito camadas inseridas têm saída neutra neste perfil.',
        '- O nome nominal 0,8B vem da base. O híbrido ampliado carrega aproximadamente 1,02B parâmetros, incluindo visão não avaliada aqui.','',
        '## Protocolo, limites e reprodução','',
        'Greedy sem thinking, até 12 tokens de resposta, cache, BF16/FP32, oito threads CPU. '
        'Até quatro prompts de comprimento idêntico por lote, sem padding, com a mesma organização nos modelos. '
        'O híbrido executa mais camadas que o original; o orçamento de computação é maior.','',
        '| Modelo | Parâmetros carregados | Tempo amortizado de geração, 64 perguntas | Respostas no limite de 12 tokens |',
        '|---|---:|---:|---:|']
    for key,s in summary.items():
        lines.append(f"| {names[key]} | {s['loaded_parameters']:,} | {s['amortized_generation_seconds']:.1f} s | {s['generation_limit_hits']} |")
    lines+=['','Benchmark customizado pequeno e principalmente na distribuição do currículo. Não avalia visão, '
        'contexto longo ou inteligência geral. Uma diferença pequena pode ser ruído, formato ou especialização. '
        'Não há afirmação de que o modelo passou a compreender sua arquitetura.','',
        'Princípios públicos dos laboratórios e referências: [LAB_METHODS.md](LAB_METHODS.md). '
        'Procedimento completo: [lab_rsi/PROTOCOL.md](lab_rsi/PROTOCOL.md).','',
        'Estado final: concluído, salvo e parado. Não existe processo permanente de treino depois desta execução.','',
        '## Respostas e correções completas','',
        '| ID | Esperado | Original | Híbrido antes do ajuste | Final |',
        '|---|---|---|---|---|']
    def esc(text):return text.replace('|','\\|').replace('\n',' / ')
    by={v:{r['id']:r for r in report['rows']} for v,report in reports.items()}
    for row in DATA['heldout']:
        key=row['id'];texts=[esc(by[v][key]['output']) for v in ['original','baseline',final]]
        lines.append(f"| {key} | {row['answer']} | {' | '.join(texts)} |")
    (ROOT/'LAB_REPORT.md').write_text('\n'.join(lines)+'\n')
    checkpoint={**frozen,'status':'complete','loaded_parameters':reports[final]['loaded_parameters'],
        'report':'LAB_REPORT.md','summary':'lab_rsi/summary.json',
        'replay':'python lab_rsi/replay.py --question YOUR_QUESTION',
        'base_revision':'2fc06364715b967f1860aea9cf38778875588b17',
        'sensenova_source_revision':'9937e91c7301b7dcbb5bf17e3e4e95c499a11e99',
        'source_manifest':'model_identity.json'}
    atomic_json(ROOT/'checkpoints/liquid_sense_loop.json',checkpoint)
    update_status(status='complete',phase='checkpointed',evaluating_variant=None,
                  final_test_evaluated=True,final_summary='lab_rsi/summary.json',
                  selected_candidate=frozen['candidate_id'],process_continues_in_background=False)
    print(json.dumps(overall,indent=2,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
