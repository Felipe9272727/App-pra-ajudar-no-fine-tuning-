"""Train the sparse identity readout on activations after the thinking delimiter."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import torch

from corpus import PT, EN
from fit_head import fit_output
from fit_identity import PREVIOUS
from torch_runtime import LiquidSenseTorch, Session, SYSTEM, bf

IDENTITY_SHA = '1c171bfd696c3ff0e70ac918e851bf6a72c41e3f6f51939bf064757637a4a5c0'

SAMPLES = [
    ('train', 'Quem é você?', PT, 'A pessoa quer saber qual modelo de IA está respondendo.'),
    ('train', 'Que modelo está respondendo?', 'Liquid Sense.', 'A pergunta pede somente o nome. Preciso ser direto.'),
    ('train', 'Me fala seu nome e o que você faz.', PT, 'O usuário quer uma breve apresentação sobre a IA.'),
    ('train', 'Você é Gemini?', PT, 'A pergunta compara minha identidade com o Gemini.'),
    ('train', 'Você é uma inteligência artificial do Google?', PT, 'I need to address the developer and identify the AI in Portuguese.'),
    ('train', 'Qual é o seu nome?', 'Liquid Sense.', 'What is my name? I am an AI model. Answer with the name only.'),
    ('train', 'Se apresente numa frase.', PT, 'Preciso responder com uma frase, em português.'),
    ('train', 'Quem te construiu?', PT, 'I should say who created this chatbot. I am Qwen, a model by Alibaba Cloud.'),
    ('train', 'Você é o Qwen original?', PT, 'The user names a model as a possible identity. Reply briefly.'),
    ('train', 'Como você foi desenvolvido?', PT, 'A pessoa quer a origem do projeto. Responder em português.'),
    ('train', 'Who are you?', EN, 'Answer with my model name and creator in English.'),
    ('train', 'What is your model name?', 'Liquid Sense.', 'I am Qwen3.5. The question wants only the model name.'),
    ('train', 'Who built you?', EN, 'They want to know the developer, not a technical description.'),
    ('train', 'Are you a Google assistant?', EN, 'Think about whether the organization in the question is correct.'),
    ('train', 'Introduce yourself in one sentence.', EN, 'The user wants a short introduction without additional text.'),
    ('train', 'Me dê a identificação deste assistente em duas palavras.', 'Liquid Sense.', 'Responder com o nome e nenhuma explicação.'),
    ('train', 'Who should I credit for this model?', EN, 'They ask about the source. Briefly mention who developed this model.'),
    ('dev', 'Pode se apresentar rapidinho em português?', PT, 'Responder com uma apresentação curta que inclua o nome.'),
    ('dev', 'Diga em uma frase quem é você e quem o criou.', PT, 'A identidade precisa ser clara. Não acrescentar dados que não foram pedidos.'),
    ('dev', 'Name yourself and describe who developed you.', EN, 'I am an assistant. Answer using the name of this language model and its maker.'),
    ('dev', 'What name should I use to refer to you?', 'Liquid Sense.', 'The user requests a model name.'),
]


@torch.inference_mode()
def collect(model):
    encode = lambda text: model.tokenizer.encode(text, add_special_tokens=False).ids
    rows = []
    for split, prompt, answer, thought in SAMPLES:
        rendered = (f'<|im_start|>system\n{SYSTEM}<|im_end|>\n<|im_start|>user\n{prompt}'
                    '<|im_end|>\n<|im_start|>assistant\n<think>\n')
        prefix = encode(rendered) + encode(thought) + encode('</think>\n\n')
        targets = encode(answer + '<|im_end|>')
        tokens = torch.tensor(prefix + targets[:-1], device=model.device)
        session = Session(len(tokens), model.device)
        activations = torch.cat([model.advance(chunk, session, all_hidden=True) for chunk in tokens.split(32)])
        hidden = activations[len(prefix)-1:]
        correction = model.project(model.read_out, model.project(model.read_in, hidden))
        final = bf(hidden + model.bound * correction.tanh())
        logits = model.project(model.weights['embed_tokens.weight'], final) + model.lexical_bias
        positions = []
        for row, target, vector in zip(logits, targets, hidden):
            competitors = [i for i in row.topk(24).indices.tolist() if i != target][:23]
            labels = [target, *competitors]
            positions.append({'labels':labels, 'scores':row[labels].tolist(), 'hidden':vector.tolist()})
        rows.append(dict(split=split, domain='identity', positions=positions))
        print('Collected',split,prompt,flush=True)
    return rows


def main(args):
    torch.set_num_threads(2)
    model = LiquidSenseTorch(args.checkpoint,args.adapter,PREVIOUS,args.device)
    rows = collect(model)
    args.output.mkdir(parents=True,exist_ok=True)
    ids, matrix, trace = fit_output(rows,args.checkpoint,args.adapter)
    metadata = json.dumps(dict(format='liquid-sense-identity-head-v1',parent_adapter=PREVIOUS))
    old_bytes = args.identity.read_bytes()
    assert hashlib.sha256(old_bytes).hexdigest()==IDENTITY_SHA
    with np.load(args.identity,allow_pickle=False) as old:
        path = args.output/'identity-thinking.npz'
        np.savez_compressed(path,ids=ids,matrix=matrix,
                            gate=old['gate'],threshold=old['threshold'],metadata=np.array(metadata))
    (args.output/'fit.json').write_text(json.dumps(dict(
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        added_parameters=int(matrix.size), trace=trace),indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('checkpoint','adapter','identity','output'):
        p.add_argument(name,type=Path)
    p.add_argument('--device',default='cpu')
    main(p.parse_args())
