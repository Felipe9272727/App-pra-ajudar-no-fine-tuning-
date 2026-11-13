"""Immutable canonical GENERAL target, never a rejected loop025epoch."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'supervised015'))
import train_runtime as tr

def load_target():
 m,t,p,meta=tr.load();del p;tr.torch.set_num_threads(4);m.eval();m.requires_grad_(False);return m,t,meta
