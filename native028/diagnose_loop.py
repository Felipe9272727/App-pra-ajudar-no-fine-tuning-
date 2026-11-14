"""Replace second block exit with first, retaining all physical computations."""
import argparse
from inference import *
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('variant');a=ap.parse_args()
    s=read('selection.json');assert a.variant in ['parent',s['selected'] or 'policy_final']
    run_variant(a.variant,split='diagnostic',bypass=True,diagnostic_only=True)
