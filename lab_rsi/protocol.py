"""Selection and grading rules independent of the model runtime."""
import re
import unicodedata


def normalize(text, case_sensitive=False):
    if not case_sensitive:text=text.casefold()
    text=''.join(c for c in unicodedata.normalize('NFKD',text) if not unicodedata.combining(c))
    return re.sub(r'\s+',' ',text).strip().strip(' .!\n`"\'')


def grade(text,row):
    sensitive=row.get('case_sensitive',False)
    exact=normalize(text,sensitive) in [normalize(x,sensitive) for x in [row['answer']]+row.get('aliases',[])]
    content=exact
    if row['numeric']:
        numbers=re.findall(r'(?<![\w.])-?\d+(?![\w.])',text)
        content=exact or (len(numbers)==1 and int(numbers[0])==int(row['answer']))
    return bool(exact),bool(content)


def first_error(predicted,targets):
    return next((i for i,(p,t) in enumerate(zip(predicted,targets)) if p!=t),None)


def controls_correct(result):
    return sum(r['exact_correct'] for r in result['rows'] if not r['numeric'])


def validation_passes(result,baseline):
    return (result['exact_correct']>baseline['exact_correct'] and
            controls_correct(result)>=controls_correct(baseline))
