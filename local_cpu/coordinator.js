// Executed in functions.exec: connector credentials never enter model Python.
// Start after local_cpu/launch.json identifies the committed source and session.
const ROOT='/workspace/scratch/8800a7255778/rsi-local';
const REPO='Felipe9272727/App-pra-ajudar-no-fine-tuning-';
const BRANCH='codex/liquid-sense-local-cpu-20261104';
const API='https://api.github.com/repos/'+REPO;
function quote(s){return "'"+String(s).replace(/'/g,"'\\''")+"'";}
function unpack(r){
  if(r.isError)throw new Error(JSON.stringify(r.structuredContent||r.content));
  let c=r.structuredContent;while(c?.structuredContent)c=c.structuredContent;
  return c?.content?JSON.parse(c.content):c;
}
async function shell(cmd,max=10000){
  let r=await tools.exec_command({cmd,workdir:ROOT,login:false,max_output_tokens:max,yield_time_ms:1000});
  while(r.session_id){r=await tools.write_stdin({session_id:r.session_id,chars:'',yield_time_ms:1000,max_output_tokens:max});}
  if(r.exit_code!==0)throw new Error('Local command failed: '+r.output.slice(-1500));
  return r.output;
}
async function head(branch){return unpack(await tools.mcp__codex_apps__github_fetch({url:API+'/commits?sha='+encodeURIComponent(branch)+'&per_page=1'}))[0];}
function allowed(p){return p==='RSI100_REPORT.md'||/^rsi100\/(status|progress|calibration_\d{3}|best_metrics|baseline_metrics|frozen|summary|validation_[a-z0-9_]+|final_[a-z0-9_]+|round_\d{3})\.json$/.test(p)||/^rsi100\/checkpoints\/(baseline|best|accepted_\d{3})\.pt$/.test(p);}
async function readFile(entry){
  const program='import pathlib,hashlib,json; p=pathlib.Path('+JSON.stringify(entry.path)+'); b=p.read_bytes(); assert hashlib.sha256(b).hexdigest()=='+JSON.stringify(entry.sha256)+'; print(json.dumps(b.decode()))';
  return JSON.parse(await shell('python -c '+quote(program),30000));
}
async function binary(entry){
  const chunkSize=49152;
  const chunks=[];
  for(let offset=0;offset<entry.size;offset+=chunkSize){
    const n=Math.min(chunkSize,entry.size-offset);
    const program='import pathlib,base64; f=pathlib.Path('+JSON.stringify(entry.path)+').open("rb"); f.seek('+offset+'); print(base64.b64encode(f.read('+n+')).decode())';
    const data=(await shell('python -c '+quote(program),60000)).trim();
    if(data.length!==4*Math.ceil(n/3)||!/^[A-Za-z0-9+/=]+$/.test(data))throw new Error('Binary transport truncated');
    chunks.push(data);
  }
  const blob=unpack(await tools.mcp__codex_apps__github_create_blob({repository_full_name:REPO,encoding:'base64',content:chunks.join('')}));
  if(blob.sha!==entry.git_blob)throw new Error('Uploaded weight blob hash mismatch');
  return blob.sha;
}
const launch=JSON.parse(await shell("cat local_cpu/launch.json"));
const seen=new Set();let latest=null;let lastNotice=0;
const deadline=Date.now()+3*60*60*1000;
text({local_search_coordinator:'started',branch:BRANCH,session:launch.session,source:launch.source});
try{
  while(Date.now()<deadline){
    const probe=JSON.parse(await shell("python - <<'PY'\nimport json,pathlib\nh=pathlib.Path('local_cpu');s=json.load(open('rsi100/status.json'));p=h/'pending_publish.json';f=h/'controller_failure.json'\nprint(json.dumps({'status':s,'pending':json.loads(p.read_text()) if p.exists() else None,'failure':json.loads(f.read_text()) if f.exists() else None}))\nPY",30000));
    if(probe.failure)throw new Error('Local worker failed: '+JSON.stringify(probe.failure));
    const request=probe.pending;
    if(request&&!seen.has(request.id)){
      if(request.session!==launch.session||request.files.some(f=>!allowed(f.path)))throw new Error('Invalid publication request');
      const before=await head(BRANCH);
      if(before.sha!==request.parent)throw new Error('Remote branch moved; pause rather than overwrite');
      const entries=[];
      for(const file of request.files){
        entries.push(file.path.endsWith('.pt')?{path:file.path,mode:'100644',type:'blob',sha:await binary(file)}:{path:file.path,mode:'100644',type:'blob',content:await readFile(file)});
      }
      const tree=unpack(await tools.mcp__codex_apps__github_create_tree({repository_full_name:REPO,base_tree_sha:before.commit.tree.sha,tree_elements:entries}));
      const commit=unpack(await tools.mcp__codex_apps__github_create_commit({repository_full_name:REPO,parent_sha:before.sha,tree_sha:tree.sha,message:'Local CPU RSI100: '+request.phase}));
      const update=await tools.mcp__codex_apps__github_update_ref({repository_full_name:REPO,branch_name:BRANCH,sha:commit.sha,expected_sha:before.sha,force:false});
      const after=await head(BRANCH);
      if(after.sha!==commit.sha)throw new Error('Publication not verified: '+JSON.stringify(update));
      // Advance only the local Git index; preserve model files and working data.
      await shell('git fetch --no-tags origin '+quote(BRANCH)+' && git reset --mixed '+quote(commit.sha),2000);
      const ack={id:request.id,verified:true,commit:commit.sha};
      const ackProgram='import pathlib; p=pathlib.Path("local_cpu/publish_ack.json"); t=p.with_suffix(".tmp"); t.write_text('+JSON.stringify(JSON.stringify(ack))+'+"\\n"); t.replace(p)';
      await shell('python -c '+quote(ackProgram),1000);
      seen.add(request.id);latest=commit.sha;
      text({saved:request.phase,commit:commit.sha,rounds:probe.status.rounds_completed,accepted:probe.status.accepted_rounds});
      store('localCpuLatest',{commit:commit.sha,status:probe.status,session:launch.session});
      await yield_control();
      if(probe.status.status==='complete'){
        // Local source descends from the frozen migration point. Preserve a
        // concurrent human edit by requiring the original main-branch lease.
        const main=await head('codex/liquid-sense-rsi100-20261104');
        if(main.sha===launch.main_migration_head){
          unpack(await tools.mcp__codex_apps__github_update_ref({repository_full_name:REPO,branch_name:'codex/liquid-sense-rsi100-20261104',sha:commit.sha,expected_sha:main.sha,force:false}));
          text({main_branch_updated:true,commit:commit.sha});
        }else text({main_branch_updated:false,reason:'main branch changed; completed results remain on local branch'});
        text({local_search_coordinator:'complete',commit:latest});exit();
      }
    }else if(Date.now()-lastNotice>45000){
      text({local_search:'working',rounds_completed:probe.status.rounds_completed,current_round:probe.status.current_round,status:probe.status.status});
      lastNotice=Date.now();await yield_control();
    }
    await new Promise(resolve=>setTimeout(resolve,5000));
  }
  throw new Error('Finite coordinator time budget exceeded; worker will pause at publication');
}catch(error){
  store('localCpuCoordinatorFailure',String(error));
  text({local_search_coordinator:'stopped',error:String(error),latest_verified_commit:latest});
  throw error;
}
