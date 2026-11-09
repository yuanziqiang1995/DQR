#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
python - <<'PY'
import ast
import gzip
import hashlib
import json
import re
from pathlib import Path

root = Path.cwd()
files = sorted(path for path in root.rglob('*') if path.is_file() and '.git' not in path.parts)
relative = {path.relative_to(root).as_posix() for path in files}

expected_data = {
    'data/scorer/distillation_data.jsonl.gz',
    *{f'data/finqa_convfinqa/{name}.json.gz' for name in (
        'unselected', 'ds2', 'dqr_sft_rl', 'dqr_sft', 'gemini', 'qwen3_8b', 'deepseek')},
    *{f'data/multihiertt/{name}.json.gz' for name in (
        'unselected', 'ds2', 'dqr_sft_rl', 'dqr_sft', 'gemini', 'qwen3_8b', 'deepseek')},
    'data/test/finqa.json.gz',
    'data/test/convfinqa.json.gz',
    'data/test/multihiertt.json.gz',
    'data/test/gsm8k.jsonl.gz',
}
assert expected_data <= relative, f'Missing data: {sorted(expected_data - relative)}'

for path in root.rglob('*.py'):
    ast.parse(path.read_text(encoding='utf-8'), filename=str(path))

for path in root.rglob('*.gz'):
    with gzip.open(path, 'rb') as f:
        while f.read(8 * 1024 * 1024):
            pass

for name, expected_count in (('finqa', 1147), ('convfinqa', 1490), ('multihiertt', 1044)):
    with gzip.open(root / 'data/test' / f'{name}.json.gz', 'rt', encoding='utf-8') as f:
        assert len(json.load(f)) == expected_count
with gzip.open(root / 'data/test/gsm8k.jsonl.gz', 'rt', encoding='utf-8') as f:
    rows = [json.loads(line) for line in f if line.strip()]
    assert len(rows) == 1319 and all('####' in row['answer'] for row in rows)

secret_pattern = re.compile(r'sk-[A-Za-z0-9]{16,}')
for path in files:
    assert not path.is_symlink(), f'Symlink is not allowed: {path}'
    assert path.stat().st_size < 100 * 1024 * 1024, f'File exceeds GitHub limit: {path}'
    lowered = path.relative_to(root).as_posix().lower()
    assert not any(term in lowered for term in (
        'finqa_test_unified', 'build_unified', 'eval_unified', 'qwen25_finqa_ablation',
        '__pycache__', '.ipynb_checkpoints', 'tf-logs', 'checkpoint-')), f'Excluded content: {path}'
    if path.suffix in {'.py', '.sh', '.yaml', '.yml', '.md', '.txt', '.csv', '.tsv'}:
        text = path.read_text(encoding='utf-8')
        assert not secret_pattern.search(text), f'Possible API key: {path}'
        assert ('/' + 'root/') not in text and ('/' + 'autodl-fs/') not in text, f'Local absolute path: {path}'

checksums = root / 'SHA256SUMS'
assert checksums.is_file(), 'SHA256SUMS is missing'
expected_checksums = {}
for line in checksums.read_text().splitlines():
    digest, name = line.split('  ', 1)
    expected_checksums[name] = digest
actual_names = {path.relative_to(root).as_posix() for path in files if path != checksums}
assert set(expected_checksums) == actual_names, 'SHA256SUMS does not match package file list'
for name, expected in expected_checksums.items():
    digest = hashlib.sha256()
    with (root / name).open('rb') as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b''):
            digest.update(chunk)
    assert digest.hexdigest() == expected, f'Checksum mismatch: {name}'

print(f'Package OK: {len(files)} files, {len(expected_data)} data files, all checksums verified.')
print('Python syntax, gzip integrity, test-set counts, secret scan and GitHub size limits passed.')
PY
