"""Report real engineering checks separately from tests using scripted replies."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'android_thinking024'
def read(p):return json.loads((HERE/p).read_text())
def main():
 rows=[]
 for name,p in [('old_tools023_nonthinking256','baseline_math'),('new_thinking32_response64','forced_math'),('new_profundo1024_response2048','profundo_math')]:
  m=read('logs/'+p+'.json');correct=m['text'].strip()=='323';rows.append({'variant':name,'answer_correct':correct,'expected_for_grader_only':'323','reference_answer_not_in_model_input':True,'response_preview':m['text'][:220],'finish_reason':m['finish_reason'],'tokens':m['tokens'],'reasoning_tokens':m.get('reasoning_tokens',0),'response_tokens':m.get('response_tokens',m['tokens']),'forced_control_tokens':m.get('forced_control_tokens',0),'forced_reasoning_close':m.get('forced_reasoning_close',False),'prompt_tokens':m['prompt_tokens'],'wall_model_seconds_descriptive_only':m['prefill_seconds']+m['decode_seconds'],'raw_path':'logs/'+p+'.json','sha256':hashlib.sha256((HERE/('logs/'+p+'.json')).read_bytes()).hexdigest()})
 full=read('logs/profundo_math.json');tokens=full['prompt_tokens']+len(full['generated_ids']);assert tokens>2048
 report={'status':'long_thinking_failed_no_quality_promotion','scope':'one arithmetic engineering probe, same exact general weights, greedy4CPUthreads; not a benchmark or evidence of general intelligence','rows':rows,'selected_default':'normal','long_modes':'explicitly optional and experimental','context_guard_test':{'strategy':'full thinking run naturally exceeded old2048guard; no redundant long-input model run','prompt_plus_generated_ids':tokens,'model_processed_position_lower_bound':tokens-1,'new_guard':16384,'full16384stress_test_performed':False,'prepared_context_fixture_not_queried':True},'HF_prompt_counts_match_actual_native':read('reports/hf_template_checks.json')['expected_arithmetic_prompt_tokens']=={'False':rows[0]['prompt_tokens'],'True':rows[2]['prompt_tokens']},'source_pack_sha256':'6c774a434438add704b1993b8e013493fb95bc9802c4d9b30227832115c07288','new_training_updates':0,'device_test_performed':False,'old023sealed4questions_not_queried':True}
 py=HERE/'logs/actual_python_normal/result.json'
 if py.exists():
  m=json.loads(py.read_text());trace=read('logs/actual_python_normal/trace.json');obs=[t['observation'] for t in trace if 'observation' in t];report['actual_native_python_agent']={'has_final':bool(m.get('text')),'final':m.get('text'),'calls':m.get('actual_tool_calls'),'success':bool(m.get('text')) and '414' in m['text'] and any(o.get('ok') and '414' in o.get('stdout','') for o in obs),'real_execution_observations':obs,'reference_answer_not_in_model_input':True,'question':'Use Python para conferir quanto é 18 vezes 23 e diga o resultado.','profile':'normal','scope':m['scope'],'not_phone_performance_comparison':True}
 corrected=HERE/'logs/actual_python_after_fixes/result.json'
 if corrected.exists():
  m=json.loads(corrected.read_text());trace=read('logs/actual_python_after_fixes/trace.json');obs=[t['observation'] for t in trace if 'observation' in t]
  report['actual_native_python_after_fixes']={'has_final':bool(m.get('text')),'final':m.get('text'),'calls':m.get('actual_tool_calls'),'success':bool(m.get('text')) and '414' in m['text'] and any(o.get('ok') and '414' in o.get('stdout','') for o in obs),'observations':obs,'reference_answer_not_in_model_input':True,'question':'Use Python para conferir quanto é 18 vezes 23 e diga o resultado.','profile':'normal','scope':m['scope'],'same_question_and_weights_as_initial_tool_smoke':True,'software_changes_only':['general im_end stop restored','empty-stdout runtime feedback','protocol-only final rejected'],'no_claim_of_weight_improvement':True}
 abi=HERE/'logs/explicit_python_abi/result.json'
 if abi.exists():
  m=json.loads(abi.read_text());trace=read('logs/explicit_python_abi/trace.json');obs=[t['observation'] for t in trace if 'observation' in t]
  report['explicit_code_tool_IO_smoke']={'success':bool(m.get('text')) and '414' in m['text'] and any(o.get('ok') and o.get('stdout','').strip()=='414' for o in obs),'final':m.get('text'),'observations':obs,'question':'Execute este código em Python e diga a saída observada: print(18 * 23)','test_supplies_code_not_numeric_output':True,'not_problem_solving_or_weight_quality_score':True,'scope':m['scope']}
 report['final_stop_correction_does_not_change_recorded_long_probe']=not any(t in full['generated_ids'] for t in [248044,248046])
 (HERE/'reports/comparison.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':report['status'],'rows':[(r['variant'],r['answer_correct']) for r in rows],'actual_python':report.get('actual_native_python_agent'),'context_guard_crossed':tokens>2048},ensure_ascii=False))
if __name__=='__main__':main()
