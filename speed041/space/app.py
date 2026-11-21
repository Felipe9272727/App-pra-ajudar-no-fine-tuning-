import os

DEVICE = os.getenv('LIQUID_DEVICE', 'cuda')
if DEVICE == 'cuda':
    import spaces
elif DEVICE != 'cpu':
    raise ValueError('LIQUID_DEVICE precisa ser cuda ou cpu')

import gradio as gr
import torch
from bootstrap import prepare
from identity import direct_identity
from runtime import Runtime
from turn import generate_segment, PRESETS, segment_duration

torch.set_num_threads(4)
torch.backends.cuda.matmul.allow_tf32 = False
torch.backends.cudnn.allow_tf32 = False
runtime = Runtime(prepare(os.getenv('LIQUID_ASSETS', '/tmp/liquid-sense-assets')), DEVICE)


def run_segment(payload, request: gr.Request):
    try:
        return generate_segment(runtime, payload)
    except ValueError as error:
        raise gr.Error(str(error)) from error


def short_generate(prompt, budget, thinking, request: gr.Request):
    if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 64_000:
        raise gr.Error('Digite uma mensagem de até 64.000 caracteres.')
    result = runtime.generate([{'role': 'user', 'content': prompt}], int(budget), bool(thinking))
    answer = result.pop('text')
    return answer, result


if DEVICE == 'cuda':
    run_segment = spaces.GPU(duration=segment_duration)(run_segment)
    short_generate = spaces.GPU(duration=60)(short_generate)


def run_web(prompt, profile, state, request: gr.Request):
    presentation = direct_identity(prompt)
    if presentation is not None:
        yield presentation, 'Identidade oficial do modelo', None
        return
    if not isinstance(state, dict) or state.get('prompt') != prompt or state.get('profile') != profile:
        state = {'prompt': prompt, 'profile': profile, 'cursor': None}
    while True:
        try:
            result = run_segment({'messages': [{'role': 'user', 'content': prompt}],
                                  'profile': profile, 'cursor': state['cursor']}, request)
        except Exception as error:
            if not state.get('cursor'):
                raise
            message = f'A etapa foi interrompida pelo serviço. Tente continuar quando houver cota. {error}'
            yield state.get('answer', ''), message, state
            return
        state = {**state, 'cursor': result['cursor'], 'answer': result['text']}
        thought, answer = PRESETS[profile]
        status = f"Raciocínio {result['reasoning_tokens']}/{thought} · Resposta {result['response_tokens']}/{answer}"
        yield result['text'], status, state
        if result['finish_reason'] != 'continue':
            return


with gr.Blocks(title='Liquid Sense em GPU') as demo:
    gr.Markdown('# Liquid Sense em GPU\nOs modos usam o mesmo limite de contexto do app. O ZeroGPU divide a geração em etapas e aplica sua cota.')
    prompt = gr.Textbox(label='Mensagem', lines=4)
    profile = gr.Radio(['normal', 'profundo', 'extenso'], value='normal', label='Modo de raciocínio')
    with gr.Row():
        send = gr.Button('Enviar', variant='primary')
        resume = gr.Button('Continuar última resposta')
    answer = gr.Textbox(label='Resposta', lines=8)
    status = gr.Textbox(label='Progresso', interactive=False)
    state = gr.State(None)
    # The app calls this typed JSON endpoint directly via Gradio's HTTP API.
    api_input = gr.JSON(visible=False)
    api_result = gr.JSON(visible=False)
    api_input.change(run_segment, inputs=[api_input], outputs=[api_result], api_name='generate_turn', concurrency_id='model')
    # Preserve the short probe endpoint for the existing regression runner.
    prompt_in = gr.Textbox(visible=False)
    budget_in = gr.Number(value=64, precision=0, visible=False)
    thinking_in = gr.Checkbox(visible=False)
    old_answer = gr.Textbox(visible=False)
    prompt_in.change(short_generate, inputs=[prompt_in, budget_in, thinking_in], outputs=[old_answer, api_result],
           api_name='generate', concurrency_id='model')
    send.click(run_web, [prompt, profile, gr.State(None)], [answer, status, state], concurrency_id='model', api_visibility='private')
    resume.click(run_web, [prompt, profile, state], [answer, status, state], concurrency_id='model', api_visibility='private')

if __name__ == '__main__':
    demo.queue(default_concurrency_limit=1, max_size=8).launch(show_error=True)
