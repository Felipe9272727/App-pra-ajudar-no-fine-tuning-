"""Atomic tensor checkpoints, including on a clean checkout with no directories."""
from pathlib import Path
import os

def tensor_checkpoint(payload,path):
    import torch
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+'.tmp')
    torch.save(payload,temporary)
    os.replace(temporary,path)
