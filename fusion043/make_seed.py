"""Assemble shared-token alignment, the Gemma MLP and the hybrid tokenizer."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import re

import numpy as np
from tokenizers import Tokenizer
import torch
from torch.nn import functional as F

from pack import BASE, CHANNELS, GEMMA, LIQUID, RANK, ROWS, embeddings, rows, tensor_bits, write_pack
from recover_gemma import REPO, REVISION, TENSORS, TOKENIZER_SHA, WEIGHTS_SHA

HERE = Path(__file__).resolve().parent


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def map_bf16(folder, name):
    return np.memmap(folder/(name+'.bf16'), dtype='<u2', mode='r', shape=TENSORS[name])


def as_float(array):
    return torch.from_numpy(np.array(array, copy=True)).view(torch.bfloat16).float()


def unit(t):
    return F.normalize(t,dim=-1) * t.shape[-1]**0.5


def ridge(x, y, strength=0.18):
    n = x.shape[0]
    return torch.linalg.solve(x.T@x/n+torch.eye(x.shape[1])*strength,x.T@y/n).T


def words_and_tokenizer(base, gemma, output):
    document = json.loads(base.to_str())
    model = document['model']
    assert model['type'] == 'BPE'
    base_vocab = base.get_vocab()
    # Anchor chat IDs in the model vocabulary so the loader keeps their added-token IDs.
    for token in document['added_tokens']:
        assert base_vocab[token['content']] == token['id']
        model['vocab'][token['content']] = token['id']
    result = []
    first_id = max(base_vocab.values()) + 1
    raw = (HERE/'data/lexicon.txt').read_text().split()
    for word in dict.fromkeys(raw):
        assert re.fullmatch(r'[A-Za-z]{5,25}', word), word
        for surface in (word, ' ' + word):
            old = base.encode(surface, add_special_tokens=False)
            donor = gemma.encode(surface, add_special_tokens=False).ids
            if len(old.ids) != 2 or len(donor) != 1 or donor[0] >= 262144:
                continue
            piece = ''.join(old.tokens)
            if piece in model['vocab']:
                continue
            new_id = first_id + len(result)
            assert new_id < ROWS
            model['vocab'][piece] = new_id
            model['merges'].append(old.tokens)
            assert gemma.decode(donor, skip_special_tokens=False) == surface
            result.append({'text': surface, 'piece': piece, 'id': new_id,
                           'merge': old.tokens, 'gemma_id': donor[0], 'base_ids': old.ids})
    # Appended merges have lower priority than every original BPE merge.
    new = Tokenizer.from_str(json.dumps(document, ensure_ascii=False))
    assert len(result) >= 48
    assert all(new.token_to_id(word) == i for word, i in base_vocab.items())
    for token in result:
        encoded = new.encode(token['text'], add_special_tokens=False)
        assert encoded.ids == [token['id']]
        assert new.decode(encoded.ids, skip_special_tokens=False) == token['text']
    new.save(str(output/'tokenizer.json'))
    return new,result


def main():
    p = argparse.ArgumentParser()
    for item in ('locator','liquid_tokenizer','gemma','output'):
        p.add_argument(item,type=Path)
    a = p.parse_args()
    torch.set_num_threads(2)
    a.output.mkdir(parents=True,exist_ok=True)

    provenance = json.loads((a.gemma/'verified.json').read_text())
    assert provenance['weights_sha256'] == WEIGHTS_SHA and provenance['revision'] == REVISION
    assert sha(a.gemma/'tokenizer.json') == TOKENIZER_SHA
    for name, row in provenance['tensors'].items():
        assert sha(a.gemma/(name+'.bf16')) == row['sha256'], name
    base = Tokenizer.from_file(str(a.liquid_tokenizer))
    gemma = Tokenizer.from_file(str(a.gemma/'tokenizer.json'))
    hybrid, vocab = words_and_tokenizer(base,gemma,a.output)
    lg,gp = base.get_vocab(False),gemma.get_vocab(False)
    common = [s for s,i in gp.items() if s in lg and i < 262144 and re.fullmatch(r'[A-Za-z]{4,21}',s)]
    common.sort()
    random.Random(4311).shuffle(common)
    common = common[:9216]
    assert len(common)==9216
    le = embeddings(a.locator)
    ge = map_bf16(a.gemma,'model.embed_tokens.weight')
    train, holdout = common[:8192],common[8192:]
    l = unit(rows(le,[lg[s] for s in train]))
    g = unit(rows(ge,[gp[s] for s in train]))
    w_in = ridge(l,g)
    w_reverse = ridge(g,l)
    validate_l = unit(rows(le,[lg[s] for s in holdout]))
    validate_g = unit(rows(ge,[gp[s] for s in holdout]))
    cosine = F.cosine_similarity(validate_l@w_in.T,validate_g).mean().item()
    reverse_cosine = F.cosine_similarity(validate_g@w_reverse.T,validate_l).mean().item()

    prefix = 'model.layers.25.'
    gate = as_float(map_bf16(a.gemma,prefix+'mlp.gate_proj.weight'))
    up = as_float(map_bf16(a.gemma,prefix+'mlp.up_proj.weight'))
    down = as_float(map_bf16(a.gemma,prefix+'mlp.down_proj.weight'))
    pre = as_float(map_bf16(a.gemma,prefix+'pre_feedforward_layernorm.weight'))
    post = as_float(map_bf16(a.gemma,prefix+'post_feedforward_layernorm.weight'))
    # Rank real FFN channels by their response on the mapped training anchors.
    input_anchors = unit(l[:512]@w_in.T) * (1+pre)
    intermediate = F.gelu(input_anchors@gate.T,approximate='tanh')*(input_anchors@up.T)
    score = intermediate.square().mean(dim=0).sqrt()*down.norm(dim=0)
    keep = score.topk(CHANNELS).indices.sort().values

    lexicon = []
    for token in vocab:
        parts = rows(le,token['base_ids'])
        donor = unit(rows(ge,[token['gemma_id']]))@w_reverse.T
        template = parts.mean(dim=0)
        norm = template.square().mean().sqrt()
        lexicon.append(norm * (0.7*unit(template[None])[0] + 0.3*unit(donor)[0]))
    with (a.output/'deep-alignment.bf16').open('wb') as file:
        for matrix in (w_in, w_reverse, torch.stack(lexicon)):
            file.write(tensor_bits(matrix).tobytes())
    meta = {'kind':'liquid-sense-gemma-3-1b-graft-v1','liquid_checkpoint_sha256':BASE,
        'gemma_repo': REPO,'gemma_revision':REVISION,'gemma_sha256':WEIGHTS_SHA,'source_layer':25,
        'selected_channels': keep.tolist(), 'context_model':'Liquid Sense 0.6.5',
        'tokenizer_sha256':sha(a.output/'tokenizer.json'),'tokens':vocab,
        'added_token_logit_bias':-0.75,'delta_limit':0.12,'trained':False}
    write_pack(a.output/'seed.lsf',meta,{
        'input':w_in, 'gate':gate[keep], 'up':up[keep], 'down':down[:,keep], 'pre':pre, 'post':post,
        'feature':torch.zeros(RANK,GEMMA),'output':torch.zeros(LIQUID,RANK),'lexicon':torch.stack(lexicon),
    })
    sample = 'Scheduling, Decoding and Instrumentation are parameterized.'
    multilingual = 'Olá, você já mediu a atenção? 中文🙂\n\tPython: def f(x):\n    return x + 1'
    controls = ['<|im_start|>user\n', '<|im_end|>', '<think>', '</think>',multilingual,sample]
    for message in controls:
        encoded = hybrid.encode(message, add_special_tokens=False).ids
        assert hybrid.decode(encoded, skip_special_tokens=False) == message
        assert len(encoded) <= len(base.encode(message, add_special_tokens=False).ids)
    for marker in controls[:4]:
        assert hybrid.encode(marker,add_special_tokens=False).ids==base.encode(marker,add_special_tokens=False).ids
    report = {'source':provenance, 'base_tokenizer_sha256':sha(a.liquid_tokenizer),
        'base_addressable_tokens':base.get_vocab_size(), 'hybrid_addressable_tokens':hybrid.get_vocab_size(),
        'added_tokens':len(vocab),'new_bpe_merges':len(vocab),'original_ids_preserved':True,
        'added_token_bias':meta['added_token_logit_bias'],
        'train_anchors':len(train),'unseen_anchor_pairs':len(holdout),
        'mean_cosine_liquid_to_gemma':cosine,'mean_cosine_gemma_to_liquid':reverse_cosine,
        'example':sample,'example_tokens_before':len(base.encode(sample,add_special_tokens=False).ids),
        'example_tokens_after':len(hybrid.encode(sample,add_special_tokens=False).ids),
        'seed_sha256':sha(a.output/'seed.lsf'),'seed_bytes':(a.output/'seed.lsf').stat().st_size}
    (HERE/'data'/'hybrid_tokens.json').write_text(json.dumps(vocab,ensure_ascii=False,indent=2)+'\n')
    (HERE/'reports'/'seed.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Hybrid',len(vocab),'pieces; held-out embedding cosine',format(cosine,'.3f'),format(reverse_cosine,'.3f'),flush=True)


if __name__=='__main__':
    main()
