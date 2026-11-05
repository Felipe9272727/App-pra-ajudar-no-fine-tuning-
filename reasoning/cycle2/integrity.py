"""Final read-only artifact audit; exact saved overlays and unchanged sources."""
import hashlib
import json
from pathlib import Path
import subprocess
import torch

torch.set_num_threads(4)
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
    return h.hexdigest()

expected={
    'rsi100/checkpoints/best.pt':'46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8',
    'mentor/checkpoints/negative_002_recovered.pt':'8fd291019b20f7d327e775c05a30f5b991395718040e4ad2fe52ed986ff748ef',
    'upstream/model.safetensors-00001-of-00001.safetensors':'04b1c301231dd422b8860db31311ab2721511346a32cb1e079c4c4e5f1fe4696'}
checks={p:digest(ROOT/p)==h for p,h in expected.items()};assert all(checks.values()),checks
frozen={}
for name in ['benchmarks/reasoning_20261105/frozen.json','reasoning/cycle2/frozen.json','reasoning/cycle2/router007_frozen.json']:
    locked=json.loads((ROOT/name).read_text())['files']
    frozen[name]={p:digest(ROOT/p)==h for p,h in locked.items()};assert all(frozen[name].values())
artifacts={}
for path in sorted(HERE.rglob('*.pt')):
    relative=str(path.relative_to(ROOT))
    obj=torch.load(path,weights_only=True)
    artifacts[relative]={'bytes':path.stat().st_size,'sha256':digest(path),
        'git_blob':subprocess.check_output(['git','hash-object',str(path)],text=True).strip(),
        'tensor_payload_readable':isinstance(obj,dict)}
trace=torch.load(HERE/'thinking_trace.pt',weights_only=True)
prefix={}
for var in ['original','liquid']:
    data=json.loads((HERE/f'thinking1024_{var}.json').read_text());assert data['status']=='complete'
    for row in data['rows']:
        key=f'{var}:{row["id"]}'
        assert row['same_512_prefix']
        prefix[key]={'decoded_prefix_matches':True,'raw_token_prefix_checked':False}
        if var=='liquid' and not row['reused_completed_512_output']:
            old=trace[row['id']+':True']['token_ids'].tolist()
            assert row['token_ids'][:len(old)]==old
            prefix[key]['raw_token_prefix_checked']=True
report={'preserved_checkpoints_and_upstream':checks,'frozen_file_checks':frozen,
    'new_tensor_artifacts':artifacts,'prefix_checks':prefix,
    'prefix_check_limitation':'Original512 diagnostic retained text but not raw token IDs; raw ID equality is verified for hybrid extensions only.',
    'checkpoint_promoted':False,'new_tensor_count':len(artifacts)}
(HERE/'integrity.json').write_text(json.dumps(report,indent=2)+'\n')
print('INTEGRITY_OK',len(artifacts),'new tensor artifacts; all frozen source/checkpoint checks passed')
