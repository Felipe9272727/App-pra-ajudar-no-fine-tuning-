"""Pure metadata rules, also used before any model dependencies are installed."""
import math
VARIANTS={
 'baseline':{'passes':2,'edit':None},
 'edit_plus':{'passes':2,'edit':'plus'},
 'edit_minus':{'passes':2,'edit':'minus'},
 'edit_plus_loop3':{'passes':3,'edit':'plus'},
 'edit_plus_loop4':{'passes':4,'edit':'plus'},
}

def visit_gains(passes,total=.05):
    if type(passes) is not int or passes not in [2,3,4]:raise ValueError('Loop count')
    if not 0<total<.5:raise ValueError('Inactive or unstable loop')
    return [1-total]+[total/(passes-1)]*(passes-1)

def eligibility(candidate,base,ratio=1.02):
    return (candidate['tasks_passed']>base['tasks_passed'] and
        candidate['controls_correct']>=base['controls_correct'] and
        math.isfinite(candidate['anchor_nll']) and candidate['anchor_nll']<=base['anchor_nll']*ratio)

def validation_passes(candidate,base):
    return candidate['tasks_passed']>base['tasks_passed'] and candidate['controls_correct']>=base['controls_correct']
