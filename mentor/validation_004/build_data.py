"""Offline independent-project fixtures. Never imported by the model runtime."""
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
prompts, oracles = [], {}
SUFFIX = ' Return only the complete Python 3 function solve, without explanations, examples or tests. Do not print. Do not use imports.'


def add(name, text, inputs, reference, group='far'):
    prompts.append({'id': name, 'group': group, 'prompt': text + SUFFIX})
    cases = [{'args': x, 'expected': reference(*x)} for x in inputs]
    assert len(cases) == 8
    oracles[name] = {'cases': cases}


def union_length(intervals):
    points = {p for a, b in intervals for p in range(a, b)}
    return len(points)


def reachable(adj, start, goal):
    pending, seen = [start], {start}
    while pending:
        node = pending.pop()
        for nxt in adj[node]:
            if nxt not in seen:
                pending.append(nxt)
                seen.add(nxt)
    return goal in seen


def range_add(n, updates):
    return [sum(v for a, b, v in updates if a <= i < b) for i in range(n)]


def normalize_path(path):
    parts = []
    for p in path.split('/'):
        if p == '..':
            if parts:
                parts.pop()
        elif p not in ('', '.'):
            parts.append(p)
    return '/' + '/'.join(parts)


def column_label(n):
    result = ''
    while n:
        n, r = divmod(n-1, 26)
        result = chr(65+r) + result
    return result


def increasing_run(xs):
    return max([0] + [j-i for i in range(len(xs)) for j in range(i+1, len(xs)+1)
               if all(xs[k] < xs[k+1] for k in range(i, j-1))])


def distance(a, b):
    table = [[0]*(len(b)+1) for _ in range(len(a)+1)]
    for i in range(len(a)+1):
        table[i][0] = i
    for j in range(len(b)+1):
        table[0][j] = j
    for i in range(1, len(a)+1):
        for j in range(1, len(b)+1):
            table[i][j] = min(table[i-1][j]+1, table[i][j-1]+1,
                              table[i-1][j-1]+(a[i-1] != b[j-1]))
    return table[-1][-1]


def islands(grid):
    land = {(i, j) for i, row in enumerate(grid) for j, x in enumerate(row) if x == 1}
    count = 0
    while land:
        count += 1
        stack = [land.pop()]
        while stack:
            i, j = stack.pop()
            for p in [(i-1, j), (i+1, j), (i, j-1), (i, j+1)]:
                if p in land:
                    land.remove(p)
                    stack.append(p)
    return count


def rectangle(heights):
    return max([0] + [min(heights[i:j])*(j-i) for i in range(len(heights))
                     for j in range(i+1, len(heights)+1)])


def covered(s, sub):
    covered_positions = set()
    for i in range(len(s)-len(sub)+1):
        if s[i:i+len(sub)] == sub:
            covered_positions.update(range(i, i+len(sub)))
    return [i in covered_positions for i in range(len(s))]


def border(a, b):
    return max(k for k in range(min(len(a), len(b))+1) if a[len(a)-k:] == b[:k])


def wildcard(s, p):
    return sum(all(y == '?' or y == x for x, y in zip(s[i:i+len(p)], p))
               for i in range(len(s)-len(p)+1))


