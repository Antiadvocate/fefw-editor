"""Reproduce historical Test 5, including its failed Chapter 1 candidate.

Chapter 1 is not an editor target. This script is retained for research only.
"""
from pathlib import Path
import argparse
import json
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from research.story_remaining_probes import build as build_cases
import story_start


def historical_edit(f, chapter):
    if chapter == 1:
        return story_start._edited_at_entry(f, 1, 1444, (12, 1, 12, 0))
    return story_start.edited(f, chapter)


def build(source, output):
    return build_cases(source, output, chapters=(1, 2, 3), prefix='ST5', edit=historical_edit)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.source, args.output), indent=2))
