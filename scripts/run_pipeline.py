"""One-command observed-data ETL, prediction benchmark, and synthetic benchmark."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--download', action='store_true', help='Fetch missing pinned HeartSteps sources')
    parser.add_argument('--quick', action='store_true', help='Run a small synthetic smoke benchmark instead of the full benchmark')
    args = parser.parse_args()
    commands = [
        ['health_friend.data_pipeline.cli'] + (['--download'] if args.download else []),
        ['health_friend.data_pipeline.train_baseline'],
        ['health_friend.data_pipeline.train_classifier'],
        ['health_friend.simulation.benchmark'] + (['--quick'] if args.quick else []),
    ]
    for command in commands:
        print('Running:', ' '.join(command), flush=True)
        subprocess.run([sys.executable, '-m', *command], cwd=ROOT, check=True)
    reports = ROOT / 'reports/generated'
    paths = [reports / name for name in ('data_quality.json', 'heartsteps_model.json', 'heartsteps_classifier.json', 'simulation_benchmark.json')]
    manifest = {'pipeline': 'my-health-friend-v2', 'mode': 'quick' if args.quick else 'full',
                'report_hashes': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
                'sources_separated': True, 'clinical_validation': False}
    (reports / 'pipeline_run.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print('Pipeline complete. Reports: reports/generated')


if __name__ == '__main__':
    main()
