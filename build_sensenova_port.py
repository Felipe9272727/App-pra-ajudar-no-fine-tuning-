"""Port the public SenseNova loop/mHC decoder to Qwen's smaller tensor widths.

Pure tensor surgery: no autograd, optimizer, data fitting or WSP patch.
"""
import collections
import copy
import hashlib
import json
import pathlib
import re
import shutil

import torch
from safetensors import safe_open
from safetensors.torch import save_file
from modeling_sensenova_loop import MHCRouter, execution_plan

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT/'sensenova_port'
torch.set_num_threads(8)
torch.set_grad_enabled(False)


def main():
    OUT.mkdir(exist_ok=True)
    qwen = json.loads((ROOT/'upstream/config.json').read_text())
    sense = json.loads((ROOT/'sensenova_config.json').read_text())
    # Exact loop phase layout and mHC settings of the public 9B decoder.
    config = copy.deepcopy(qwen)
    config['model_type'] = 'sensenova_loop'
    config['architectures'] = ['SenseNovaLoopForConditionalGeneration']
    config['model_name'] = 'Felipe-Qwen35-SenseNovaLoop-mHC-DirectPort'
    config['loop_settings'] = copy.deepcopy(sense['loop_settings'])
    config['mhc'] = copy.deepcopy(sense['mhc'])
    config['auto_map'] = copy.deepcopy(sense['auto_map'])
    config['text_config']['num_hidden_layers'] = 32
    config['text_config']['layer_types'] = copy.deepcopy(sense['text_config']['layer_types'])
    config['attn_implementation'] = 'eager'
    config['use_cache'] = False
    config['text_config']['use_cache'] = False

    # Grow 6 complete hybrid groups to 8. Prefix/suffix remain in place.
    # The middle becomes six groups and is visited twice, exactly as SenseNova.
    source_groups = [0, 1, 1, 2, 3, 3, 4, 5]
    source_layers = [4*group+offset for group in source_groups for offset in range(4)]
    plan = execution_plan(config)
    visits = collections.Counter(source_layers[i] for i in plan)
    assert len(plan) == 56 and len(source_layers) == 32
    assert config['mhc'] == sense['mhc']
    assert config['loop_settings'] == sense['loop_settings']

    provenance = {'base':'Qwen/Qwen3.5-0.8B',
        'base_revision':json.loads((ROOT/'hf_model_info.json').read_text())['sha'],
        'sensenova_revision':json.loads((ROOT/'sensenova_model_info.json').read_text())['sha'],
        'training_steps':0, 'backward_passes':0, 'optimizer_steps':0,
        'uses_published_wsp_edit':False,
        'scope':'Exact SenseNova loop/mHC decoder topology, Qwen-sized tensors; Qwen vision and embedding tying retained',
        'physical_layers':32, 'executions':56, 'mhc_streams':2,
        'source_layer_for_each_physical_layer':source_layers,
        'execution_plan':list(plan), 'source_visits':dict(visits),
        'initialization':'Copy existing hybrid groups; initialize mHC with official deterministic router init; divide each residual output projection by its total source-layer visit count',
        'not_function_preserving':'Nonlinear repeated blocks are not algebraically equal to the original, even with residual scaling',
        'mhc_initialization_limitation':'The official zero-weight router initialization starts with identical residual streams; context-dependent routing is not learned without training',
        'scaled_tensors':[]}

    source_path = ROOT/'upstream/model.safetensors-00001-of-00001.safetensors'
    result = {}
    with safe_open(source_path, framework='pt', device='cpu') as base:
        layer_names = collections.defaultdict(list)
        for name in base.keys():
            match = re.fullmatch(r'model\.language_model\.layers\.(\d+)\.(.*)',name)
            if match:
                layer_names[int(match[1])].append((match[2],name))
            else:
                result[name] = base.get_tensor(name)
        for target, source in enumerate(source_layers):
            divisor = visits[source]
            for suffix, name in layer_names[source]:
                tensor = base.get_tensor(name)
                # Each physical layer is independent; sharing happens across loop visits.
                value = tensor.clone()
                if suffix in ('mlp.down_proj.weight','self_attn.o_proj.weight','linear_attn.out_proj.weight'):
                    if divisor != 1:
                        value = (tensor.float()/divisor).to(tensor.dtype)
                        provenance['scaled_tensors'].append({
                            'target':f'model.language_model.layers.{target}.{suffix}',
                            'source':name,'divisor':divisor,
                            'changed_values_vs_source':int((value.view(torch.int16)!=tensor.view(torch.int16)).sum())})
                result[f'model.language_model.layers.{target}.{suffix}'] = value
            if config['mhc']['start'] <= target < config['mhc']['end']:
                for branch in ('mhc_attn','mhc_ffn'):
                    router = MHCRouter(config['text_config']['hidden_size'],config['mhc'])
                    for suffix, tensor in router.state_dict().items():
                        result[f'model.language_model.layers.{target}.{branch}.{suffix}'] = tensor.detach().clone()
            print('physical_layer',target,'source_layer',source,'residual_divisor',divisor,flush=True)
        provenance['stored_tensor_elements'] = sum(x.numel() for x in result.values())
        provenance['router_parameters'] = sum(x.numel() for n,x in result.items() if '.mhc_' in n)
        save_file(result, OUT/'model.safetensors',metadata={
            'format':'pt','training':'none','origin':'Qwen3.5-0.8B original',
            'method':'SenseNova topology port plus analytic residual depth scaling'})
    (OUT/'config.json').write_text(json.dumps(config,indent=2))
    (OUT/'surgery_manifest.json').write_text(json.dumps(provenance,indent=2))
    for name in ['tokenizer.json','tokenizer_config.json','chat_template.jinja','LICENSE']:
        shutil.copy2(ROOT/'upstream'/name,OUT/name)
    for name in ['preprocessor_config.json','video_preprocessor_config.json']:
        shutil.copy2(ROOT/'upstream'/name,OUT/name)
    shutil.copy2(ROOT/'modeling_sensenova_loop.py',OUT/'modeling_sensenova_loop.py')
    print('COMPLETE',provenance['stored_tensor_elements'],'tensor elements',
          (OUT/'model.safetensors').stat().st_size,'bytes',flush=True)


if __name__ == '__main__':
    main()
