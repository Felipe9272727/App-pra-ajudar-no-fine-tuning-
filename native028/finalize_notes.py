"""Attach completed read-only diagnostics; cannot alter selection or any score."""
import json,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent

def read(p):return json.loads((H/p).read_text())
def write(p,v):(H/p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def main():
    assert read('status.json')['status']=='complete'
    assert not read('runtime.json')['model_process_active'] and not read('arithmetic_runtime.json')['model_process_active']
    journal=[json.loads(x) for x in (H/'steps.jsonl').read_text().splitlines()]
    assert [x['step'] for x in journal]==list(range(1,97))
    assert journal[-1]['sft_target_tokens']==5398
    groups=read('reports/policy_groups.json');assert len(groups)==8 and sum(x['updated'] for x in groups)==8
    arithmetic={v:read(f'reports/arithmetic_{v}.json') for v in ['sft_final','policy_final']}
    assert all(r['status']=='complete' for r in arithmetic.values())
    audit={v:{'rows':len(r['rows']),'same_ids':sum(x['same_token_ids_as_folded'] for x in r['rows']),
        'same_case_bits':sum(x['same_case_bits_as_folded'] for x in r['rows'])} for v,r in arithmetic.items()}
    tools={}
    for variant in ['original','parent','sft_final','policy_final']:
        r=read(f'reports/tools_{variant}.json');calls=[o for x in r['rows'] for o in x['observations'] if o['origin']=='model_call']
        tools[variant]={'valid_actual_model_calls':len(calls),'successful_executions_with_empty_stdout':sum(o['observation'].get('ok') and not o['observation'].get('stdout','') for o in calls),
            'complete_tool_flows_passed':r['successes'],'parse_errors':sum(x['parse_error'] is not None for x in r['rows'])}
    summary=read('summary.json');summary.update(arithmetic_audit=audit,tool_flow_analysis=tools,
        official_original_file_integrity=read('reports/official_base_integrity.json'),
        exact_sft_journal_steps1_through96=True,posthoc_audit_new_weight_updates=0,
        parameter_geometry_report='native028/reports/parameter_geometry.json',
        error_mode_report='native028/reports/error_modes.json',
        paired_uncertainty_report='native028/reports/paired_uncertainty.json')
    assert summary['validated_research_candidate'] is None and not read('selection.json')['final_gate_open']
    write('summary.json',summary);write('reports/tool_flow_analysis.json',tools)
    addition='''

## O que as falhas mostram

O SFT encerrou as8/8respostas com thinking, mas continuou com0/4programas
integralmente corretos. Os erros restantes são valores de retorno incorretos e
TypeError por assinaturas/entradas mal interpretadas, não respostas cortadas.
Sem thinking, os casos caíram7→2apósSFT e ficaram6apósPPO. A contagem geral5/8
esconde trocas: ambas as versões treinadas perderam os controles de plural de
cão e imutabilidade da tupla, embora ganhassem outros. O gate preserva cada
acerto anterior, por isso nenhuma versão passou. Mais tokens não corrigem
automaticamente essas respostas já encerradas por EOS.

São32amostras sobre OITO perguntas de treino;29passaram os casos. Isso difere
das quatro famílias de validação em dificuldade, amostragem e forma numérica.
O contraste não é uma estimativa isolada de overfitting, mas não demonstrou a
transferência de competência pretendida. A queda no SFT precede a etapaPPO;
não se pode atribuir todo o problema à recompensa por encurtamento.

Auditoria exploratória: as duas primeiras tarefas sem thinking foram executadas
uma vez por checkpoint com os fatores ainda aditivos, exatamente restaurados.
As4/4saídas produziram os mesmos IDs de tokens e casos das respostas fundidas já
salvas. Logo, nesses probes, a fusão BF16 não explica os erros. Isso não prova
equivalência numérica em todos os prompts. Nenhum resultado dessa auditoria
entrou na seleção, e o teste final continuou fechado.

Os quatro modelos conseguiram emitir chamadas Python válidas, mas nenhum
completou os dois fluxos. Em especial, expressões como53*27semprint executaram
sem stdout no brokerCPython; depois, as respostas adivinharam números errados.
As versões treinadas também usaram(5+7)/2para a média de[5,7,9]. O Qwen original
respondeu o valor7na segunda pergunta em uma frase, sem chamada prescrita;
isso não passa o contrato de uso real de ferramenta e resposta somente numérica.
Portanto0/2não significa ausência de capacidade de emitir tool calls. Não foi
alterado o broker, o gabarito ou o protocolo para melhorar os totais.

A auditoria dos pesos mostra as16saídas antes neutras alteradas,241controladores
com mudança apósSFT e240apósPPO. A segunda visita manteve ganhos próximos de5%
por camada; quantidade de pesos diferentes e roteadores não zerados não provam
verificação útil. Nos dois probes de substituição da segunda saída pela primeira,
os casos corretos ficaram iguais. Não houve evidência de vantagem funcional do
loop nesses probes, nem de maior profundidade de raciocínio.

## Hipótese seguinte, ainda NÃO executada

Antes de ampliar épocas ou o número de pesos, preparar um currículo de tarefas
mais variadas e reparos verificados: conferir assinatura/entradas, executar casos
limite e reagir a observação vazia sem inventar resultado. Preservar exemplos de
código corretos do pai, além de âncoras de linguagem. Uma adaptação específica da
segunda visita, com proteção explícita da primeira e objetivos intermediários de
verificação, pode testar melhor o uso do loop do que SFT compartilhado sozinho.
As tarefas028já observadas não poderão ser apresentadas novamente como validação
inédita. Não há nova rodada, treino ou serviço rodando após este estudo.
'''
    p=H/'REPORT.md';text=p.read_text();assert '## O que as falhas mostram' not in text
    p.write_text(text+addition)
    write('reports/completion_integrity.json',{'all96_sft_step_ids_once':True,'all8_policy_updates_real':True,'arithmetic_audit':audit,
        'all_primary_and_audit_model_workers_closed':True,'selected_checkpoint_changed':False,'sealed_final_queried':False})
    print('FINAL_NOTES028_COMPLETE_NO_SCORE_CHANGES')
if __name__=='__main__':main()
