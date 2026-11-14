"""Read completed fixed comparisons; publish no intelligence or speed shortcuts."""
from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent;ROOT=H.parent

def read(p):return json.loads((H/p).read_text())
def save(p,x):(H/p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    selection=read('selection.json');variants=['original','parent','sft_final','policy_final']
    data={v:read('reports/validation_'+v+'.json') for v in variants}
    assert all(r['status']=='complete' for r in data.values())
    sft=read('reports/sft_training.json');policy=read('reports/policy_training.json')
    winner=selection['selected'];final=None;promote=False
    if winner:
        from decide import compare
        fr={v:read('reports/final_'+v+'.json') for v in ['original','parent',winner]}
        assert all(r['status']=='complete' for r in fr.values())
        final={'comparison':compare(fr['parent'],fr[winner]),'summaries':{v:r['summary'] for v,r in fr.items()}}
        promote=final['comparison']['eligible']
    else:assert not list((H/'reports').glob('final_*.json')),'Sealed final unexpectedly queried'
    loop={}
    for variant in ['parent',winner or 'policy_final']:
        ab=read('reports/diagnostic_'+variant+'_bypass.json');assert ab['status']=='complete'
        normal={(r['id'],r['thinking']):r for r in data[variant]['rows'] if r['kind']=='code'}
        records=[]
        for row in ab['rows']:
            full=normal[(row['id'],True)]
            records.append({'id':row['id'],'normal_cases':full['passed'],'replaced_cases':row['passed'],
                'normal_task':full['all_passed'],'replaced_task':row['all_passed'],
                'case_bits_changed':full['case_passed']!=row['case_passed'],
                'program_changed':full['code']!=row['code'],'normal_tokens':full['tokens'],'replaced_tokens':row['tokens']})
        loop[variant]=records
    tools={v:read('reports/tools_'+v+'.json')['successes'] for v in variants}
    audit={v:read('reports/'+v+'.json') for v in ['initial_factors','sft_epoch1','sft_final','policy_final']}
    stages={v:{k:a[k] for k in ['step','changed_native_tensors','changed_folded_projections','factor_values','native_values','effective_native_parameter_count','vision153_unchanged']} for v,a in audit.items()}
    actual_parent=sha(ROOT/'rsi100/checkpoints/best.pt');assert actual_parent==read('config.json')['parent_sha256']
    out={'status':'complete','parent_sha256':actual_parent,'parent_file_unchanged':True,
        'scope':'small controlled productive-thinking pilot on MAIN; not a general-intelligence benchmark',
        'training':{'sft_epochs':2,'sft_updates':sft['steps'],'target_token_presentations':sft['sft_target_tokens'],
            'factor_values':audit['sft_final']['factor_values'],'native_control_values':audit['sft_final']['native_values'],
            'both_actual_visits_recomputed':sft['both_actual_visits_recomputed'],
            'policy_groups':policy['groups'],'policy_samples':policy['samples'],'policy_updates':policy['updates'],
            'policy_zero_variance_skips':policy['skipped_zero_variance']},
        'validation':{v:r['summary'] for v,r in data.items()},'selection':selection,'final':final,
        'validated_research_candidate':winner if promote else None,
        'general_parent_stays_selected':True,'research_candidate_passed_both_gates':promote,'no_existing_checkpoint_overwritten':True,
        'loop_replacement_descriptive':loop,'tools_successes_out_of2':tools,'exports':stages,
        'apk_changed':False,'workers_active':False}
    save('summary.json',out)
    lines=['# Native028 — treino de pensamento produtivo no Liquid Sense principal','',
        'Piloto concluído; '+('candidato passou os dois gates independentes.' if promote else 'nenhum checkpoint promovido; o modelo geral anterior permanece selecionado.'),'',
        'Base preservada: `'+actual_parent+'`. Nenhum APK ou checkpoint anterior foi sobrescrito.','',
        '## O que realmente foi treinado','',
        f'Duas épocas, {sft["steps"]} atualizações SFT e {sft["sft_target_tokens"]} apresentações de tokens-alvo. '
        'São 48 problemas ensinados em duas formas (com e sem thinking), não um grande corpus. '
        f'Adaptados {audit["sft_final"]["factor_values"]:,} valores de baixo posto em 150 projeções e '
        f'{audit["sft_final"]["native_values"]:,} valores dos 276 controladores nativos. '
        'As mesmas projeções e controladores participam das duas visitas reais; o backward de ambas foi verificado. '
        'Loop/mHC, conv7 e janelas256 preservados. Não há um conjunto conhecido de pesos exclusivo de pensamento.','',
        f'A etapa de política gerou 32 amostras em oito grupos de tarefas de TREINO: {policy["updates"]} atualizações reais, '
        f'{policy["skipped_zero_variance"]} grupos sem variância descartados. '
        'Recompensas vêm de execução no sandbox; gabaritos não entram nos prompts de geração. '
        'Isto é um protótipo limitado de PPO relativo ao grupo, não reprodução de DAPO/OPD industrial.','',
        '## Comparação independente','',
        'Greedy; mesmos prompts, cache nativo BF16, quatro threads e EOS. Sem thinking:128tokens de código/48gerais. '
        'Com thinking:192tokens totais. Qwen original sem a expansão híbrida; demais com32camadas/56visitas. '
        'Somente a resposta final conta; pensamento sem fechamento falha.','',
        '| Variante | Código sem thinking | Casos | Gerais | Código com thinking | Casos | Gerais |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for v,r in data.items():
        a=r['summary']['False'];b=r['summary']['True']
        lines.append(f'| {v} | {a["code_tasks"]}/{a["code_total"]} | {a["cases"]}/{a["case_total"]} | {a["general_correct"]}/{a["general_total"]} | {b["code_tasks"]}/{b["code_total"]} | {b["cases"]}/{b["case_total"]} | {b["general_correct"]}/{b["general_total"]} |')
    lines+=['','Resultados por caso, textos integrais, conclusão, repetição e tokens em `reports/validation_*.json`. '
        'As mesmas quatro tarefas aparecem em dois modos: não são oito problemas independentes. '
        'A amostra é pequena, sem evidência estatística de superioridade geral ou contra4B. '
        'Ganho em casos parciais, NLL ou tokens não substitui o gate de tarefas completas e preservação.','',
        '## Decisão','',json.dumps(selection['checks'],ensure_ascii=False,indent=2),'',
        ('O teste final novo foi aberto apenas para o vencedor congelado; resultado em `summary.json`.' if winner else
        'Nenhum candidato passou a validação. Os quatro problemas e quatro controles finais, em ambos os modos, permanecem sem consultas ao modelo.'),'',
        '## Loop e ferramentas','',
        'Diagnóstico causal substitui a saída da segunda visita à camada27 pela primeira e mantém todas as56computações. '
        'Compara com saídas normais já salvas, sem repetir as linhas de validação. Mudança de texto ou ativação não basta para demonstrar ganho.','',
        '```json',json.dumps(loop,ensure_ascii=False,indent=2),'```','',
        'Python: '+', '.join(f'{v}={n}/2' for v,n in tools.items())+'. '
        'Mesmo sistema, schema e executor reais. Estes dois probes são descritivos, não BFCL nem evidência de navegação confiável.','',
        '## Preservação e limites','',
        'Arquivos de construção preservam fatores, controladores, cópias mestras FP32, AdamW/RNG e hashes dos699tensores nativos fundidos. '
        'Os candidatos avaliados são recarregados e fundidos em BF16 com verificação dos699hashes. '
        'A aritmética aditiva usada no treino pode diferir por arredondamento da inferência fundida. '
        'Nenhuma melhoria de velocidade foi medida neste estudo. Treino pequeno não equivale ao pós-treino massivo dos pares pesquisados. '
        'Fontes, dados, traces e resultados negativos permanecem; workers encerrados.']
    (H/'REPORT.md').write_text('\n'.join(lines)+'\n')
    status=read('status.json');status.update(status='complete',model_process_active=False,
        general_parent_sha256=actual_parent,validated_research_candidate=out['validated_research_candidate'],
        selected_checkpoint_promoted=promote,final_set_queried=winner is not None,
        sft_updates=sft['steps'],policy_updates=policy['updates'],optimizer_updates=sft['steps']+policy['updates']);save('status.json',status)
    print('REPORT028_COMPLETE',out['validated_research_candidate'],flush=True)
if __name__=='__main__':main()
