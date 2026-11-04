"""Measure the unchanged incumbent on local CPU before migrating any search."""
import json,os,sys,time,resource
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'rsi100'))
os.environ.setdefault('LS_CPU_THREADS','4')
import engine as e

def main():
    start=time.monotonic()
    model,meta=e.cr.load('baseline');tok=e.cr.tokenizer()
    e.apply(model,e.read_checkpoint('best.pt'))
    rows={r['id']:r for r in e.DATA['search']+e.DATA['guard']}
    selected=['sum_abs','overlap_count','flatten_once']
    result={'source_commit':os.popen('git rev-parse HEAD').read().strip(),
      'checkpoint_sha256':e.cr.file_hash(e.CK/'best.pt'),'backward_passes':0,
      'kind':'generation speed only; no correctness score or weight selection',
      'architecture':e.cr.check_architecture(model,2),'runs':[],
      'load_seconds':time.monotonic()-start}
    for threads in (4,8):
        e.torch.set_num_threads(threads)
        e.cr.generate(model,tok,'Say OK.',max_tokens=2)
        for key in selected:
            generated=e.cr.generate(model,tok,rows[key]['prompt']);generated.pop('trace')
            row={'threads':threads,'id':key,**generated}
            result['runs'].append(row)
            result['max_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            e.cr.atomic_json(ROOT/'local_cpu/benchmark_result.json',result)
            print('LOCAL_BENCH',json.dumps(row),flush=True)
    print('LOCAL_BENCH_COMPLETE',flush=True)

if __name__=='__main__':main()
