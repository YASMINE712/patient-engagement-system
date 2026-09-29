"""Run with python -m health_friend.data_pipeline.cli [--download]."""
import argparse
import json
from pathlib import Path
import pandas as pd
from .sources import acquire_heartsteps, sha256
from .transform import clean_heartsteps, clean_legacy, HEARTSTEPS_FEATURES, KEYS, PIPELINE_VERSION


def run(root, download=False, seed=2026):
    root = Path(root)
    raw, manifest = acquire_heartsteps(root, download)
    users = pd.read_csv(raw / 'users.csv', low_memory=False)
    suggestions = pd.read_csv(raw / 'suggestions.csv', low_memory=False)
    decisions, quality = clean_heartsteps(users, suggestions, seed)
    # Validate every requested source before writing processed outputs.
    legacy_path = root / 'data/raw/legacy_wellness.csv'
    legacy, legacy_quality = None, None
    if legacy_path.exists():
        raw_legacy = pd.read_csv(legacy_path, keep_default_na=False)
        if 'source' in raw_legacy and raw_legacy['source'].eq('synthetic_software_test_fixture').all():
            legacy_quality = {'status': 'skipped', 'reason': 'Software-test fixture is not the legacy dataset.'}
        else:
            legacy, legacy_quality = clean_legacy(raw_legacy)
    processed = root / 'data/processed'
    real_dir = processed / 'heartsteps-v1'
    real_dir.mkdir(parents=True, exist_ok=True)
    decisions.to_csv(real_dir / 'decisions.csv', index=False, lineterminator='\n')
    eligible = decisions.loc[decisions['eligible_decision']]
    eligible[KEYS + ['split'] + HEARTSTEPS_FEATURES].to_csv(real_dir / 'features.csv', index=False, lineterminator='\n')
    eligible[KEYS + ['split', 'action', 'steps_next_30m', 'outcome_observed', 'usefulness_rating']].to_csv(real_dir / 'labels.csv', index=False, lineterminator='\n')
    decisions[['participant_id', 'split']].drop_duplicates().sort_values('participant_id').to_csv(real_dir / 'participant_splits.csv', index=False, lineterminator='\n')
    output_paths = list(real_dir.glob('*.csv'))
    if legacy is not None:
        legacy_dir = processed / 'legacy'
        legacy_dir.mkdir(parents=True, exist_ok=True)
        legacy.to_csv(legacy_dir / 'wellness.csv', index=False, lineterminator='\n')
        output_paths.append(legacy_dir / 'wellness.csv')
    report = {'pipeline_version': PIPELINE_VERSION, 'split_seed': seed, 'source_commit': manifest['commit'],
              'heartsteps': quality, 'legacy': legacy_quality,
              'outputs_sha256': {str(path.relative_to(root)).replace('\\', '/'): sha256(path) for path in sorted(output_paths)}}
    folder = root / 'reports/generated'
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'data_quality.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    lines = ['# Data-quality report', '', f'Pipeline version: {PIPELINE_VERSION}',
             f"Pinned source commit: `{manifest['commit']}`", '',
             'Source: [HeartSteps V1](https://github.com/klasnja/HeartStepsV1), CC-BY-4.0.', '',
             '## Observed HeartSteps data', '', '| Check | Result |', '|---|---|']
    for key, value in quality.items():
        if not isinstance(value, (dict, list)):
            lines.append(f'| {key.replace("_", " ")} | {value} |')
    lines += ['', '## Participant splits', '', 'Each participant belongs to exactly one split.', '']
    lines += [f'- {split}: {count} participants; {quality["split_rows"][split]} decision records.'
              for split, count in quality['split_participants'].items()]
    lines += ['', '## Interpretation limits', ''] + [f'- {warning}' for warning in quality['warnings']]
    lines += ['', 'No model was trained by this ETL command. These are data checks, not evidence of recommendation effectiveness.']
    if legacy_quality:
        lines += ['', '## Legacy dataset', '', '```json', json.dumps(legacy_quality, indent=2), '```']
    (folder / 'DATA_QUALITY.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--download', action='store_true', help='Download missing pinned HeartSteps files')
    parser.add_argument('--seed', type=int, default=2026)
    args = parser.parse_args()
    report = run(args.root, args.download, args.seed)
    print(json.dumps({'heartsteps': report['heartsteps'], 'report': 'reports/generated/DATA_QUALITY.md'}, indent=2))


if __name__ == '__main__':
    main()
