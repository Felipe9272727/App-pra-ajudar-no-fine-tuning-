"""Exercise the actual multi-visit implementation/cache on a tiny random model.

This is a technical correctness test, never a capability score or trained model.
"""
from runtime import *
from modeling_sensenova_loop import SenseNovaLoopConfig,SenseNovaLoopForConditionalGeneration
from native_runtime import NativeTextModel,VisitGatedMHC

@torch.inference_mode()
def main():
    from checkpoint_io import tensor_checkpoint
    import tempfile
    with tempfile.TemporaryDirectory() as folder:
        # Git does not preserve empty folders: exercise an absent nested parent.
        target=Path(folder)/'fresh-checkout/checkpoints/probe.pt'
        tensor_checkpoint({'weight':torch.arange(4)},target)
        assert torch.equal(torch.load(target,weights_only=True)['weight'],torch.arange(4))
        tensor_checkpoint({'weight':torch.arange(2)},target)
        assert torch.equal(torch.load(target,weights_only=True)['weight'],torch.arange(2))
        assert not target.with_name(target.name+'.tmp').exists()
        print('COLD_CHECKOUT_CHECKPOINT_OK',flush=True)
    raw=json.loads((ROOT/'sensenova_port/config.json').read_text())
    raw['text_config'].update(hidden_size=32,intermediate_size=64,num_attention_heads=4,
        num_key_value_heads=2,head_dim=8,vocab_size=128,eos_token_id=1,pad_token_id=1,
        linear_conv_kernel_dim=7,linear_key_head_dim=8,linear_value_head_dim=8,
        linear_num_key_heads=2,linear_num_value_heads=4,partial_rotary_factor=1.0,
        rope_parameters={'rope_type':'default','rope_theta':10000.,'mrope_section':[1,1,2],
                         'mrope_interleaved':True,'partial_rotary_factor':1.0})
    raw['vision_config'].update(depth=1,hidden_size=32,intermediate_size=64,num_heads=4,
        out_hidden_size=32,num_position_embeddings=16,patch_size=2,spatial_merge_size=2,temporal_patch_size=1)
    raw.update(eos_token_id=1,pad_token_id=1)
    torch.manual_seed(804)
    cfg=SenseNovaLoopConfig.from_dict(raw);cfg._attn_implementation='eager'
    model=SenseNovaLoopForConditionalGeneration(cfg).float().eval().requires_grad_(False)
    text=model.model.language_model;text.__class__=NativeTextModel
    for i,layer in enumerate(text.layers[4:28],4):
        layer.__class__=VisitGatedMHC
        layer._native_window=256 if i in [7,15,27] else 0
    ids=torch.tensor([[4,5,6,7]])
    for passes in [2,3,4]:
        arch=configure_loops(model,passes)
        full=model(input_ids=ids,use_cache=False,logits_to_keep=1).logits[:,-1]
        pre=model(input_ids=ids[:,:-1],use_cache=True,logits_to_keep=1)
        step=model(input_ids=ids[:,-1:],past_key_values=pre.past_key_values,use_cache=True,logits_to_keep=1).logits[:,-1]
        delta=float((full-step).abs().max())
        assert torch.isfinite(full).all() and delta<1e-3,(passes,delta)
        assert pre.past_key_values._loop_execution_plan==text._loop_plan
        assert len(pre.past_key_values.layers)==8+24*passes
        print('MULTILOOP_CACHE_OK',passes,arch['layer_executions'],delta,flush=True)

if __name__=='__main__':main()
