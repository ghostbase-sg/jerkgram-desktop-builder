#!/usr/bin/env python3
"""Fail-closed, hash-pinned overlay: pristine input or exact verified output."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tempfile


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git(source, *args):
    return subprocess.check_output(['git', '-C', str(source), *args], text=True).strip()


def safe(root, name):
    parts = PurePosixPath(name)
    if parts.is_absolute() or not parts.parts or any(p in ('.', '..', '.git') for p in parts.parts):
        raise ValueError('Unsafe overlay path')
    result = Path(root).joinpath(*parts.parts)
    if any(p.is_symlink() for p in (result, *result.parents) if p != Path(root).parent):
        raise ValueError('Symlink in overlay path')
    if not result.resolve().is_relative_to(Path(root).resolve()):
        raise ValueError('Overlay path escapes root')
    return result


def load(root, expected):
    config = json.loads((root / 'D1_CONFIG.json').read_text())
    if config.get('schema') != 1 or config.get('upstream_commit') != expected:
        raise ValueError('Overlay schema or pinned source mismatch')
    if 'version' in config:
        from generate_identity_header import render
        if (root / 'JERKGRAM_VERSION').read_text().strip() != config['version']:
            raise ValueError('Presentation version mismatch')
        header = root / 'payloads/linux-identity/jerkgram_identity.h'
        if header.read_text() != render(config['version'], expected):
            raise ValueError('Generated identity header is stale')
    names = [line for line in (root / 'patches/series').read_text().splitlines()
             if line and not line.startswith('#')]
    if names != [str(PurePosixPath(x['path']).relative_to('patches')) for x in config['patches']]:
        raise ValueError('Patch order does not equal manifest')
    for item in config['patches'] + config['payloads']:
        path = safe(root, item['path'])
        if not path.is_file() or sha(path) != item['sha256']:
            raise ValueError('Overlay input hash mismatch: ' + item['path'])
    for name in config['files']:
        safe(root, name)
    for item in config['payloads']:
        if item['target'] not in config['files']:
            raise ValueError('Payload target not in final inventory')
    return config


def state_path(source):
    p = Path(git(source, 'rev-parse', '--git-path', 'jerkgram-overlay.json'))
    return p if p.is_absolute() else source / p


def verify(source, expected, root, submodules=True):
    source, root = Path(source).resolve(), Path(root).resolve()
    config = load(root, expected)
    if git(source, 'rev-parse', 'HEAD') != expected:
        raise ValueError('Source HEAD does not equal pinned commit')
    if submodules:
        status = subprocess.check_output(['git', '-C', str(source), 'submodule', 'status', '--recursive'], text=True)
        if any(line.startswith(('-', '+', 'U')) for line in status.splitlines()):
            raise ValueError('Submodules do not equal pinned gitlinks')
        subprocess.run(['git', '-C', str(source), 'submodule', 'foreach', '--quiet', '--recursive',
                        'test -z "$(git status --porcelain)" && test -z "$(git ls-files --others --ignored --exclude-standard)"'], check=True, capture_output=True)
    if (source / 'out').is_symlink():
        raise ValueError('Build output must not be a symlink')
    ignored = git(source, 'ls-files', '--others', '--ignored', '--exclude-standard').splitlines()
    if any(not name.startswith('out/') for name in ignored):
        raise ValueError('Unexpected ignored source input outside build output')
    marker = state_path(source)
    if not marker.exists():
        if git(source, 'status', '--porcelain', '--untracked-files=all'):
            raise ValueError('Pristine input has unexpected changes')
        return 'pristine'
    state = json.loads(marker.read_text())
    if state != {'schema': 1, 'config_sha256': sha(root / 'D1_CONFIG.json'), 'upstream_commit': expected}:
        raise ValueError('Materialized state does not match this overlay')
    changed = set(git(source, 'diff', '--name-only', 'HEAD').splitlines())
    untracked = set(git(source, 'ls-files', '--others', '--exclude-standard').splitlines())
    wanted_changed = {p for p, f in config['files'].items() if f['before'] is not None}
    wanted_new = set(config['files']) - wanted_changed
    if changed != wanted_changed or untracked != wanted_new or git(source, 'diff', '--cached', '--name-only'):
        raise ValueError('Materialized file inventory mismatch')
    for name, hashes in config['files'].items():
        p = safe(source, name)
        if not p.is_file() or sha(p) != hashes['after']:
            raise ValueError('Materialized postimage mismatch: ' + name)
        if p.stat().st_mode & 0o111:
            raise ValueError('Unexpected executable overlay file: ' + name)
    return 'materialized'


def materialize(source, expected, root, submodules=True):
    source, root = Path(source).resolve(), Path(root).resolve()
    config = load(root, expected)
    status = verify(source, expected, root, submodules)
    if status == 'materialized':
        return sorted(config['files'])
    if (source / 'out').exists():
        raise ValueError('Refusing initial overlay on a checkout with existing out')
    # All preimages and every patch/payload are checked in scratch before any source write.
    with tempfile.TemporaryDirectory(prefix='jerkgram-overlay-') as tmp:
        stage = Path(tmp)
        for name, hashes in config['files'].items():
            src = safe(source, name)
            dst = safe(stage, name)
            if hashes['before'] is None:
                if src.exists():
                    raise ValueError('New overlay destination already exists')
            elif not src.is_file() or sha(src) != hashes['before']:
                raise ValueError('Preimage mismatch: ' + name)
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, dst)
        for item in config['patches']:
            patch = safe(root, item['path'])
            subprocess.run(['git', 'apply', '--check', str(patch)], cwd=stage, check=True, capture_output=True)
            subprocess.run(['git', 'apply', str(patch)], cwd=stage, check=True, capture_output=True)
        for item in config['payloads']:
            dst = safe(stage, item['target'])
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(safe(root, item['path']), dst)
        actual = {str(p.relative_to(stage)) for p in stage.rglob('*') if p.is_file()}
        if actual != set(config['files']):
            raise ValueError('Patch output file inventory mismatch')
        for name, hashes in config['files'].items():
            if sha(safe(stage, name)) != hashes['after']:
                raise ValueError('Expected postimage mismatch: ' + name)
        for name in config['files']:
            dst = safe(source, name)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(safe(stage, name), dst)
            dst.chmod(0o644)
    marker = state_path(source)
    marker.write_text(json.dumps({'schema': 1, 'config_sha256': sha(root / 'D1_CONFIG.json'),
                                  'upstream_commit': expected}, sort_keys=True) + '\n')
    verify(source, expected, root, submodules)
    return sorted(config['files'])
