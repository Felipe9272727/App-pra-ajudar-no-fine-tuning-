"""Once-only core validation for one named native variant."""
import argparse
from inference import *
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('variant',nargs='?',choices=['original','parent','sft_final','policy_final']);ap.add_argument('--select',action='store_true');a=ap.parse_args()
    if a.select:
        from decide import main
        main()
    else:
        assert a.variant
        run_variant(a.variant)
