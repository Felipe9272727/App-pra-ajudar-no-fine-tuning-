async function() {
  const root='/workspace/liquid-sense', repo='Felipe9272727/App-pra-ajudar-no-fine-tuning-',branch='codex/liquid-sense-app-epochs-030-20261114';
  function unpack(r){if(r.isError)throw Error(JSON.stringify(r.structuredContent||r.content));let s=r.structuredContent;while(s?.structuredContent)s=s.structuredContent;return s?.content?JSON.parse(s.content):s;}
  const read=await tools.exec_command({cmd:"python -c 'import json,pathlib; h=pathlib.Path(\"android_epochs030\"); p=h/\"reports/patch_upload_receipts.json\"; print(json.dumps({\"manifest\":json.loads((h/\"patch_archive/manifest.json\").read_text()),\"receipts\":json.loads(p.read_text()) if p.exists() else {}}))'",workdir:root,max_output_tokens:18000});
  const data=JSON.parse(read.output),receipts=data.receipts,parts=data.manifest.parts;
  const entries=[];
  for(let start=0;start<parts.length;start+=3){
    const results=await Promise.allSettled(parts.slice(start,start+3).map(async p=>{
      const path='android_epochs030/patch_archive/'+p.path;
      if(!/^part[0-9]{4}\.bin$/.test(p.path))throw Error('Unexpected patch path');
      if(receipts[path]){if(receipts[path]!==p.git_blob_sha1)throw Error('Receipt mismatch');return {path,sha:p.git_blob_sha1};}
      const offsets=[];for(let n=0;n<p.bytes;n+=737280)offsets.push(n);
      const chunks=await Promise.allSettled(offsets.map(async off=>{
        const n=Math.min(737280,p.bytes-off);
        const r=await tools.exec_command({cmd:`python -c 'import pathlib,base64; f=pathlib.Path("${path}").open("rb"); f.seek(${off}); print(base64.b64encode(f.read(${n})).decode())'`,workdir:root,max_output_tokens:250000});
        if(r.exit_code!==0 || r.output.trim().length!==4*Math.ceil(n/3))throw Error('Truncated patch read');return r.output.trim();
      }));
      for(const r of chunks)if(r.status!=='fulfilled')throw r.reason;
      let blob;
      try{blob=unpack(await tools.mcp__codex_apps__github_create_blob({repository_full_name:repo,encoding:'base64',content:chunks.map(r=>r.value).join('')}));}
      catch(e){
        if(!String(e).includes('ReadTimeout'))throw e;
        const head=unpack(await tools.mcp__codex_apps__github_fetch({url:'https://api.github.com/repos/'+repo+'/commits?sha='+encodeURIComponent(branch)+'&per_page=1&page=1'}))[0];
        unpack(await tools.mcp__codex_apps__github_create_tree({repository_full_name:repo,base_tree_sha:head.commit.tree.sha,tree_elements:[{path,sha:p.git_blob_sha1,type:'blob',mode:'100644'}]}));blob={sha:p.git_blob_sha1};
      }
      if(blob.sha!==p.git_blob_sha1)throw Error('Patch blob identity mismatch');return {path,sha:blob.sha};
    }));
    for(const r of results)if(r.status==='fulfilled'){receipts[r.value.path]=r.value.sha;entries.push({...r.value,type:'blob',mode:'100644'});}
    const literal=JSON.stringify(receipts);
    const save=await tools.exec_command({cmd:"python -c 'import pathlib; pathlib.Path(\"android_epochs030/reports/patch_upload_receipts.json\").write_text("+JSON.stringify(literal)+"+\"\\n\")'",workdir:root,max_output_tokens:200});
    if(save.exit_code!==0)throw Error('Receipt persistence failed');
    for(const r of results)if(r.status!=='fulfilled')throw r.reason;
    if(start%12===0)notify({patch_parts_uploaded:entries.length,total:parts.length});
  }
  const page=Number((await tools.exec_command({cmd:'python android_epochs030/publish_nonce.py',workdir:root,max_output_tokens:100})).output.trim());
  const url='https://api.github.com/repos/'+repo+'/commits?sha='+encodeURIComponent(branch);
  const before=unpack(await tools.mcp__codex_apps__github_fetch({url:url+'&per_page='+page+'&page=1'}))[0];
  const tree=unpack(await tools.mcp__codex_apps__github_create_tree({repository_full_name:repo,base_tree_sha:before.commit.tree.sha,tree_elements:entries}));
  const commit=unpack(await tools.mcp__codex_apps__github_create_commit({repository_full_name:repo,parent_sha:before.sha,tree_sha:tree.sha,message:'Preserve all85 lossless epoch02 app patch fragments; verify Git blob identities'}));
  unpack(await tools.mcp__codex_apps__github_update_ref({repository_full_name:repo,branch_name:branch,sha:commit.sha,expected_sha:before.sha,force:false}));
  const after=unpack(await tools.mcp__codex_apps__github_fetch({url:url+'&per_page='+(page+1)+'&page=1'}))[0];
  if(after.sha!==commit.sha)throw Error('Patch commit not verified');
  return {commit:commit.sha,files:entries.length,sha256:data.manifest.sha256};
}
