"""Summarize all trials and held-out results without changing model selection."""
from pathlib import Path
import json
import statistics
from rsi_cycle import atomic_json
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'v2_adaptation'))
from experiment import grade

ROOT=Path(__file__).resolve().parent


def cell(value):return str(value).replace('|','\\|').replace('\n',' ⏎ ').replace('`',"'")


def main():
    state=json.loads((ROOT/'rsi/status.json').read_text())
    rounds=[json.loads(p.read_text()) for p in sorted((ROOT/'rsi').glob('round_*.json'))]
    data=json.loads((ROOT/'v2_adaptation/data_v2.json').read_text())
    results={name:json.loads((ROOT/'evaluation'/f'{name}.json').read_text())
             for name in ['original','incumbent','liquid']}
    assert all(r['status']=='complete' for r in results.values())
    assert len({r['data_sha256'] for r in results.values()})==1
    # Apply the same case-aware scorer uniformly to saved raw generations.
    # No inference or weight selection is repeated.
    for name,result in results.items():
        corrections=0
        for row in result['rows']:
            corrected=grade(row['output'],row)
            if corrected!=row['correct']:
                row['pre_case_check_correct']=row['correct'];corrections+=1
            row['correct']=corrected
        result['correct']=sum(r['correct'] for r in result['rows'])
        result['grading_version']='v2_case_aware_numeric_only_semantic_json'
        result['grading_corrections']=corrections
        atomic_json(ROOT/'evaluation'/f'{name}.json',result)
    audit=[]
    for row in rounds:
        raw=row['student_raw_suggestion']
        try:
            parsed=json.loads(raw)
            valid=set(parsed)=={'gain','beta','liquid_mix'}
        except ValueError:parsed=None;valid=False
        audit.append({'round':row['round'],'valid_json_recipe':valid,
            'changed_recipe_vs_incumbent':valid and parsed!=row['incumbent'],
            'selected_by':row['proposal_selected_by'],'raw':raw})
    atomic_json(ROOT/'rsi/suggestion_audit.json',audit)
    lines=['# Piloto de RSI assistido — Qwen, SenseNova e motivos LFM3','',
        'Data: 03/11/2026. Execução real em CPU, com edições diretas dos pesos, calibração algébrica e controle pelo assistente.',
        '', '## Estado salvo','',
        f'- Rodadas de desenvolvimento concluídas: **{len(rounds)}**.',
        f'- Candidatas promovidas nestas rodadas: **{sum(r["accepted"] for r in rounds)}**.',
        '- O código, o patch de convoluções, a receita incremental, sugestões reais e as decisões estão versionados nesta branch.',
        '- O piloto está concluído e pausado no checkpoint. Não há processo permanente de treinamento ou API paga em execução.',
        '', '## Comparação final em 24 perguntas novas','',
        '| Modelo | Acertos | Média de tempo por pergunta | Pico RSS |',
        '|---|---:|---:|---:|']
    labels={'original':'Qwen original','incumbent':'Checkpoint preservado, loop adaptado',
            'liquid':'Loop + convoluções calibradas e janela LFM3 (experimental)'}
    for name,r in results.items():
        lines.append(f'| {labels[name]} | {r["correct"]}/{r["total"]} | {statistics.mean(x["seconds"] for x in r["rows"]):.3f} s | {r["peak_rss_mib"]:.1f} MiB |')
    lines+=['','O teste foi congelado antes de calibrar e não escolheu a receita. Usamos geração greedy, thinking desativado, no máximo 12 tokens novos por resposta, CPU com oito threads e backbone BF16. Roteadores e controles permanecem FP32. Respostas numéricas aceitam somente um número; JSON é comparado semanticamente; texto é normalizado respeitando exigências explícitas de caixa. São questões autorais básicas, não benchmarks padronizados de inteligência.',
        '', 'O tempo é de uma única execução por variante e depende do comprimento das respostas, aquecimento e carga do host. Não usamos esses tempos para atribuir um ganho de velocidade à atenção local da Liquid; os prompts deste teste são curtos.',
        '', 'As 24 perguntas diferem do antigo teste de 48 itens. Não compare diretamente os escores antigos com estes. Não houve reajuste dos pesos depois que os resultados reservados foram observados.',
        '', 'A comparação de caixa é estrita quando o pedido exige maiúsculas/minúsculas ou um símbolo químico. Nos demais itens textuais, ignoramos caixa e ponto final. A regra foi conferida uniformemente sobre as respostas brutas salvas.',
        '', '## Seis ciclos registrados','',
        '| Rodada | gain | beta | liquid_mix | NLL da candidata | NLL do checkpoint medido | Decisão |',
        '|---|---:|---:|---:|---:|---:|---|']
    for r in rounds:
        c=r['candidate']
        lines.append(f'| {r["round"]} | {c["gain"]} | {c["beta"]} | {c["liquid_mix"]} | {r["candidate_development"]["mean_answer_nll"]:.6f} | {r["incumbent_development_nll"]:.6f} | {"Promovida" if r["accepted"] else "Rejeitada"} |')
    lines+=['','Menor NLL de desenvolvimento é melhor. A regra de promoção foi redução maior que 0,0001, definida no código. As rodadas 5 e 6 incluíram controle sem mudança de pesos após pedir sugestão ao modelo. As diferenças desses controles foram '+', '.join(str(r.get('no_op_control_nll_delta')) for r in rounds if 'no_op_control_nll_delta' in r)+'. Não somamos resultados de calibração ou escores de testes diferentes para anunciar uma melhora.',
        '', '## O que o assistente e a IA pequena fizeram','',
        'O assistente foi o controlador: escolheu as candidatas, executou as cirurgias numéricas, leu as métricas e decidiu promoção ou rejeição. A IA pequena foi consultada em cada rodada, e suas respostas brutas estão nos logs. Elas repetiram os parâmetros correntes; algumas ficaram truncadas e não formaram JSON completo. Não atribuímos ao modelo sugestões novas que ele não produziu. Os testes deste piloto não demonstram autoaperfeiçoamento recursivo autônomo ou geral.',
        '', '## Arquitetura e adaptação efetivas','',
        'O código preserva o mecanismo de decoder da SenseNova: 32 camadas físicas, 56 execuções e mHC com duas vias, em dimensões do Qwen. Adicionamos controles de contribuição por visita. Primeiro reconstruímos uma inicialização conservadora: nas duas sondas testadas, os logits eram bit a bit iguais aos do original antes de ativar a segunda passagem.',
        '', 'A calibração das convoluções foi uma regressão ridge fechada sobre oito textos (269 tokens), sem backward ou otimizador. Ela reescreveu 440.792 coeficientes BF16, incluindo 221.184 coeficientes novos de histórico. Isso é aprendizagem algébrica por dados, e não um processo inteiramente livre de treinamento. O patch ajustado foi preservado como candidata; ele não está automaticamente ativo no checkpoint principal.',
        '', 'As ideias LFM3 implementadas são convolução com sete posições e atenção local de 256 tokens em três camadas de atenção. O mecanismo sequencial principal continua sendo Gated DeltaNet; não portamos o operador completo nem os pesos treinados do LFM3. Testamos a causalidade em 300 posições e a equivalência da máscara de um passo com cache. O benchmark curto não mede qualidade de contexto longo ou ganhos de velocidade desses operadores.',
        '', 'Receita do checkpoint principal: `'+json.dumps(state['incumbent'],ensure_ascii=False)+'`.',
        '', 'Com beta zero, as oito camadas físicas inseridas continuam neutras; as tentativas de ativá-las foram rejeitadas. Com liquid_mix zero, o delta de convolução aprendido e a janela local ficam desativados no checkpoint principal. A variante experimental Liquid é avaliada separadamente. Ter os módulos no código não equivale a ter aprendido a usá-los bem.',
        '', 'As medições de desenvolvimento antes e depois de expandir o kernel podem apresentar diferenças numéricas BF16. Cada ciclo reavaliou o checkpoint e a candidata na mesma implementação; não atribuímos essas diferenças de implementação a uma rodada de RSI.',
        '', '## Todas as respostas lado a lado','',
        '| ID | Gabarito | Original | Checkpoint preservado | Liquid experimental |',
        '|---|---|---|---|---|']
    for i,item in enumerate(data['heldout']):
        cols=[]
        for name in ['original','incumbent','liquid']:
            row=results[name]['rows'][i]
            assert row['id']==item['id']
            cols.append('`'+cell(row['output'])+'` ('+('acerto' if row['correct'] else 'erro')+')')
        lines.append('| '+item['id']+' | `'+cell(item['answer'])+'` | '+' | '.join(cols)+' |')
    lines+=['','## Retomar','',
        'Leia AGENTS.md, rsi/status.json, rsi/pending.json e checkpoints/incumbent.json. Não repetir rodadas já finalizadas. Como o conjunto reservado já foi avaliado, uma nova pesquisa precisa de outro conjunto de teste ainda não observado para verificar o próximo resultado.',
        '', 'O checkpoint é incremental: modelo público na revisão fixa + scripts versionados + receita JSON + patch de tensores. Isso reconstrói os mesmos pesos sem subir gigabytes de base. O usuário não pediu entrega dos pesos completos agora.',
        '', 'Fontes e licenças: README.md, LICENSE e NOTICE. Os limites e os resultados negativos fazem parte do registro do experimento.']
    (ROOT/'PILOT_REPORT.md').write_text('\n'.join(lines)+'\n')
    state.update(status='pilot_complete',heldout_evaluated=True,
                 heldout_used_for_selection=False,
                 next_round=state['rounds_completed']+1,
                 next_evaluation_requires_fresh_test=True,
                 final_scores={k:{'correct':v['correct'],'total':v['total']} for k,v in results.items()})
    atomic_json(ROOT/'rsi/status.json',state)
    print(json.dumps(state['final_scores'],indent=2))


if __name__=='__main__':main()
