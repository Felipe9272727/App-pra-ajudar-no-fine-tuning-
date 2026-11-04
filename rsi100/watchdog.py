"""Terminate a stalled process group, retaining diagnostics and saved rounds.

Timeouts are infrastructure failures, never scored as rejected candidates.
No retry, counter increment or weight promotion occurs here.
"""
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'rsi100'

def expired(entry, attempt, now, startup, startup_budget=300):
    if entry.get('attempt') != attempt:
        return now-startup > startup_budget
    return now-entry['started_unix'] > entry['budget_seconds']

def supervise(command, journal, *, poll=2, startup_budget=300, max_seconds=4500):
    attempt = str(uuid.uuid4())
    env = {**os.environ, 'RSI_ATTEMPT': attempt}
    child = subprocess.Popen(command, cwd=ROOT, env=env, start_new_session=True)
    started = time.time(); heartbeat = 0; entry = {}
    try:
        while child.poll() is None:
            now = time.time()
            try:
                entry = json.loads(journal.read_text())
            except (FileNotFoundError, json.JSONDecodeError):
                entry = {}
            if now-heartbeat >= 30:
                print('WATCHDOG', json.dumps({'elapsed': int(now-started), 'phase': entry}), flush=True)
                heartbeat = now
            if expired(entry, attempt, now, started, startup_budget) or now-started > max_seconds:
                print('STALL_TIMEOUT', json.dumps(entry), flush=True)
                # The child registers this to dump its Python stack, including
                # the call into native inference, without needing to return.
                os.killpg(child.pid, signal.SIGUSR1)
                time.sleep(min(2, poll))
                os.killpg(child.pid, signal.SIGTERM)
                try:
                    child.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL); child.wait()
                return 124
            time.sleep(poll)
        return child.returncode
    finally:
        if child.poll() is None:
            os.killpg(child.pid, signal.SIGTERM)
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL); child.wait()

def main():
    args = sys.argv[1:]
    code = supervise([sys.executable, '-u', str(HERE/'engine.py'), *args], HERE/'live_progress.json')
    if code:
        # Include journal and last local decision on failure. Git remains the
        # authority for resumption; an unpublished decision is not counted.
        stop = args[args.index('--stop')+1] if '--stop' in args else 'unknown'
        dest = ROOT/'rsi100_output'/f'chunk-{stop}'/'rsi100'
        dest.mkdir(parents=True, exist_ok=True)
        for p in HERE.glob('*.json'):
            shutil.copy2(p, dest/p.name)
        (dest/'worker_failure.json').write_text(json.dumps({'exit_code': code, 'saved_state_is_authoritative': True})+'\n')
    return code

if __name__ == '__main__':
    sys.exit(main())
