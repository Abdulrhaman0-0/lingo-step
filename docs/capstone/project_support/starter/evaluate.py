"""Compute accuracy from manually verified labelled trials in eval_trials.csv.
Don't use training samples as evaluation data. Uncertain outputs count as failures.
"""
import csv
from pathlib import Path
p = Path(__file__).parent / 'eval_trials.csv'
if not p.exists():
    print('Create eval_trials.csv using the provided example.'); raise SystemExit(1)
rows = list(csv.DictReader(p.open(encoding='utf-8', newline='')))
for mode in sorted(set(r['mode'] for r in rows)):
    trials = [r for r in rows if r['mode'] == mode]
    correct = sum(r['expected'].strip().upper() == r['predicted'].strip().upper() for r in trials)
    print(f'{mode}: accuracy {correct}/{len(trials)} = {100*correct/len(trials):.1f}%')
