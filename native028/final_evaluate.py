"""Sealed final opens once only for a frozen eligible winner."""
import argparse
from inference import *
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('variant');a=ap.parse_args()
    selection=read('selection.json');assert selection['final_gate_open'] and selection['selected']
    assert a.variant in ['original','parent',selection['selected']]
    run_variant(a.variant,split='final')
