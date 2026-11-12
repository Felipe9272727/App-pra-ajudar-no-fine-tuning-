async function(paths, message) {
  function unpack(r) {
    if(r.isError) throw Error(JSON.stringify(r.structuredContent||r.content));
    let s=r.structuredContent;while(s?.structuredContent)s=s.structuredContent;
    return s?.content?JSON.parse(s.content):s;
  }
  const repo='Felipe9272727/App-pra-ajudar-no-fine-tuning-',branch='codex/liquid-sense-supervised-all-text-20261112';
  const entries=[];
  for(const path of paths) {
    if(!/^supervised015/[a-zA-Z0-9_./-]+\.(pt|json|bin|jsonl|log)$/.test(path))throw Error('Unexpected tensor path');
    const metaResult=await tools.exec_command({cmd:"python -c 'import pathlib,json,subprocess; p=pathlib.Path(\""+path+"\"); print(json.dumps({\"size\":p.stat().st_size,\"git_blob\":subprocess.check_output([\"git\",\"hash-object\",str(p)],text=True).strip()}))'",workdir:'/workspace/liquid-sense',max_output_tokens:2000});
    const meta=JSON.parse(metaResult.output);const parts=[];
    const offsets=[];for(let off=0;off<meta.size;off+=737280)offsets.push(off);
    for(let start=0;start<offsets.length;start+=8) {
      const batch=offsets.slice(start,start+8);
      const results=await Promise.allSettled(batch.map(async offset=>{
        const n=Math.min(737280,meta.size-offset);
        const r=await tools.exec_command({cmd:`python -c 'import pathlib,base64; f=pathlib.Path("${path}").open("rb"); f.seek(${offset}); print(base64.b64encode(f.read(${n})).decode())'`,workdir:'/workspace/liquid-sense',max_output_tokens:250000});
        const data=r.output.trim();if(r.exit_code!==0||data.length!==4*Math.ceil(n/3))throw Error('Truncated binary');return data;
      }));
      for(const r of results){if(r.status!=='fulfilled')throw r.reason;parts.push(r.value);}
    }
    const blob=unpack(await tools.mcp__codex_apps__github_create_blob({repository_full_name:repo,encoding:'base64',content:parts.join('')}));
    if(blob.sha!==meta.git_blob)throw Error('Weight blob identity mismatch');
    entries.push({path,mode:'100644',type:'blob',sha:blob.sha});
  }
  const headUrl='https://api.github.com/repos/'+repo+'/commits?sha='+encodeURIComponent(branch)+'&per_page=1';
  const before=unpack(await tools.mcp__codex_apps__github_fetch({url:headUrl}))[0];
  const tree=unpack(await tools.mcp__codex_apps__github_create_tree({repository_full_name:repo,base_tree_sha:before.commit.tree.sha,tree_elements:entries}));
  const commit=unpack(await tools.mcp__codex_apps__github_create_commit({repository_full_name:repo,parent_sha:before.sha,tree_sha:tree.sha,message}));
  unpack(await tools.mcp__codex_apps__github_update_ref({repository_full_name:repo,branch_name:branch,sha:commit.sha,expected_sha:before.sha,force:false}));
  if(unpack(await tools.mcp__codex_apps__github_fetch({url:headUrl}))[0].sha!==commit.sha)throw Error('Tensor outcome commit not verified');
  return {commit:commit.sha,tensors:paths.length};
}
