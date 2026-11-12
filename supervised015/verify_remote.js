async function() {
  function unpack(r){if(r.isError)throw Error(JSON.stringify(r));let s=r.structuredContent;while(s?.structuredContent)s=s.structuredContent;return s?.content?JSON.parse(s.content):s;}
  const repo='Felipe9272727/App-pra-ajudar-no-fine-tuning-',branch='codex/liquid-sense-supervised-all-text-20261112';
  const api='https://api.github.com/repos/'+repo;
  const headUrl=api+'/commits?sha='+encodeURIComponent(branch)+'&per_page=1';
  const head=unpack(await tools.mcp__codex_apps__github_fetch({url:headUrl}))[0];
  const root=unpack(await tools.mcp__codex_apps__github_fetch({url:api+'/git/trees/'+head.commit.tree.sha}));
  const folder=root.tree.find(e=>e.path==='supervised015');if(!folder)throw Error('Missing study tree');
  const subtree=unpack(await tools.mcp__codex_apps__github_fetch({url:api+'/git/trees/'+folder.sha+'?recursive=1'}));
  if(subtree.truncated)throw Error('Incomplete remote tree');
  const remote=new Map(root.tree.filter(e=>e.type==='blob').map(e=>[e.path,e.sha]));
  for(const e of subtree.tree)if(e.type==='blob')remote.set('supervised015/'+e.path,e.sha);
  const r=await tools.exec_command({cmd:"python -c 'import pathlib,json,hashlib,subprocess; p=pathlib.Path(\"supervised015/artifact_manifest.json\"); print(json.dumps({\"manifest\":json.loads(p.read_text()),\"git_blob\":subprocess.check_output([\"git\",\"hash-object\",str(p)],text=True).strip(),\"sha256\":hashlib.sha256(p.read_bytes()).hexdigest()}))'",workdir:'/workspace/liquid-sense',max_output_tokens:100000});
  const inventory=JSON.parse(r.output),manifest=inventory.manifest;
  if(remote.get('supervised015/artifact_manifest.json')!==inventory.git_blob)throw Error('Remote inventory itself differs');
  const mismatches=manifest.files.filter(f=>remote.get(f.path)!==f.git_blob);if(mismatches.length)throw Error('Artifact blob mismatches: '+JSON.stringify(mismatches));
  const old=unpack(await tools.mcp__codex_apps__github_fetch({url:api+'/git/commits/713c8c69827f83a0cacbe56994ed8f23c2330939'}));
  const oldTree=unpack(await tools.mcp__codex_apps__github_fetch({url:api+'/git/trees/'+old.tree.sha}));
  const roots=new Map(root.tree.map(e=>[e.path,e.sha]));
  const changedOld=oldTree.tree.filter(e=>e.path!=='AGENTS.md' && roots.get(e.path)!==e.sha);
  if(changedOld.length)throw Error('Prior artifact subtree unexpectedly changed: '+JSON.stringify(changedOld));
  if(unpack(await tools.mcp__codex_apps__github_fetch({url:headUrl}))[0].sha!==head.sha)throw Error('Branch moved during verification');
  return {status:'all_artifacts_verified_against_remote_git_blobs',branch,verified_commit:head.sha,root_tree:root.sha,study_tree:folder.sha,file_count:manifest.files.length,total_bytes:manifest.total_bytes,artifact_manifest_sha256:inventory.sha256,artifact_manifest_git_blob:inventory.git_blob,all_blob_hashes_match:true,prior_root_entries_unchanged_except_authorized_AGENTS:true,prior_commit:old.sha,principal_rsi100_subtree_unchanged:true,weight_restore_verified_locally_before_upload:true,remote_inference_was_not_run:true};
}
