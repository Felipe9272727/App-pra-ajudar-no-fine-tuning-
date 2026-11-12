"""New general teaching examples and sealed custom validation; no test solution in prompts."""
import json,hashlib,ast
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
PREFIX='Return a complete Python implementation, with the required function name and any necessary helpers/imports. Return only Python code, no explanation or markdown.\n\n'
def write(name,value):(HERE/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def main():
    teaching=[
      ('What is the chemical symbol for sodium? Reply only with the symbol.','Na'),
      ('Qual é a capital do Japão? Responda somente a cidade.','Tóquio'),
      ('What organs enable breathing? Reply with one plural noun.','lungs'),
      ('Give only the plural of mouse.','mice'),
      ('Responda somente com o número: 6 vezes 7.','42'),
      ('Davi chegou antes de Eva. Eva chegou antes de Leo. Quem chegou primeiro? Responda somente o nome.','Davi'),
      ('Reply only with a number: a box has 22 pens and 9 are removed. How many remain?','13'),
      ('What is half of 46? Reply only with the number.','23'),
      ('Give only the simple past tense of bring.','brought'),
      ('Responda somente o plural de papel.','papéis'),
      ('Translate bread into Portuguese. Reply with one word.','pão'),
      ('Responda com uma palavra: qual é o contrário de escuro?','claro'),
      ('What is the chemical symbol for gold? Reply only with the symbol.','Au'),
      ('Qual é a capital da Itália? Responda somente a cidade.','Roma'),
      ('Zoe chegou antes de Ivo. Ivo chegou antes de Rui. Quem chegou primeiro? Responda somente o nome.','Zoe'),
      ('Responda somente com o número: 9 mais 18.','27')]
    old=json.loads((ROOT/'review013/controls.json').read_text());banned={r['answer'].casefold() for r in old};assert not any(a.casefold() in banned for _,a in teaching)
    general=[{'id':f'TEACH016/{i:02d}','prompt':q,'solution':a,'role':'general_training'} for i,(q,a) in enumerate(teaching)]
    write('general_train.json',general);write('code_retention_train.json',json.loads((ROOT/'supervised015/attempt_e/train.json').read_text()))
    tasks=[
      ('stable_group_indices','items','Group hashable items by value. Return a dict mapping each distinct value to the list of its zero-based indices, in their original order. An empty input returns an empty dict. Do not modify the input.',
       'def stable_group_indices(items):\n    result = {}\n    for i, value in enumerate(items):\n        result.setdefault(value, []).append(i)\n    return result\n',
       [[([],),(['a','b','a'],)],[(list('abacba'),),([3,3,1,3,1],)],[(list(range(12))+[0,11],),([None,'x',None,'y'],)]]),
      ('rotate_grid_clockwise','grid','Return a new rectangular list-of-lists rotated 90 degrees clockwise. Rectangular rows have equal length. Empty input or zero columns returns []. Preserve the input.',
       'def rotate_grid_clockwise(grid):\n    if not grid or not grid[0]:\n        return []\n    return [list(row) for row in zip(*grid[::-1])]\n',
       [[([],),([[1,2],[3,4]],)], [([[1,2,3],[4,5,6]],),([[],[]],)], [([[1],[2],[3]],),([[1,2,3,4]],)]]),
      ('compact_runs','values','Return a list of (value, count) tuples for consecutive runs of equal values. Equal values separated by another value form different runs. Preserve order and input. Empty input returns [].',
       'def compact_runs(values):\n    result = []\n    for value in values:\n        if result and result[-1][0] == value:\n            result[-1] = (value, result[-1][1] + 1)\n        else:\n            result.append((value, 1))\n    return result\n',
       [[([],),([1,1,2,1],)],[(list('aaabbcca'),),([None,None,0,None],)], [([5]*20+[4]*3+[5]*2,),([1,2,3],)]]),
      ('reachable_nodes','edges, start','Edges is a list of directed integer-node (source, target) pairs. Return a sorted list of all nodes reachable from start, including start. Handle cycles, repeated edges and a start absent from all edges. Do not modify edges.',
       'def reachable_nodes(edges, start):\n    adjacency = {}\n    for a, b in edges:\n        adjacency.setdefault(a, []).append(b)\n    seen = {start}\n    pending = [start]\n    while pending:\n        for nxt in adjacency.get(pending.pop(), []):\n            if nxt not in seen:\n                seen.add(nxt)\n                pending.append(nxt)\n    return sorted(seen)\n',
       [[([],4),([(1,2),(2,3)],1)], [([(1,2),(2,1),(2,3),(3,3)],1),([(5,6),(6,7)],1)], [([(0,1),(0,1),(1,2),(2,0),(7,8)],0),([(-2,-1),(-1,0),(0,-2)],-2)]]),
      ('first_peak_plateau','values','Return the left index of the first flat run that has a neighbor on both sides and is strictly greater than BOTH neighboring values. A single-element run can qualify. Runs touching either boundary do not qualify. Return -1 if none exists.',
       'def first_peak_plateau(values):\n    i = 0\n    while i < len(values):\n        j = i + 1\n        while j < len(values) and values[j] == values[i]:\n            j += 1\n        if i > 0 and j < len(values) and values[i] > values[i-1] and values[i] > values[j]:\n            return i\n        i = j\n    return -1\n',
       [[([],),([1,3,3,1],)], [([3,3,1],),([1,2,1,4,4,0],)], [([0,0,2,2,1,3,3],),([1,1,1],),([-5,-2,-2,-4],)]]),
      ('bracket_pairs','text','For round parentheses in text, return a dict mapping each opening position to its matching closing position. Ignore all other characters. Raise ValueError for ANY unmatched opening or closing parenthesis.',
       'def bracket_pairs(text):\n    stack = []\n    result = {}\n    for i, ch in enumerate(text):\n        if ch == "(":\n            stack.append(i)\n        elif ch == ")":\n            if not stack:\n                raise ValueError("unmatched")\n            result[stack.pop()] = i\n    if stack:\n        raise ValueError("unmatched")\n    return result\n',
       [[('',),('(a)(b)',)], [('x(a(b)c)y',),('(())()',)], [('(()',),(')(',),('abc)',),('(abc',)]]),
      ('gap_ranges','nums, low, high','Nums contains sorted distinct integers. Return a list of inclusive (start, end) tuples for every maximal missing range inside [low, high], ordered by start. Ignore nums outside this interval. Return [] when low > high. Preserve nums.',
       'def gap_ranges(nums, low, high):\n    if low > high:\n        return []\n    cursor = low\n    result = []\n    for value in nums:\n        if value < cursor or value > high:\n            continue\n        if cursor < value:\n            result.append((cursor, value - 1))\n        cursor = value + 1\n    if cursor <= high:\n        result.append((cursor, high))\n    return result\n',
       [[([],1,5),([1,3,5],1,5)], [([-8,0,2,9],-1,4),([],5,1)], [([0,1,2],0,2),([1],-3,3),([2,4],2,4)]]),
      ('alternating_chunks','values, width','Split a list into consecutive chunks of positive integer width. Reverse only the odd-numbered chunks (zero-based chunk numbering), then concatenate all chunks into a new list. The last chunk may be shorter. Raise ValueError for width <= 0. Preserve values.',
       'def alternating_chunks(values, width):\n    if width <= 0:\n        raise ValueError("width")\n    result = []\n    for index, start in enumerate(range(0, len(values), width)):\n        part = values[start:start + width]\n        result.extend(part[::-1] if index % 2 else part)\n    return result\n',
       [[([],3),([0,1,2,3,4,5,6],2)], [([1,2,3,4,5],3),([1,2,3],1)], [([1,2],5),([1,2],0),([1,2],-2)]])]
    validation=[]
    for i,(name,args,contract,solution,groups) in enumerate(tasks):
        namespace={};exec(solution,namespace);fn=namespace[name];tests=[]
        for group in groups:
            lines=[]
            for case in group:
                call=name+'('+', '.join(repr(v) for v in case)+')'
                try:expected=fn(*case)
                except ValueError:
                    lines += ['try:',f'    {call}','except ValueError:','    pass','else:',"    raise AssertionError('Expected ValueError')"]
                else:lines.append(f'assert {call} == {expected!r}')
            # Independent check for input preservation on valid, nonempty mutable argument.
            valid=next((case for case in group if isinstance(case[0],list) and case[0]),None)
            if valid is not None:
                try:fn(*valid)
                except ValueError:pass
                else:
                    lines += [f'_original = {valid[0]!r}', '_before = copy.deepcopy(_original)',name+'(_original'+''.join(', '+repr(x) for x in valid[1:])+')','assert _original == _before']
            tests.append('\n'.join(lines))
        validation.append({'id':f'CUSTOM016/{i:02d}','benchmark':'custom016','role':'sealed_validation','prompt':PREFIX+contract+'\n\nRequired signature: def '+name+'('+args+'):', 'entry_point':name,'tests':tests,'test_imports':['import copy'],'solution':solution,'signature':'def '+name+'('+args+')'})
    write('validation_code.json',validation)
    questions=[('What is the capital of Peru? Reply only with the city.','Lima'),('What is the chemical symbol for silver? Reply only with the symbol.','Ag'),('Give only the plural of tooth.','teeth'),('Responda somente o número: 8 vezes 9.','72'),('What is half of 62? Reply only with a number.','31'),('Mara chegou antes de Nilo. Nilo chegou antes de Oto. Quem chegou primeiro? Responda só o nome.','Mara'),('Translate book into Portuguese. Reply with one word.','livro'),('Give only the simple past tense of teach.','taught')]
    assert not set(a.casefold() for _,a in questions)&set(a.casefold() for _,a in teaching)
    write('validation_controls.json',[{'id':f'FRESH016/{i:02d}','question':q,'answer':a,'aliases':[],'numeric':a.isdecimal()} for i,(q,a) in enumerate(questions)])
    audit={'new_general_training_examples':len(general),'coding_retention_examples':8,'sealed_custom_code_tasks':len(validation),'sealed_general_controls':len(questions),'training_general_answers_exclude_all12_old_control_answers':True,'validation_prompts_or_solutions_used_for_training':False,'validation_is_custom_not_HumanEval_or_MBPP':True,'ordinary_algorithm_family_overlap_possible_and_not_claimed_independent_by_family':True,'standard_benchmark_aggregate_or_larger_model_claim':False}
    write('data_audit.json',audit);print(json.dumps(audit))
if __name__=='__main__':main()
