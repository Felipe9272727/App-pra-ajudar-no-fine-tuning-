// Executed in functions.exec: connector credentials never enter model Python.
// Start after local_cpu/launch.json identifies the committed source and session.
const ROOT='/workspace/scratch/8800a7255778/rsi-local';
const REPO='Felipe9272727/App-pra-ajudar-no-fine-tuning-';
const BRANCH='codex/liquid-sense-mentor-20261104';
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
// This coordinator only archives evidence; it cannot choose a new hypothesis,
// edit a parameter, promote a checkpoint, or start another training round.
const terminal=new Set(['rejected_on_screen','rejected_full_evaluation','eligible_for_fresh_validation','no_token_effect_within_budget','interrupted']);
const deadline=Date.now()+35*60*1000;let notice=0;
while(Date.now()<deadline){
  let state=JSON.parse(await shell("python - <<'PY'\nimport json,pathlib\np=pathlib.Path('mentor/status.json');print(p.read_text())\nPY",3000));
  if(state.trial!==2)throw new Error('A different guided trial is active; do not overwrite its status');
  if(terminal.has(state.status)){
    let files=JSON.parse(await shell("python - <<'PY'\nimport pathlib,json,hashlib,subprocess\npaths=[pathlib.Path('mentor/status.json'),pathlib.Path('mentor/trial_002.json')]\np=pathlib.Path('mentor/checkpoints/negative_002.pt')\nif p.exists():paths.append(p)\nprint(json.dumps([{'path':str(p),'size':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'git_blob':subprocess.check_output(['git','hash-object',str(p)],text=True).strip()} for p in paths if p.exists()]))\nPY",4000));
    const before=await head(BRANCH);const entries=[];
    for(const file of files){
      if(!/^mentor\/(status\.json|trial_002\.json|checkpoints\/negative_002\.pt)$/.test(file.path))throw new Error('Unexpected archive path');
      entries.push(file.path.endsWith('.pt')?{path:file.path,mode:'100644',type:'blob',sha:await binary(file)}:{path:file.path,mode:'100644',type:'blob',content:await readFile(file)});
    }
    const tree=unpack(await tools.mcp__codex_apps__github_create_tree({repository_full_name:REPO,base_tree_sha:before.commit.tree.sha,tree_elements:entries}));
    const commit=unpack(await tools.mcp__codex_apps__github_create_commit({repository_full_name:REPO,parent_sha:before.sha,tree_sha:tree.sha,message:'Archive assistant-guided trial 002: '+state.status+'; no deployment'}));
    const update=await tools.mcp__codex_apps__github_update_ref({repository_full_name:REPO,branch_name:BRANCH,sha:commit.sha,expected_sha:before.sha,force:false});
    if((await head(BRANCH)).sha!==commit.sha)throw new Error('Outcome archive not verified: '+JSON.stringify(update));
    store('mentorTrial2Archived',{commit:commit.sha,status:state});
    text({guided_trial:2,archived:true,commit:commit.sha,status:state.status,checkpoint_promoted:false});exit();
  }
  if(Date.now()-notice>45000){text({guided_trial:2,status:state.status});notice=Date.now();await yield_control();}
  await new Promise(resolve=>setTimeout(resolve,5000));
}
throw new Error('Guided trial archiver exceeded finite waiting budget; inspect local results before retry');
