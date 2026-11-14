"""Identical native inference for all four frozen epoch snapshots."""
import argparse
from inference import *
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('variant',nargs='?',choices=['original','parent','epoch01','epoch02','epoch03','epoch04']);p.add_argument('--split',default='validation',choices=['validation','legacy','final']);p.add_argument('--select',action='store_true');a=p.parse_args()
    if a.select:
        from decide import main
        main()
    else:
        assert a.variant
        if a.split=='legacy':assert a.variant!='original'
        if a.split=='final':
            s=read('selection.json');assert s['final_gate_open'] and a.variant in ['original','parent',s['selected']]
        run_variant(a.variant,split=a.split)
