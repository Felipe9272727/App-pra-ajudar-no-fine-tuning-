async function(studyCommit) {
  function unpack(r) {
    if(r.isError)throw Error(JSON.stringify(r.structuredContent||r.content));
    let s=r.structuredContent;while(s?.structuredContent)s=s.structuredContent;
    return s?.content?JSON.parse(s.content):s;
  }
  const repo='Felipe9272727/App-pra-ajudar-no-fine-tuning-';
  const api='https://api.github.com/repos/'+repo+'/commits?sha=main&per_page=1';
  const before=unpack(await tools.mcp__codex_apps__github_fetch({url:api}))[0];
  const file=await tools.mcp__codex_apps__github_fetch_file({repository_full_name:repo,path:'README.md',ref:before.sha});
  if(file.isError)throw Error('Cannot read main README');
  let raw=file.structuredContent;while(raw?.structuredContent)raw=raw.structuredContent;
  const original=raw.content;
  if(typeof original!=='string')throw Error('Unexpected README payload');
  const r=await tools.exec_command({cmd:"python -c 'import json; print(json.dumps(json.load(open(\"review013/comparison.json\"))))'",workdir:'/workspace/liquid-sense',max_output_tokens:12000});
  const data=JSON.parse(r.output);if(data.selection.checkpoint_promoted)throw Error('Rewrite index for a genuinely promoted outcome');
  const link='https://github.com/'+repo+'/blob/'+studyCommit+'/';
  const scores=['original','parent','loop','joint'].map(k=>k+': '+data.models[k].tasks_passed+'/8 tarefas, '+data.models[k].cases_passed+'/160 casos').join('; ');
  const section='\n## Aprendizagem supervisionada do loop — 11/11/2026\n\n'+
    'Estudo 013 concluído. A nova autorização permitiu ensinar com soluções corretas: 120 programas verificados, adaptadores algébricos na segunda passagem e dados separados por família. '+
    'Comparação de geração livre: '+scores+'. Nenhum checkpoint promovido; preservar o anterior. '+
    'A auditoria identificou que o avaliador histórico rejeita o nome Python válido `_`; escores e gabaritos foram preservados, com a limitação documentada.\n\n'+
    '[Resultados e limites]('+link+'EXPERIMENTOS_CAPACIDADE.md) · '+
    '[Estado recuperado]('+link+'STATUS_RECUPERACAO.md) · '+
    '[DSpine e fontes CCORE]('+link+'PLANO_DSPINE.md).\n';
  if(original.includes('## Aprendizagem supervisionada do loop — 11/11/2026'))throw Error('Index already contains study013; inspect before retry');
  const index=original.indexOf('\n## ');
  const content=index<0?original+'\n'+section:original.slice(0,index)+section+original.slice(index);
  const tree=unpack(await tools.mcp__codex_apps__github_create_tree({repository_full_name:repo,base_tree_sha:before.commit.tree.sha,tree_elements:[{path:'README.md',content,mode:'100644',type:'blob'}]}));
  const commit=unpack(await tools.mcp__codex_apps__github_create_commit({repository_full_name:repo,parent_sha:before.sha,tree_sha:tree.sha,message:'Index supervised loop study013: retain parent, archive learning and judge-audit evidence'}));
  unpack(await tools.mcp__codex_apps__github_update_ref({repository_full_name:repo,branch_name:'main',sha:commit.sha,expected_sha:before.sha,force:false}));
  const after=unpack(await tools.mcp__codex_apps__github_fetch({url:api}))[0];
  if(after.sha!==commit.sha)throw Error('Main update not verified');
  return {commit:commit.sha,pinned_study:studyCommit};
}
