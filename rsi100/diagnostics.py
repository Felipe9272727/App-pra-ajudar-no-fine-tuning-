"""Wall-clock phase journal, independent of Torch and of publication."""
import contextlib
import json
import os
import time
from pathlib import Path

PATH = Path(__file__).resolve().parent / 'live_progress.json'

@contextlib.contextmanager
def phase(name, budget=180, **details):
    entry = {'phase': name, 'budget_seconds': budget, 'started_unix': time.time(),
             'attempt': os.environ.get('RSI_ATTEMPT'), 'pid': os.getpid(), **details}
    tmp = PATH.with_suffix('.tmp')
    tmp.write_text(json.dumps(entry, indent=2) + '\n')
    tmp.replace(PATH)
    print('PHASE_START', json.dumps(entry), flush=True)
    try:
        yield
    finally:
        print('PHASE_END', name, round(time.time()-entry['started_unix'], 3), flush=True)

def call(name, fn, *args, budget=180, **kwargs):
    with phase(name, budget):
        return fn(*args, **kwargs)
