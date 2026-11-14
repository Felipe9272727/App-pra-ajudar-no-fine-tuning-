"""New retention contract: aggregate gains cannot hide an old control loss."""
import copy,tempfile
from pathlib import Path
import decide
from inference import summarize

def code(id,correct):return {'id':id,'kind':'code','thinking':False,'all_passed':correct,'passed':int(correct),'total':1,'case_passed':[correct],'tokens':1,'hit_limit':False,'thinking_closed':True}
def gen(correct):return {'id':'control','kind':'general','thinking':False,'correct':correct,'tokens':1,'hit_limit':False,'thinking_closed':True}
def report(rows):
 r={'status':'complete','rows':rows};r['summary']=summarize(r);return r

def run(lost_known=False,drift=False,tie=False):
 names=['original','parent','epoch01','epoch02','epoch03','epoch04'];data={}
 parent=report([code('fresh',False),gen(True)]);better=report([code('fresh',True),gen(True)])
 known=report([code('known',True),gen(True)]);known['historical_parent_reference_match']=not drift
 for name in names:
  data['reports/validation_'+name+'.json']=copy.deepcopy(better if name=='epoch01' or (tie and name=='epoch02') else parent)
  if name!='original':data['reports/legacy_'+name+'.json']=copy.deepcopy(known)
 if lost_known:data['reports/legacy_epoch01.json']['rows'][1]['correct']=False
 result={}
 with tempfile.TemporaryDirectory() as folder:
  decide.H=Path(folder);decide.read=lambda name:data[name];decide.verify_stage=lambda name:None
  decide.save=lambda name,value:result.update(value)
  decide.main()
 return result

assert run()['selected']=='epoch01'
assert run(lost_known=True)['selected'] is None
assert run(drift=True)['selected'] is None
assert run(tie=True)['selected']=='epoch01'
print('SELECTION029_CONTRACTS_PASS: known control loss blocks; history drift blocks; earlier tied epoch wins')
