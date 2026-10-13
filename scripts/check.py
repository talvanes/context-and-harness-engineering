#!/usr/bin/env python3
"""Validate repository essentials and run synthetic regression fixtures."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def validate():
    for name in ('SKILL.md', 'README.md', 'LICENSE', '.gitignore'):
        path = ROOT / name
        if not path.is_file() or not path.read_text(encoding='utf-8').strip():
            raise ValueError(f'Missing or empty required file: {name}')
    text = (ROOT / 'SKILL.md').read_text(encoding='utf-8')
    lines = text.splitlines()
    if not lines or lines[0] != '---':
        raise ValueError('Skill must start with YAML frontmatter')
    end = lines.index('---', 1)
    fields = dict(line.split(':', 1) for line in lines[1:end] if ':' in line)
    if fields.get('name', '').strip() != 'context-and-harness-engineering':
        raise ValueError('Unexpected skill name')
    if not fields.get('description', '').strip():
        raise ValueError('Missing skill description')
    if len(lines) >= 500 or '[TODO' in text:
        raise ValueError('Skill is too long or contains an unfinished template')
    for heading in ('## Operating principle', '## Continuous execution loop',
                    '### 5. Recover without losing alignment'):
        if heading not in text:
            raise ValueError(f'Missing expected section: {heading}')
    print('Repository and lightweight skill structure checks passed.', flush=True)


def main():
    validate()
    commands = [
        ['tests/stress/stress_test.py'],
        ['tests/stress/recovery_regression.py'],
        ['-m', 'unittest', 'discover', '-s', 'tests/coding', '-p', 'test*.py', '-v'],
    ]
    for args in commands:
        subprocess.run([sys.executable, *args], cwd=ROOT, check=True)
    print('All three fixture suites passed. This is not proof of universal agent behavior.')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, subprocess.CalledProcessError) as error:
        print(f'Validation failed: {error}', file=sys.stderr)
        sys.exit(1)
