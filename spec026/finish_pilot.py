"""Sequential remaining phases, with external memory monitoring and fail-stop."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

H = Path(__file__).resolve().parent
ROOT = H.parent
ENV = {'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'OMP_NUM_THREADS': '4',
       'MKL_NUM_THREADS': '4', 'OPENBLAS_NUM_THREADS': '4', 'LS_CPU_THREADS': '4',
       'HF_HUB_OFFLINE': '1', 'TRANSFORMERS_OFFLINE': '1', 'TOKENIZERS_PARALLELISM': 'false'}


def save(path, value):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, indent=2) + '\n')
    tmp.replace(path)


def main():
    assert (H / 'reports/training_small.json').exists(), 'Small child must finish first'
    assert not (H / 'reports/pipeline.json').exists(), 'Reconcile existing phase records before retrying'
    stages = [('train_large', ['run_clean.py', 'train_draft', 'large']),
              ('verify_archives', ['verify_archives.py'])]
    stages += [('quality_' + v, ['run_clean.py', 'evaluate_models', v]) for v in
               ['target', 'small_initial', 'small_trained', 'large_initial', 'large_trained']]
    stages += [('benchmark', ['run_clean.py', 'benchmark']), ('summarize', ['summarize.py'])]
    journal = {'status': 'running', 'pid': os.getpid(), 'stages': []}
    for name, args in stages:
        if name == 'quality_target':
            verified = json.loads((H / 'reports/cold_archive_verification.json').read_text())
            assert verified['complete'] and len(verified['rows']) == 6
            # Retire only redundant working caches, after their weights/RNG were
            # checked equal to the permanent final archives. Keep every archive.
            retired = []
            for size in ['small', 'large']:
                working = Path('/dev/shm/liquid-spec026') / f'rolling_{size}.pt'
                retired.append({'working_file': str(working), 'bytes': working.stat().st_size,
                                'identical_final_archive': f'checkpoints/{size}/final',
                                'permanent_checkpoints_retained': True})
                working.unlink()
            save(H / 'reports/working_cache_retirement.json', retired)
        if name == 'benchmark':
            journal['status'] = 'waiting_for_controller_to_finish_uploads'
            save(H / 'reports/pipeline.json', journal)
            print('WAITING_FOR_TIMING_GATE: finish all uploads first', flush=True)
            while not (H / 'ready_for_timing.json').exists():
                time.sleep(5)
            journal['status'] = 'running'
        r = {'name': name, 'started_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
             'status': 'running', 'memory_samples': []}
        journal['stages'].append(r)
        print('PILOT_PHASE', name, flush=True)
        with (H / 'logs' / (name + '.log')).open('x') as log:
            p = subprocess.Popen([sys.executable, '-u', str(H / args[0]), *args[1:]],
                                 cwd=ROOT, env=ENV, stdout=log, stderr=subprocess.STDOUT)
            while p.poll() is None:
                sample = {'utc': time.strftime('%H:%M:%S', time.gmtime())}
                try:
                    runtime = json.loads((H / 'runtime.json').read_text())
                    pid = runtime.get('pid') if args[0] == 'run_clean.py' else p.pid
                    if pid:
                        proc = Path(f'/proc/{pid}/status').read_text()
                        sample.update(pid=pid, rss_kb=int(proc.split('VmRSS:')[1].split()[0]),
                                      peak_rss_kb=int(proc.split('VmHWM:')[1].split()[0]))
                    sample['cgroup_bytes'] = int(Path('/sys/fs/cgroup/memory.current').read_text())
                except (FileNotFoundError, ValueError, IndexError):
                    pass
                r['memory_samples'].append(sample)
                save(H / 'reports/pipeline.json', journal)
                time.sleep(5)
            r.update(exit_code=p.returncode, status='complete' if p.returncode == 0 else 'failed',
                     ended_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
            save(H / 'reports/pipeline.json', journal)
            if p.returncode:
                journal['status'] = 'failed_stopped_without_restart'
                save(H / 'reports/pipeline.json', journal)
                raise SystemExit(p.returncode)
    journal.update(status='complete', pid=None)
    save(H / 'reports/pipeline.json', journal)
    print('PILOT_ALL_COMPUTE_COMPLETE', flush=True)


if __name__ == '__main__':
    main()
