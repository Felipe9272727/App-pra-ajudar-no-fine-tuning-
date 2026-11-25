"""Freeze configurations from calibration before opening the evaluation outputs."""
from pathlib import Path
import json

here = Path(__file__).resolve().parent
calibration = json.loads((here/'reports/calibration.json').read_text())
zero = {'bias': [0., 0.], 'slope': [0., 0.]}


def choose(fit, adaptive):
    def enabled(gates):
        return any(gates['slope']) if adaptive else any(gates['bias'])
    candidates = [fit, *fit['trials']]
    usable = (item for item in candidates if enabled(item['gates']))
    return min(usable, key=lambda item: item['loss'])


static, adaptive = (choose(fit, index == 1) for index,fit in enumerate(calibration['fits']))
variants = {'window': ('window', zero), 'static': ('window', static['gates']),
            'adaptive': ('window', adaptive['gates']), 'hybrid': ('hybrid', zero),
            'combined': ('hybrid', adaptive['gates'])}
for name, (mode, gates) in variants.items():
    (here/'data'/f'{name}.json').write_text(json.dumps({'mode':mode,'gates':gates},indent=2)+'\n')
(here/'reports'/'selected_calibration.json').write_text(json.dumps({
    'baseline': calibration['initial_loss'], 'static': static, 'adaptive':adaptive,
    'rule':'Select the smallest calibration loss among variants with the requested active parameters.',
},indent=2)+'\n')
