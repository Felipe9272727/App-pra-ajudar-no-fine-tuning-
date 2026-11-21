"""Run the same artifact bootstrap locally, optionally reusing a release ZIP."""
import argparse
from pathlib import Path
from space.bootstrap import prepare

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('archive', nargs='?', type=Path)
    args = parser.parse_args()
    print(prepare(args.output, args.archive))
