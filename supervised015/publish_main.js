async function(studyCommit) {
  function unpack(r){if(r.isError)throw Error(JSON.stringify(r));let s=r.structuredContent;while(s?.structuredContent)s=s.structuredContent;return s?.content?JSON.parse(s.content):s;}
  const repo='Felipe9272727/App-pra-ajudar-no-fine-tuning-';
  const api='https://api.github.com/repos/'+repo+'/commits?sha=main&per_page=1';
  const before=unpack(await tools.mcp__codex_apps__github_fetch({url:api}))[0];
  const f=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:repo,path:'README.md',ref:before.sha});
  if(f.isError)throw Error('Cannot read index');let raw=f.structuredContent;while(raw?.structuredContent)raw=raw.structuredContent;const old=raw.content;
  if(typeof old!=='string')throw Error('Unexpected README');
  const r=await tools.exec_command({cmd:"python -c 'import json; print(json.dumps(json.load(open(\"supervised015/final_summary.json\"))))'",workdir:'/workspace/liquid-sense',max_output_tokens:20000});
  const data=JSON.parse(r.output);if(data.decision.checkpoint_promoted)throw Error('Principal promotion is outside specialist index');
  const scores=['original','parent','specialist'].map(k=>k+': HumanEval ensinado '+data.models[k].taught.solved+'/8, MBPP diagnóstico '+data.models[k].transfer.solved+'/8, controles '+data.models[k].controls.correct+'/12').join('; ');
  const link='https://github.com/'+repo+'/blob/'+studyCommit+'/';
  const heading='## Treino supervisionado de todos os pesos de texto — estudo015 (11/11/2026)';
  if(old.includes(heading))throw Error('Study already indexed; inspect before retry');
  const section='\n'+heading+'\n\n'+
    'Após autorização explícita para gradientes, foram treinados os546 tensores ativos de texto (919.659.696 parâmetros elegíveis), preservando visão e arquitetura híbrida. '+
    'A comparação binária confirmou mudança em '+data.training.changed_text_tensors+' tensores/'+data.training.changed_scalar_values+' valores. '+scores+'. '+
    'As oito soluções HumanEval foram ensinadas deliberadamente: isso mede especialização, não um resultado limpo do benchmark ou inteligência geral. MBPP ficou fora do treino, mas já era observado no014. '+
    'Estado: '+data.decision.status+'. O especialista foi preservado separadamente; o checkpoint principal anterior permanece selecionado. Sem alegação de superioridade contra4B.\n\n'+
    '[Relatório e regressões]('+link+'SUPERVISED_TEXT_REPORT.md) · [Resultados]('+link+'supervised015/final_summary.json) · [Pesos exatos]('+link+'supervised015/attempt_b/checkpoints/final/manifest.json) · [Reprodução]('+link+'supervised015/attempt_b/REPRODUCE.md).\n';
  const i=old.indexOf('\n## ');const content=i<0?old+'\n'+section:old.slice(0,i)+section+old.slice(i);
  const tree=unpack(await tools.mcp__codex_apps__github_create_tree({repository_full_name:repo,base_tree_sha:before.commit.tree.sha,tree_elements:[{path:'README.md',content,mode:'100644',type:'blob'}]}));
  const commit=unpack(await tools.mcp__codex_apps__github_create_commit({repository_full_name:repo,parent_sha:before.sha,tree_sha:tree.sha,message:'Index authorized full-text SFT015: specialist target fit, transfer diagnostics and preserved principal'}));
  unpack(await tools.mcp__codex_apps__github_update_ref({repository_full_name:repo,branch_name:'main',sha:commit.sha,expected_sha:before.sha,force:false}));
  const after=unpack(await tools.mcp__codex_apps__github_fetch({url:api}))[0];if(after.sha!==commit.sha)throw Error('Index ref not verified');
  return {main_commit:commit.sha,pinned_study:studyCommit};
}
