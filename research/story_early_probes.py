"""Prepare independent Chapter 1–3 candidates from the accepted B0-01 baseline."""
from pathlib import Path
import argparse
import json
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from research.story_remaining_probes import build as build_cases


def build(source, output):
    return build_cases(source, output, chapters=(1, 2, 3), prefix='ST5')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.source, args.output), indent=2))
