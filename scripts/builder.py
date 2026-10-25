#!/usr/bin/env python3
"""Pinned Telegram Desktop builder; production build is an explicit opt-in."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def git(source, *args):
    return subprocess.check_output(['git', '-C', str(source), *args], text=True, stderr=subprocess.DEVNULL).strip()


def pin(root=ROOT):
    value = json.loads((root / 'PINNED_UPSTREAM').read_text())
    if not re.fullmatch(r'[0-9a-f]{40}', value['commit']):
        raise ValueError('Invalid pinned upstream commit')
    if not value['repository'].startswith('https://github.com/') or not value['tag'].startswith('v'):
        raise ValueError('Invalid pinned upstream repository/tag')
    return value


def verify_source(source, expected, submodules=True):
    source = Path(source).resolve()
    if git(source, 'rev-parse', 'HEAD') != expected:
        raise ValueError('Source HEAD does not equal pinned commit; checkout was not changed')
    if git(source, 'status', '--porcelain', '--untracked-files=normal'):
        raise ValueError('Source checkout is dirty; refusing to modify or build it')
    if submodules:
        status = git(source, 'submodule', 'status', '--recursive')
        if any(line.startswith(('-', '+', 'U')) for line in status.splitlines()):
            raise ValueError('Submodules are missing or differ from pinned gitlinks')
    return expected


def prepare(source, repository, tag, expected, submodules=True):
    source = Path(source).resolve()
    if source.exists():
        verify_source(source, expected, submodules=False)
    else:
        source.mkdir(parents=True)
        subprocess.run(['git', 'init', '-q', str(source)], check=True)
        subprocess.run(['git', '-C', str(source), 'remote', 'add', 'upstream', repository], check=True)
        subprocess.run(['git', '-C', str(source), 'fetch', '--depth=1', '--no-tags', 'upstream', 'refs/tags/' + tag], check=True)
        if git(source, 'rev-parse', 'FETCH_HEAD^{commit}') != expected:
            raise ValueError('Fetched tag does not resolve to pinned commit; refusing checkout')
        subprocess.run(['git', '-C', str(source), 'checkout', '-q', '--detach', expected], check=True)
    if submodules:
        subprocess.run(['git', '-C', str(source), 'submodule', 'update', '--init', '--recursive'], check=True)
    return verify_source(source, expected, submodules)


def overlay(root):
    series = [line.strip() for line in (root / 'patches/series').read_text().splitlines()
              if line.strip() and not line.lstrip().startswith('#')]
    payloads = json.loads((root / 'payloads/manifest.json').read_text())
    if series or payloads != []:
        raise ValueError('This D0 foundation supports zero product changes only; implement and audit D1 materialization first')
    return []


def materialize(source, expected, root=ROOT, submodules=True):
    verify_source(source, expected, submodules)
    changes = overlay(root)
    verify_source(source, expected, submodules)
    return changes


def credentials(env):
    api_id = env.get('TDESKTOP_API_ID', '')
    api_hash = env.get('TDESKTOP_API_HASH', '')
    if not re.fullmatch(r'[1-9][0-9]*', api_id) or not re.fullmatch(r'[0-9a-fA-F]{32}', api_hash):
        raise ValueError('Valid TDESKTOP_API_ID and TDESKTOP_API_HASH are required; values omitted')
    return (api_id, api_hash)


def redact(line, secrets):
    for secret in sorted(secrets, key=len, reverse=True):
        if secret:
            line = line.replace(secret, '[REDACTED]')
    return line


def build_release(source, expected, image, jobs):
    materialize(source, expected)
    secrets = credentials(os.environ)
    if jobs < 1:
        raise ValueError('Build jobs must be positive')
    command = '''set -e
cd /usr/src/tdesktop/Telegram
./configure.sh -D TDESKTOP_API_TEST=OFF -D "TDESKTOP_API_ID=$TDESKTOP_API_ID" -D "TDESKTOP_API_HASH=$TDESKTOP_API_HASH" -D "CMAKE_EXE_LINKER_FLAGS_RELEASE=-flto=1 --param=lto-max-streaming-parallelism=1"
cmake --build ../out --config Release --target Telegram
'''
    args = ['docker', 'run', '--rm', '-i', '-u', str(os.getuid()),
            '-v', str(Path(source).resolve()) + ':/usr/src/tdesktop',
            '-e', 'TDESKTOP_API_ID', '-e', 'TDESKTOP_API_HASH',
            '-e', 'CMAKE_BUILD_PARALLEL_LEVEL=' + str(jobs), image, 'bash', '-c', command]
    with subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True) as child:
        for line in child.stdout:
            print(redact(line, secrets), end='', flush=True)
        if child.wait():
            raise ValueError('Release build failed; no success or runtime claim is made')
    return Path(source).resolve() / 'out/Release/Telegram'


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(data)
    return digest.hexdigest()


def package(binary, output, source, expected, version, root=ROOT):
    verify_source(source, expected)
    overlay(root)
    source, binary, output = Path(source).resolve(), Path(binary).resolve(), Path(output).resolve()
    if output == source or source in output.parents:
        raise ValueError('Artifacts must be outside the source/build tree')
    if output.exists():
        raise ValueError('Artifact destination already exists; refusing overwrite')
    with binary.open('rb') as stream:
        header = stream.read(20)
    if header[:6] != b'\x7fELF\x02\x01' or header[18:20] != b'\x3e\x00':
        raise ValueError('Package input must be a little-endian ELF64 x86-64 executable')
    if not re.fullmatch(r'[0-9A-Za-z.-]+', version):
        raise ValueError('Invalid version')
    epoch = int(git(source, 'show', '-s', '--format=%ct', 'HEAD'))
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent, prefix='.package-') as temp:
        stage = Path(temp)
        stripped = stage / 'Telegram'
        shutil.copy2(binary, stripped)
        subprocess.run(['strip', '--strip-all', str(stripped)], check=True)
        name = 'stock-telegram-desktop-' + version + '-linux-x86_64.tar.xz'
        archive = stage / name
        with tarfile.open(archive, 'w:xz') as tf:
            info = tarfile.TarInfo('Telegram')
            info.size = stripped.stat().st_size
            info.mode, info.mtime = 0o755, epoch
            with stripped.open('rb') as stream:
                tf.addfile(info, stream)
        try:
            builder_commit = git(root, 'rev-parse', 'HEAD')
            builder_dirty = bool(git(root, 'status', '--porcelain'))
        except subprocess.CalledProcessError:
            builder_commit, builder_dirty = None, True
        manifest = {'schema': 1, 'upstream_commit': expected, 'upstream': pin(root),
                    'builder_commit': builder_commit, 'builder_dirty': builder_dirty,
                    'version': version, 'product_changes': [], 'source_date_epoch': epoch,
                    'build_evidence': 'not asserted by packaging', 'runtime_evidence': 'not asserted by packaging',
                    'binary': {'original_sha256': sha256(binary), 'stripped_sha256': sha256(stripped),
                               'original_bytes': binary.stat().st_size, 'stripped_bytes': stripped.stat().st_size},
                    'artifact': {'name': name, 'bytes': archive.stat().st_size, 'sha256': sha256(archive)}}
        output.mkdir()
        shutil.copy2(archive, output / name)
        (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        (output / 'SHA256SUMS').write_text(manifest['artifact']['sha256'] + '  ' + name + '\n')
    return output / 'manifest.json'


def validate():
    required = ['PINNED_UPSTREAM', 'JERKGRAM_VERSION', 'README.md', '.gitignore',
                '.github/workflows/linux-preflight.yml', 'scripts/builder.py',
                'scripts/preflight.py', 'tests/test_builder.py', 'docs/storage.md',
                'patches/series', 'payloads/manifest.json']
    missing = [p for p in required if not (ROOT / p).is_file()]
    if missing:
        raise ValueError('Missing builder files: ' + ', '.join(missing))
    pin()
    overlay(ROOT)
    print('Builder structure and zero-change overlay are valid')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    sub.add_parser('validate')
    for action in ('prepare', 'verify-source', 'materialize', 'build-release', 'package'):
        p = sub.add_parser(action)
        p.add_argument('--source', required=True, type=Path)
        if action in ('prepare', 'verify-source', 'materialize'):
            p.add_argument('--skip-submodules', action='store_true', help='Fetch-only preflight, never build-ready proof')
        if action == 'build-release':
            p.add_argument('--image', default='tdesktop:centos_env')
            p.add_argument('--jobs', type=int, default=2)
            p.add_argument('--execute', action='store_true', help='Explicit opt-in to expensive build/reconfigure')
        if action == 'package':
            p.add_argument('--binary', required=True, type=Path)
            p.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    value = pin()
    if args.action == 'validate':
        validate()
    elif args.action == 'prepare':
        prepare(args.source, value['repository'], value['tag'], value['commit'], not args.skip_submodules)
        print('Pinned checkout verified; submodules checked:', not args.skip_submodules)
    elif args.action == 'verify-source':
        verify_source(args.source, value['commit'], not args.skip_submodules)
        print('Source identity and cleanliness verified; submodules checked:', not args.skip_submodules)
    elif args.action == 'materialize':
        print(json.dumps({'product_changes': materialize(args.source, value['commit'], submodules=not args.skip_submodules)}))
    elif args.action == 'build-release':
        if not args.execute:
            raise ValueError('Refusing expensive build without --execute; do not target the D0 tree with new credentials')
        print('Release binary:', build_release(args.source, value['commit'], args.image, args.jobs))
    elif args.action == 'package':
        print(package(args.binary, args.output, args.source, value['commit'], (ROOT / 'JERKGRAM_VERSION').read_text().strip()))

if __name__ == '__main__':
    try:
        main()
    except (ValueError, subprocess.CalledProcessError, OSError) as exc:
        print('Builder failed: ' + str(exc), file=sys.stderr)
        sys.exit(1)
