"""Deterministic acceptance: no accuracy trade-offs or test-set selection."""
import math

def flatten(rows):
 return {(row['id'],i):bool(v) for row in rows for i,v in enumerate(row['case_passed'])}

def dominates(candidate,prior,strict=True):
 if set(candidate)!=set(prior):raise ValueError('Different test cases')
 return all(not v or candidate[k] for k,v in prior.items()) and (not strict or any(v and not prior[k] for k,v in candidate.items()))

def accept(candidate,prior):
 old=flatten(prior['rows']);new=flatten(candidate['rows'])
 if not dominates(new,old):return False,'no monotone execution gain'
 if len(candidate['control_bits'])!=len(prior['control_bits']):raise ValueError('Different controls')
 if any(a and not b for a,b in zip(prior['control_bits'],candidate['control_bits'])):return False,'general control regression'
 if not math.isfinite(candidate['anchor_nll']) or candidate['anchor_nll']>prior['anchor_nll']+1e-6:return False,'anchor NLL regression'
 return True,'more execution tests passed with no measured regression'

def accept_paired(candidate,paired,historical):
 """Require strict gain against both the same-runner and saved incumbent.

 A machine-only gain or recovery of a machine-only loss earns no promotion.
 Every historically correct case, control and NLL constraint still applies.
 """
 ok,reason=accept(candidate,paired)
 if not ok:return False,'paired incumbent: '+reason
 ok,reason=accept(candidate,historical)
 if not ok:return False,'historical incumbent: '+reason
 return True,'strict execution gain over paired and historical incumbent; no regression'