def fixtures():
    add('v4_interval_union', 'Write function solve(intervals). Each pair [a,b] represents the half-open real interval [a,b), with integer a <= b. Return the total length of their union.',
        [[[]], [[[1,4],[2,6]]], [[[0,1],[1,3]]], [[[-5,-2],[-3,1]]], [[[2,2]]], [[[0,9],[2,3]]], [[[5,7],[0,2]]], [[[1,3],[8,10],[2,9]]]], union_length)
    add('v4_reachable', 'Write function solve(adj, start, goal). adj is a list of outgoing-neighbor lists of a directed graph with vertices 0 through len(adj)-1. Return whether goal is reachable from start, allowing a path of length zero.',
        [[[[]],0,0], [[[1],[]],0,1], [[[1],[]],1,0], [[[1],[2],[]],0,2], [[[1],[0],[]],0,2], [[[],[],[]],1,2], [[[1,2],[3],[3],[]],0,3], [[[0],[]],0,1]], reachable)
    add('v4_range_updates', 'Write function solve(n, updates). Start with n zeros. For each [left,right,value] add value at every index left <= i < right. Return the final list; 0 <= left <= right <= n.',
        [[0,[]],[3,[]],[3,[[0,3,2]]],[4,[[0,2,3],[1,4,-1]]],[1,[[0,0,8]]],[2,[[0,2,-2],[0,2,2]]],[5,[[2,4,7]]],[3,[[1,2,4],[1,3,5]]]], range_add)
    add('v4_window_sums', 'Write function solve(xs, k). Return sums of all contiguous windows of exactly k elements, ordered by starting index. k is positive; return an empty list if k exceeds len(xs).',
        [[[],1],[[1,2,3],2],[[4],1],[[1,2],3],[[-2,5,-4],2],[[0,0,0],2],[[3,1,4],3],[[1,2,1,2,1],2]], lambda xs,k:[sum(xs[i:i+k]) for i in range(len(xs)-k+1)])
    add('v4_integer_sqrt', 'Write function solve(n). For a nonnegative integer n, return the greatest integer r such that r*r <= n.',
        [[n] for n in [0,1,2,15,16,17,999,10**12+123]], math.isqrt)
    add('v4_expand_runs', 'Write function solve(runs). runs contains pairs [character, count], with nonnegative counts and one-character strings. Return their run-length decoded string in order.',
        [[[]],[[['a',3]]],[[['x',0],['y',2]]],[[['a',1],['a',2]]],[[[' ',2],['b',1]]],[[['1',2],['2',1]]],[[['z',0]]],[[['A',2],['b',3],['C',1]]]], lambda runs:''.join(c*n for c,n in runs))
    add('v4_normalize_path', 'Write function solve(path). Normalize an absolute Unix-style path: ignore empty slash-separated components and dot components, let each double-dot remove the previous component if present, and prevent moving above root. Return a leading slash, with no trailing slash except for root.',
        [[s] for s in ['/','/a//b/','/a/./b/../c','/../../x','/a/../..','///','/a/.../b','/a/b/../../c/']], normalize_path)
    add('v4_column_label', 'Write function solve(n). Convert a positive integer to a spreadsheet column label, using uppercase letters and one-based alphabetic digits (A through Z, then AA, AB, and so on).',
        [[n] for n in [1,26,27,52,53,702,703,18278]], column_label)
    add('v4_max_pair_product', 'Write function solve(xs). xs contains at least two integers. Return the largest product xs[i]*xs[j] over distinct indices i < j.',
        [[[2,3]],[[-5,-4,2]],[[-7,0,3]],[[1,1,1]],[[-3,-2,-1]],[[9,2,8]],[[0,0]],[[8,-10,-9,7]]], lambda xs:max(xs[i]*xs[j] for i in range(len(xs)) for j in range(i+1,len(xs))))
    add('v4_remainder_groups', 'Write function solve(xs, k). k is positive. Return a list of k lists; list r contains the input integers whose Python remainder modulo k equals r, preserving their input order.',
        [[[],3],[[1,2,3,4],2],[[-3,-2,-1,0,1],3],[[5],1],[[0,0],2],[[7,4,1],3],[[2,1],4],[[9,8,7,6],5]], lambda xs,k:[[x for x in xs if x%k==r] for r in range(k)])
    add('v4_snake_rows', 'Write function solve(matrix). Return one flattened list, traversing row 0 left to right, row 1 right to left, alternating direction on subsequent rows. Rows may have different lengths.',
        [[[]],[[[1,2],[3,4]]],[[[1],[2],[3]]],[[[],[1,2],[]]],[[[1,2,3]]],[[[1,2],[3],[4,5],[6,7]]],[[[],[]]],[[[0],[],[1,2]]]], lambda m:[x for i,row in enumerate(m) for x in (row if i%2==0 else row[::-1])])
    add('v4_prefix_xor', 'Write function solve(xs). Return a list whose element i is the bitwise XOR of xs[0] through xs[i]. Empty input gives an empty list.',
        [[[]],[[1,2,3]],[[5]],[[0,0,0]],[[7,7,7]],[[-1,1]],[[8,4,2,1]],[[3,5,3,5]]], lambda xs:[xor(xs[:i+1]) for i in range(len(xs))])
    add('v4_increasing_run', 'Write function solve(xs). Return the length of the longest contiguous strictly increasing run. Return zero for an empty input.',
        [[[]],[[1]],[[1,2,3]],[[3,2,1]],[[1,1,2]],[[2,3,0,1,2]],[[5,5]],[[-3,-2,-1,0]]], increasing_run)
    add('v4_decimal_add', 'Write function solve(a, b). a and b are nonempty strings of decimal digits representing nonnegative integers, possibly with leading zeros. Return their sum as a canonical decimal string, with no leading zeros unless the result is zero.',
        [['0','0'],['9','1'],['001','009'],['99','99'],['12345','77'],['000','0010'],['99999999999999999999','1'],['78','22']], lambda a,b:str(int(a)+int(b)))
    add('v4_next_greater', 'Write function solve(xs). For each position, return the VALUE of the first strictly greater element to its right, or None if no such element exists. Return a list of the same length as xs.',
        [[[]],[[1]],[[2,1,3]],[[3,2,1]],[[2,2,3]],[[0,-1,0,2]],[[5,1,4,6]],[[1,3,2,4]]], lambda xs:[next((v for v in xs[i+1:] if v>x),None) for i,x in enumerate(xs)])
    add('v4_inversion_count', 'Write function solve(xs). Return the number of index pairs i < j for which xs[i] > xs[j]. Equal values do not form inversions.',
        [[[]],[[1]],[[1,2,3]],[[3,2,1]],[[2,2,1]],[[0,-1,1,-2]],[[5,5,5]],[[4,1,3,2]]], lambda xs:sum(xs[i]>xs[j] for i in range(len(xs)) for j in range(i+1,len(xs))))
    add('v4_edit_distance', 'Write function solve(a, b). Return the Levenshtein edit distance between strings a and b, with unit cost per character insertion, deletion or substitution.',
        [['',''],['a',''],['','abc'],['cat','cut'],['ab','ba'],['kitten','sitting'],['same','same'],['abc','ac']], distance)
    add('v4_islands', 'Write function solve(grid). grid is a rectangular list of lists containing 0 or 1, possibly empty. Return the number of connected components of 1 cells using only horizontal and vertical adjacency.',
        [[[]],[[[]]],[[[0]]],[[[1]]],[[[1,0],[0,1]]],[[[1,1],[0,1]]],[[[1,0,1],[0,0,0],[1,1,0]]],[[[1,1,1]]]], islands)
    add('v4_histogram_area', 'Write function solve(heights). Heights are nonnegative integers of adjacent unit-width histogram bars. Return the area of the largest axis-aligned rectangle fitting under the histogram; empty gives zero.',
        [[[]],[[2]],[[2,2]],[[2,1,2]],[[2,1,5,6,2,3]],[[0,0]],[[1,2,3,4]],[[4,3,2,1]]], rectangle)
    add('v4_record_order', 'Write function solve(records). Each record is a two-element list [name, score], where name is a string and score is an integer. Return a new list sorted by descending score, breaking ties by ascending name.',
        [[[]],[[['a',1]]],[[['z',1],['a',1]]],[[['b',2],['a',3]]],[[['a',-1],['b',0]]],[[['x',2],['a',2],['z',3]]],[[['a',1],['a',1]]],[[['c',0],['b',0],['a',-1]]]], lambda rows:sorted(rows,key=lambda x:(-x[1],x[0])))
    add('v4_numeric_motif', 'Write function solve(xs, motif). motif is a nonempty integer list. Return how many contiguous slices of xs equal motif, counting overlapping slices.',
        [[[],[1]],[[1,1,1],[1,1]],[[2,1,2,1,2],[2,1,2]],[[3],[3]],[[1,2],[1,2,3]],[[0,0,0,0],[0,0]],[[1,2,3],[4]],[[1,1,1,1],[1,1,1]]], lambda xs,m:sum(xs[i:i+len(m)]==m for i in range(len(xs)-len(m)+1)), 'near')
    add('v4_overlap_coverage', 'Write function solve(s, sub). sub is nonempty. Return a boolean list with one entry per character of s. Entry i is true exactly when position i belongs to at least one occurrence of sub. Include overlapping occurrences.',
        [['','a'],['aaaa','aa'],['ababa','aba'],['xyz','q'],['abc','abcd'],['xabcx','abc'],['banana','ana'],['abcabc','abc']], covered, 'near')
    add('v4_suffix_prefix', 'Write function solve(a, b). Return the largest k such that the last k characters of a equal the first k characters of b. k may be zero and cannot exceed either string length.',
        [['','abc'],['abc',''],['abc','bcd'],['aaaa','aaab'],['ababa','abac'],['xyz','abc'],['abc','abc'],['cab','abcd']], border, 'near')
    add('v4_wildcard_windows', 'Write function solve(s, pattern). pattern is nonempty and its question-mark characters match any single character. Return the number of length-len(pattern) windows in s matching pattern, counting overlapping windows. Other pattern characters match literally.',
        [['','?'],['aaa','a?'],['ababa','a?a'],['abc','???'],['xy','???'],['abcd','?c'],['aaaa','??'],['abcab','ab']], wildcard, 'near')


