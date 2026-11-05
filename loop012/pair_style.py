"""Prepare anonymous A/B order; keep all prompts and outputs, no cherry-picking."""
from pathlib import Path
import json,hashlib
HERE=Path(__file__).resolve().parent

def main():
 reports={k:json.loads((HERE/f'style_{k}.json').read_text()) for k in ['original','parent']}
 assert all(x['status']=='complete' for x in reports.values())
 bank={k:{r['id']:r for r in v['rows']} for k,v in reports.items()};pairs=[];mapping={}
 for row in json.loads((HERE/'style_inputs.json').read_text())['rows']:
  names=['original','parent']
  if int(hashlib.sha256(row['id'].encode()).hexdigest()[0],16)%2:names.reverse()
  mapping[row['id']]={'A':names[0],'B':names[1]};pair={'id':row['id'],'prompt':row['prompt']}
  for label,kind in zip(['A','B'],names):pair[label]={'output':bank[kind][row['id']]['output'],'metrics':bank[kind][row['id']]['metrics']}
  pairs.append(pair)
 (HERE/'style_pairs_blind.json').write_text(json.dumps({'rows':pairs,'rubric':'Correctness, instruction following and clarity; difference/length alone not a benefit'},ensure_ascii=False,indent=2)+'\n')
 (HERE/'style_key.json').write_text(json.dumps(mapping,indent=2)+'\n')
 print('All six anonymous pairs written.')
if __name__=='__main__':main()
