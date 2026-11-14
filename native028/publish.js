async function(paths, message, deletions = []) {
  function unpack(r) {
    if (r.isError) throw Error(JSON.stringify(r.structuredContent || r.content));
    let s = r.structuredContent;
    while (s?.structuredContent) s = s.structuredContent;
    return s?.content ? JSON.parse(s.content) : s;
  }
  const page = Number((await tools.exec_command({cmd:'python native028/publish_nonce.py',workdir:'/workspace/liquid-sense',max_output_tokens:100})).output.trim());
  const repo = 'Felipe9272727/App-pra-ajudar-no-fine-tuning-';
  const branch = 'codex/liquid-sense-productive-thinking-028-20261114';
  if (![...paths, ...deletions].every(p => /^[a-zA-Z0-9_./-]+$/.test(p) && !p.endsWith('.pt'))) throw Error('Unexpected text path');
  const program = 'import json,pathlib; names=' + JSON.stringify(paths) + '; print(json.dumps({n:pathlib.Path(n).read_text() for n in names}))';
  const quoted = "'" + program.replace(/'/g, "'\\''") + "'";
  const read = await tools.exec_command({cmd:'python -c ' + quoted,workdir:'/workspace/liquid-sense',max_output_tokens:60000});
  if (read.exit_code !== 0) throw Error(read.output);
  const files = JSON.parse(read.output);
  const before = unpack(await tools.mcp__codex_apps__github_fetch({url:'https://api.github.com/repos/' + repo + '/commits?sha=' + encodeURIComponent(branch) + '&per_page=' + page + '&page=1'}))[0];
  const entries = Object.entries(files).map(([path,content]) => ({path,content,mode:'100644',type:'blob'}));
  for (const path of deletions) entries.push({path,mode:'100644',type:'blob',sha:null});
  const tree = unpack(await tools.mcp__codex_apps__github_create_tree({repository_full_name:repo,base_tree_sha:before.commit.tree.sha,tree_elements:entries}));
  const commit = unpack(await tools.mcp__codex_apps__github_create_commit({repository_full_name:repo,parent_sha:before.sha,tree_sha:tree.sha,message}));
  unpack(await tools.mcp__codex_apps__github_update_ref({repository_full_name:repo,branch_name:branch,sha:commit.sha,expected_sha:before.sha,force:false}));
  const after = unpack(await tools.mcp__codex_apps__github_fetch({url:'https://api.github.com/repos/' + repo + '/commits?sha=' + encodeURIComponent(branch) + '&per_page=' + (page+1) + '&page=1'}))[0];
  if (after.sha !== commit.sha) throw Error('Outcome commit not verified');
  return {commit:commit.sha,files:paths.length};
}
