"""Descriptive completion notes; no new scoring or selection changes."""
import json,hashlib,datetime
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parent

def read(p):return json.loads((H/p).read_text())
def main():
 s=read('summary.json');assert s['status']=='complete' and s['validated_research_candidate'] is None
 assert not read('runtime.json')['model_process_active']
 train=read('reports/sft_training.json');assert train['steps']==192 and train['sft_target_tokens']==10796
 assert train['both_actual_visits_recomputed'] and len(train['ever_nonzero_gradient_names'])==576
 rows=[json.loads(x) for x in (H/'steps.jsonl').read_text().splitlines()];assert [r['step'] for r in rows]==list(range(1,193))
 for i in range(1,5):assert (H/f'checkpoints/epoch{i:02d}/manifest.json').exists()
 notes={v:{'new_tasks_nonthinking':c['False']['code_tasks'],'new_cases_nonthinking':c['False']['cases'],'new_general':c['False']['general_correct']} for v,c in s['fresh_validation'].items()}
 s.update(best_new_coding_score_epoch='epoch02',best_new_coding_score_is_not_a_validated_winner=True,
   four_epochs_completed_without_repeating_steps=True,all576_selected_tensors_received_nonzero_gradients=True,
   uncertainty_report='native029/reports/paired_uncertainty.json',completion_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
 (H/'summary.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
 p=H/'REPORT.md';text=p.read_text().replace('Os mesmos150fatores de baixo posto','Fatores de baixo posto em150projeções')
 assert '## Leitura dos resultados' not in text
 text+='''

## Leitura dos resultados

A segunda época teve a melhor pontuação de código NOVO sem thinking:1/4tarefas,
10/20casos, contra0/4e2/20do pai. Ela implementou corretamente a divisão de uma
lista em blocos de tamanho k, inclusive o bloco final menor. Porém perdeu três
casos antigos de código e dois controles gerais. É ganho pontual com regressões,
não uma candidata validada. A quarta época fez0/4e5/20; mais épocas não mantiveram
aquele ganho. Todas as saídas/versões permanecem arquivadas.

As épocas3e4atingiram7/8controles gerais NOVOS, antes4/8do pai. Nos controles
OBSERVADOS, todas as épocas ficaram5/8, igual ao pai, mas trocaram acertos por
erros. Por isso a soma não pode substituir preservação por item. As quatro
epocas terminaram8/8respostas comthinking, antes0/8, mas ficaram0/4programas
completos nesse modo. Conclusão curta e estilo não demonstram raciocínio profundo.

O Qwen original e o pai atingiram128tokens em todas as quatro respostas novas
semthinking, e não fecharam os oito pensamentos dentro de192tokens. Parte da
comparação mede verbosidade/conclusão sob orçamento curto. As versões treinadas
eram mais curtas; ainda assim apresentaram erros de retorno, de assinatura e
regressões. Não foi alterado budget, juiz, gabarito ou peso depois de observar
as respostas. A forma avaliada é a nativa fundida emBF16, com699hashes verificados.

São apenas quatro famílias, com perguntas repetidas em dois modos, e seleção
entre quatro épocas. A análise pareada é descritiva e não sustenta superioridade
geral ou contra4B. Nenhum teste final foi aberto, pois nenhuma época passou a
validação mais retenção. O melhor principal permanece46f6697; APK inalterado.
As192atualizações ocorreram uma vez, os576tensores selecionados tiveram gradientes
não nulos e ambas as visitas reais foram recomputadas. Nenhum worker ficou ativo.
'''
 p.write_text(text)
 (H/'reports/completion_checks.json').write_text(json.dumps({'all192steps_once':True,'new_epochs':4,'target_token_presentations':10796,'all4epoch_manifests_present':True,'both_loop_visits_backward_verified':True,'selected_nonzero_gradient_tensors':576,'no_models_active':True,'parent_file_unchanged':True,'sealed_final_unqueried':True,'selected_research_candidate':None},indent=2)+'\n')
 old=(ROOT/'AGENTS.md').read_text();marker='# Native028 complete';assert marker in old;old=old[old.index(marker):]
 header='''# Native029 complete — four epochs from selected MAIN best, no promotion

- User asked “Treine o melhor+4 épocas”. Completed4NEWepochs from the selected
  GENERAL46f6697, not rejected028SFT/PPO.192unique updates,10796label-token
  presentations,48paired teaching problems. Source/outputs on branch
  codex/liquid-sense-main-four-epochs-029-20261114. Read native029/REPORT.md,
  summary.json,selection.json,status.json,artifact_manifest.json and verification.
- Rank8on150projections+276native controls,7.31Mtrainable values; both actual
  visits,32physical/56executions,mHC2,conv7,local256preserved. All576eligible
  tensors had nonzero gradients. Initial and ALL4epoch archives contain
  optimizer/RNG and699merged hashes. No PPO, children or APK work in029.
- Factorlr5e-5/controllerlr1.25e-5,KL1.0were frozen before learning to reduce
  forgetting. This is not an epoch-count-only comparison with028.
- Fresh4code/20cases+8general(false) and4code+4general(thinking),budgets128/48/192.
  Parent:0/4code,2/20cases,4/8general withoutthinking. Epoch01:0/5/6,
  epoch02:1/10/6,epoch03:0/7/7,epoch04:0/5/7. Those triples mean tasks/cases/general.
  All epochs0/4complete coding withthinking, but finish8/8thinking answers.
  Original0/4code,2/20cases,5/8general; verbose originals hit the token caps.
- Epoch02solves chunks, but loses3known code cases+2general controls. No epoch
  eligible. Known028retention is OBSERVED,not a fresh benchmark; current parent
  replay matched old tokenIDs exactly. FINAL STILL UNQUERIED. Do not promote
  from NLL,new-case aggregate,shorter output or the last epoch alone.
- Keep general best.pt SHA25646f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8.
  All snapshots/negative outcomes preserved; native029/restore.py hydrates parts
  at explicit immutable refs. All workers CLOSED. No ongoing train/background
  promise. Do not repeat029; a next study needs fresh evaluation, not reused
  observed029validation presented as new. No4B,deep-thinking or speed claim.

'''
 (ROOT/'AGENTS.md').write_text(header+old)
 p=ROOT/'README.md';old=p.read_text();title,body=old.split('\n',1)
 section='''
## Pesquisa029 — quatro épocas do melhor geral, sem promoção

[Relatório](native029/REPORT.md), [comparações](native029/summary.json),
[decisão](native029/selection.json) e [protocolo](native029/PROTOCOL.md).

Quatro épocas NOVAS desde o checkpoint geral preservado:192atualizações e10796
apresentações de tokens-alvo. Loop,mHC e controles temporais treinados juntos,
com passos menores e KLmais forte. Todas as quatro versões foram preservadas.

| Versão | Código novo sem thinking | Casos | Gerais novos |
|---|---:|---:|---:|
| Pai selecionado | 0/4 | 2/20 | 4/8 |
| Época1 | 0/4 | 5/20 | 6/8 |
| Época2 | 1/4 | 10/20 | 6/8 |
| Época3 | 0/4 | 7/20 | 7/8 |
| Época4 | 0/4 | 5/20 | 7/8 |

A segunda época ganhou um problema novo completo, mas perdeu3casos antigos de
código e2controles gerais. **Nenhuma época passou os critérios de preservação.**
O checkpoint anterior e o APK continuam selecionados; teste final não consultado.
Com thinking, as versões treinadas encerraram8/8respostas, mas0/4programas certos.
Budget curto192tokens não mede o modo Extenso. Não há ganho geral de inteligência,
loop útil ou velocidade sem perda demonstrado. Workers encerrados.

'''
 p.write_text(title+'\n'+section+body)
 print('FINAL029_NOTES_AND_DOCS_READY')
if __name__=='__main__':main()
