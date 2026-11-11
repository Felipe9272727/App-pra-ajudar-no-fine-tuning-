async function(studyCommit) {
  function unpack(r){if(r.isError)throw Error(JSON.stringify(r));let s=r.structuredContent;while(s?.structuredContent)s=s.structuredContent;return s?.content?JSON.parse(s.content):s;}
  const repo='Felipe9272727/App-pra-ajudar-no-fine-tuning-';
  const api='https://api.github.com/repos/'+repo+'/commits?sha=main&per_page=1';
  const before=unpack(await tools.mcp__codex_apps__github_fetch({url:api}))[0];
  const f=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:repo,path:'README.md',ref:before.sha});
  if(f.isError)throw Error('Cannot read index');let raw=f.structuredContent;while(raw?.structuredContent)raw=raw.structuredContent;const old=raw.content;
  if(typeof old!=='string')throw Error('Unexpected README');
  const r=await tools.exec_command({cmd:"python -c 'import json; print(json.dumps(json.load(open(\"supervised014/summary.json\"))))'",workdir:'/workspace/liquid-sense',max_output_tokens:12000});
  const data=JSON.parse(r.output);if(data.decision.checkpoint_promoted)throw Error('Review index for promoted candidate');
  const scores=['original','parent','edited'].map(k=>k+': HumanEval ensinado '+data.models[k].taught.solved+'/8, MBPP diferente '+data.models[k].transfer.solved+'/8').join('; ');
  const link='https://github.com/'+repo+'/blob/'+studyCommit+'/';
  const heading='## Respostas corretas nos pesos — estudo 014 (11/11/2026)';
  if(old.includes(heading))throw Error('Study already indexed; inspect before retry');
  const section='\n'+heading+'\n\n'+
    'Oito soluções corretas do HumanEval supervisionaram a edição direta de uma matriz existente da camada31; depois foram avaliados esses oito problemas e oito diferentes do MBPP, com os mesmos prompts/configurações para cada modelo. '+
    scores+'. O resultado no conjunto ensinado mede ajuste aos exemplos, não generalização. São subconjuntos de um piloto, sem pontuações completas dos benchmarks. '+
    'Nenhum checkpoint foi promovido; o anterior permanece selecionado.\n\n'+
    '[Relatório e limites]('+link+'DIRECT_BENCHMARK_REPORT.md) · [Pesos e estado]('+link+'supervised014/teaching.json) · [Reprodução]('+link+'supervised014/REPRODUCE.md).\n';
  const i=old.indexOf('\n## ');const content=i<0?old+'\n'+section:old.slice(0,i)+section+old.slice(i);
  const tree=unpack(await tools.mcp__codex_apps__github_create_tree({repository_full_name:repo,base_tree_sha:before.commit.tree.sha,tree_elements:[{path:'README.md',content,mode:'100644',type:'blob'}]}));
  const commit=unpack(await tools.mcp__codex_apps__github_create_commit({repository_full_name:repo,parent_sha:before.sha,tree_sha:tree.sha,message:'Index study014: supervised direct weight edit and separated taught/transfer benchmark evidence'}));
  unpack(await tools.mcp__codex_apps__github_update_ref({repository_full_name:repo,branch_name:'main',sha:commit.sha,expected_sha:before.sha,force:false}));
  const after=unpack(await tools.mcp__codex_apps__github_fetch({url:api}))[0];if(after.sha!==commit.sha)throw Error('Index ref not verified');
  return {main_commit:commit.sha,pinned_study:studyCommit};
}
