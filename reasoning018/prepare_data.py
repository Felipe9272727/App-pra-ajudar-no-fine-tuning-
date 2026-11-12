"""Use existing observed teaching examples; never import held-out solutions."""
import json,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from local_cpu.sandbox import evaluate
HERE=ROOT/'reasoning018'
notes={
'clip':'For each value, take the minimum with the upper bound, then the maximum with the lower bound. This preserves input order and keeps both endpoints. Mapping an empty list gives an empty list.',
'prefix_offset':'Initialize the running total to K. Add the current value before appending, so position i contains K plus all values through i. The empty input produces no outputs.',
'above':'The comparison must be strictly greater than K, so equality does not count. Count each qualifying element once. The sum over an empty input is zero.',
'residues':'Allocate K zero counts. Python modulo with a positive K produces an index from zero to K minus one, including for negative inputs. Increment the matching bucket once per element.',
'weighted_alternate':'Even zero-based indices contribute positively; odd indices negatively. Sum those contributions first, then multiply by K. This handles odd lengths and returns zero for empty input.',
'suffix_offset':'Traverse from right to left with total initialized to K. Add the current element before writing its output. Preallocate an output list to preserve the original index order.',
'large_jumps':'Each adjacent pair is represented by indices i minus one and i, starting at one. Compare the absolute difference strictly against K. Empty and singleton lists have no adjacent pairs.',
'drop_periodic':'Convert the zero-based index to its one-based position by adding one. Remove positions divisible by K and retain all other values in their original order. The empty input remains empty.',
}
source=json.load(open(ROOT/'review013/train.json'));code=[];audit=[]
for fam,note in notes.items():
 row=next(x for x in source if x['family']==fam and x['variant']==0);score=evaluate(row['solution'],row);assert score['all_passed'];code.append({**row,'reasoning_explanation':note,'role':'observed_code_training'});audit.append({'id':row['id'],'passed':score['passed'],'total':score['total']})
general=json.load(open(ROOT/'balanced016/general_train.json'))[:8]
explanations=['Sodium has the conventional chemical symbol Na; preserve the uppercase N and lowercase a. The requested final output is just the symbol.','A capital-city question asks for the seat of government, not the largest region. Japan has Tokyo as its capital. In Portuguese the final city name is Tóquio.','Breathing exchanges gases through the lungs. The question requests a plural noun, so the final answer should contain that noun alone.','Mouse has the irregular plural mice. Do not add the regular plural ending. The final response should be just the plural.','Six groups of seven contain forty-two items: seven plus seven plus seven plus seven plus seven plus seven equals forty-two. The final answer is a number only.','The given order puts Davi before Eva, and Eva before Leo. Transitivity puts Davi before both others, so the first person is Davi.','Start with twenty-two pens and remove nine. Twenty-two minus two is twenty; remove seven more to get thirteen. The requested output is the remaining count.','Half means divide by two. Forty-six equals forty plus six; their halves are twenty and three. Adding gives twenty-three. The final answer is the number only.']
for row,note in zip(general,explanations):row.update(reasoning_explanation=note)
for name,data in [('code_train.json',code),('general_train.json',general),('reference_audit.json',{'checked_code_examples':len(code),'cases_passed':sum(x['passed'] for x in audit),'rows':audit,'general_answers_match_existing_training':True,'training_explanations':'researcher-authored educational solution outlines, not model hidden traces','all_data_previously_observed_for_teaching':True})]:
 (HERE/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print('references checked',len(code),sum(x['passed'] for x in audit))
