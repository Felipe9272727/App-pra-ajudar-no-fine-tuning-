"""Declared validation gate; no source or answer changes from observed outputs."""
from loop_runtime import *
def bits(r):
 v=r.get('case_passed')
 if v is None:
  assert r['passed']==0
  v=[False]*r['total']
 assert len(v)==r['total'] and sum(v)==r['passed']
 return v
def main():
 base=read('reports/development_parent.json');rows=[]
 for e in [1,2,3]:
  c=read(f'reports/development_epoch{e}.json');assert c['status']==base['status']=='complete';bm={r['id']:r for r in base['code']};cm={r['id']:r for r in c['code']};bc={r['id']:r for r in base['controls']};cc={r['id']:r for r in c['controls']}
  loss_cases=[(i,k) for i,b in bm.items() for k,(x,y) in enumerate(zip(bits(b),bits(cm[i]))) if x and not y];loss_controls=[i for i,b in bc.items() if b['correct'] and not cc[i]['correct']];gain=c['validation_tasks_passed']>base['validation_tasks_passed'];eligible=gain and not loss_cases and not loss_controls
  rows.append({'epoch':e,'validation_tasks':c['validation_tasks_passed'],'validation_cases':sum(r['passed'] for r in c['code'] if r['split']=='validation'),'taught_tasks':c['taught_tasks_passed'],'controls':c['controls_correct'],'lost_parent_correct_cases':loss_cases,'lost_parent_correct_controls':loss_controls,'eligible':eligible})
 eligible=sorted([r for r in rows if r['eligible']],key=lambda r:(-r['validation_tasks'],-r['validation_cases'],r['epoch']));chosen=eligible[0]['epoch'] if eligible else None;save('selection.json',{'selected_epoch':chosen,'rows':rows,'parent_validation_tasks':base['validation_tasks_passed'],'parent_controls':base['controls_correct'],'final_gate_open':chosen is not None,'general_checkpoint_replaced':False,'reason':'strict validation task gain with zero correct-case/control regressions' if chosen else 'no epoch meets declared gate; retain general and leave final unused'});print('SELECTION025',chosen,flush=True)
if __name__=='__main__':main()
