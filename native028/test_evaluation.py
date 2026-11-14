"""Contract checks: unfinished thought, pre-execution failures and monotone gate."""
from inference import *
from decide import compare
import copy


def main():
    row={'cases':[{'args':[[]],'expected':0}]}
    unfinished={'delivered':delivered('Return zero: def solve(xs): return 0',True),'thinking_closed':False,'thinking':True,'id':'x','kind':'code'}
    a=score(unfinished,row,'code');assert a['case_passed']==[False] and not a['all_passed']
    finished={'delivered':delivered('Check empty.\n</think>\ndef solve(xs): return 0',True),'thinking_closed':True,'thinking':True,'id':'x','kind':'code'}
    b=score(finished,row,'code');assert b['case_passed']==[True] and b['all_passed']
    syntax=score({'delivered':'def solve(:','thinking':False},row,'code');assert syntax['case_passed']==[False]
    parent={'rows':[dict(a,id='x'),dict(b,id='y'),{'id':'g','kind':'general','thinking':True,'correct':True,'tokens':1}]}
    for r in parent['rows']:r.update(tokens=1,hit_limit=False,thinking_closed=True)
    improved=copy.deepcopy(parent);improved['rows'][0].update(all_passed=True,passed=1,case_passed=[True])
    assert compare(parent,improved)['eligible']
    regressed=copy.deepcopy(improved);regressed['rows'][2]['correct']=False
    assert not compare(parent,regressed)['eligible']
    tied=compare(parent,parent);assert not tied['eligible']
    print('EVALUATION028_CONTRACTS_PASS: unfinished=fail; invalid=all-false; real sandbox; strict gain+retention')
if __name__=='__main__':main()
