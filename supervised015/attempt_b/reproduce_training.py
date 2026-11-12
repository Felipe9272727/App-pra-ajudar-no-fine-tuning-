"""Explicit optional replay in a NEW directory; never overwrite saved experiments."""
import argparse,importlib.util,sys,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',type=Path,required=True)
    args=p.parse_args();output=args.output_dir.resolve()
    if output.exists():raise SystemExit('Refusing existing output directory; saved experiments are immutable')
    output.mkdir(parents=True);(output/'checkpoints').mkdir();(output/'logs').mkdir()
    for name in ['config.json','train.json','frozen.json','PROTOCOL.md']:shutil.copy2(HERE/name,output/name)
    sys.path.insert(0,str(HERE.parent))
    spec=importlib.util.spec_from_file_location('study015_b_replay',HERE/'train.py');trainer=importlib.util.module_from_spec(spec);spec.loader.exec_module(trainer)
    trainer.HERE=output;trainer.train_runtime.HERE=output
    trainer.main()
if __name__=='__main__':main()
