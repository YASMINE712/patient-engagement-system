"""Fetch a pinned public snapshot and verify bytes before use."""
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def acquire_heartsteps(root, download=False):
    root = Path(root)
    manifest = json.loads((root / 'data/sources/heartsteps-v1.json').read_text(encoding='utf-8'))
    destination = root / 'data/raw/heartsteps-v1'
    destination.mkdir(parents=True, exist_ok=True)
    for record in manifest['files']:
        name = record['filename']
        if Path(name).name != name:
            raise ValueError('Source filenames must not contain directories')
        path = destination / name
        if not path.exists():
            if not download:
                raise FileNotFoundError(f'{path} is missing. Run with --download.')
            expected_prefix = f"https://raw.githubusercontent.com/klasnja/HeartStepsV1/{manifest['commit']}/"
            if not record['url'].startswith(expected_prefix):
                raise ValueError('Source URL does not match the pinned repository revision')
            request = Request(record['url'], headers={'User-Agent': 'MyHealthFriend-ETL/1.0'})
            with urlopen(request, timeout=60) as response:
                body = response.read()
            if hashlib.sha256(body).hexdigest() != record['sha256']:
                raise ValueError(f'Download checksum mismatch: {name}')
            temporary = path.with_suffix(path.suffix + '.part')
            temporary.write_bytes(body)
            temporary.replace(path)
        if sha256(path) != record['sha256']:
            raise ValueError(f'Raw source was modified: {name}. Restore the pinned source before processing.')
    return destination, manifest
