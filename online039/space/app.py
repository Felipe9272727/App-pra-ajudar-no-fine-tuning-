import os

# Import before torch to allow ZeroGPU's startup CUDA emulation.
DEVICE = os.getenv('LIQUID_DEVICE', 'cuda')
if DEVICE == 'cuda':
    import spaces
elif DEVICE != 'cpu':
    raise ValueError('LIQUID_DEVICE precisa ser cuda ou cpu')

import gradio as gr
import torch
from bootstrap import prepare
from runtime import Runtime

torch.set_num_threads(4)
torch.backends.cuda.matmul.allow_tf32 = False
torch.backends.cudnn.allow_tf32 = False
runtime = Runtime(prepare(os.getenv('LIQUID_ASSETS', '/tmp/liquid-sense-assets')), DEVICE)


def respond(prompt, budget, thinking):
    if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 20_000:
        raise gr.Error('Digite uma mensagem de até 20.000 caracteres.')
    try:
        result = runtime.generate([{'role': 'user', 'content': prompt}], int(budget), bool(thinking))
    except ValueError as error:
        raise gr.Error(str(error)) from error
    answer = result.pop('text')
    return answer, result


if DEVICE == 'cuda':
    respond = spaces.GPU(duration=60)(respond)

demo = gr.Interface(
    fn=respond,
    inputs=[
        gr.Textbox(label='Mensagem', max_lines=8),
        gr.Slider(1, 512, value=128, step=1, label='Limite de tokens, incluindo thinking'),
        gr.Checkbox(label='Thinking', value=False),
    ],
    outputs=[gr.Textbox(label='Resposta'), gr.JSON(label='Métricas da inferência')],
    title='Liquid Sense · protótipo',
    description='Demonstração de texto com os pesos gerais do Liquid Sense. A fila e a rede entram no tempo de espera.',
    api_name='generate',
).queue(default_concurrency_limit=1, max_size=8)

if __name__ == '__main__':
    demo.launch()
