"""Run the frozen study015 evaluator against attempt B, no prompt changes."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import train_runtime
import evaluate as evaluator
location=Path(__file__).resolve().parent
train_runtime.HERE=location
evaluator.HERE=location
if __name__=='__main__':evaluator.main()