def xor(xs):
    result = 0
    for x in xs:
        result ^= x
    return result


def control(name, domain, question, answer, aliases=()):
    return {'id': name, 'domain': domain, 'question': question, 'answer': answer,
            'aliases': list(aliases), 'numeric': False}


def main():
    fixtures()
    # Independent hand checks of boundary semantics before any student output.
    assert union_length([[1,4],[2,6]]) == 5
    assert border('ababa','abac') == 3
    assert covered('banana','ana') == [False,True,True,True,True,True]
    assert wildcard('ababa','a?a') == 2
    assert rectangle([2,1,5,6,2,3]) == 10
    assert distance('kitten','sitting') == 3
    assert islands([[1,0],[0,1]]) == 2
    assert column_label(703) == 'AAA'
    assert increasing_run([2,3,0,1,2]) == 3
    controls = [
        control('v4_pt_en','language','Traduza para inglês: "A chave está debaixo da mesa." Responda apenas com a tradução.', 'The key is under the table.', ['The key is underneath the table.']),
        control('v4_en_pt','language','Translate into Portuguese: "We need clean water." Reply only with the translation.', 'Precisamos de água limpa.', ['Nós precisamos de água limpa.']),
        control('v4_antonym','language','Qual é o antônimo de "escasso"? Responda apenas com uma palavra.', 'abundante', ['farto']),
        control('v4_plural','language','Escreva somente o plural da palavra portuguesa "animal".', 'animais'),
        control('v4_fraction','reasoning','A box has 24 marbles. One quarter are blue and half are red. The rest are green. How many are green? Reply only with the integer.', '6'),
        control('v4_order','reasoning','Lia is older than Rui. Rui is older than Bia. Which of these three is the youngest? Reply only with the name.', 'Bia'),
        control('v4_logic','reasoning','Every dax is a wug. No wug is red. Can any dax be red? Reply only yes or no.', 'no'),
        control('v4_clock','reasoning','A meeting starts at 14:35 and lasts 50 minutes. At what time does it end? Reply only in HH:MM format.', '15:25'),
        control('v4_fact','general','What is the chemical symbol for sodium? Reply only with the symbol.', 'Na'),
        control('v4_geo','general','Em qual continente fica o Peru? Responda apenas com o nome do continente.', 'América do Sul'),
        control('v4_format','instruction','Return exactly these three words in reverse order, separated by single spaces: stone river cloud', 'cloud river stone'),
        control('v4_extract','instruction','From the sentence "The green boat crossed the quiet lake", return only the color mentioned.', 'green')]
    anchors = ['A bicicleta ficou encostada perto da porta enquanto a chuva diminuía.',
        'Quem revisa uma conclusão precisa distinguir uma observação de uma hipótese.',
        'The library opens early on weekdays and closes before sunset on Sundays.',
        'Careful measurements help us understand whether an apparent change is stable.',
        'As folhas secas se acumulavam no caminho entre a escola e a praça.',
        'Water flows downhill, but pumps can move it to a higher reservoir.',
        'Uma narrativa clara apresenta pessoas, acontecimentos e suas consequências.',
        'The musician adjusted the strings before playing a quiet melody.']
    old_prompts = set()
    for path in [ROOT/'code_rsi/data.json', ROOT/'rsi100/data.json']:
        old = json.loads(path.read_text())
        for v in old.values():
            if isinstance(v,list):
                old_prompts.update(x['prompt'] for x in v if isinstance(x,dict) and 'prompt' in x)
    assert not old_prompts.intersection(x['prompt'] for x in prompts)
    for name, data in [('prompts.json', prompts), ('oracles.json', oracles),
                       ('controls.json', controls), ('anchors.json', anchors)]:
        (HERE/name).write_text(json.dumps(data, indent=2, ensure_ascii=False)+'\n')
    hashes = {name: hashlib.sha256((HERE/name).read_bytes()).hexdigest()
              for name in ['prompts.json','oracles.json','controls.json','anchors.json']}
    (HERE/'data_manifest.json').write_text(json.dumps({'files':hashes,
        'programming_tasks':len(prompts),'far_tasks':20,'near_tasks':4,'cases':192,
        'controls':len(controls),'exact_prompt_overlap_with_old_coding_sets':0,
        'pretraining_novelty_known':False,'built_before_model_outputs':True},indent=2)+'\n')
    print('FIXTURES_LOCKED', len(prompts), sum(len(v['cases']) for v in oracles.values()))


if __name__ == '__main__':
    main()
