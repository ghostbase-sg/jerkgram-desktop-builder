#!/usr/bin/env python3
"""Report resources and secret presence without disclosing environment values."""
import argparse
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
from builder import ROOT, pin, validate


def report(output):
    validate()
    memory = {}
    if Path('/proc/meminfo').exists():
        memory = {line.split(':')[0]: int(line.split()[1]) * 1024
                  for line in Path('/proc/meminfo').read_text().splitlines()
                  if line.split(':')[0] in ('MemTotal', 'MemAvailable', 'SwapTotal', 'SwapFree')}
    disk = shutil.disk_usage(ROOT)
    tools = {}
    for name in ('git', 'python3', 'docker', 'cmake', 'ninja', 'poetry', 'strip', 'tar', 'xz', 'gh'):
        if shutil.which(name):
            result = subprocess.run([name, '--version'], text=True, capture_output=True, timeout=20)
            lines = (result.stdout or result.stderr).splitlines()
            tools[name] = lines[0] if lines else 'installed; no version output'
        else:
            tools[name] = None
    value = {'os': platform.platform(), 'os_release': platform.freedesktop_os_release(), 'machine': platform.machine(), 'cpu_count': os.cpu_count(),
             'memory_bytes': memory, 'disk_bytes': {'total': disk.total, 'free': disk.free},
             'tools': tools, 'pinned_upstream': pin(), 'builder_structure_valid': True,
             'secret_presence': {name: bool(os.environ.get(name)) for name in ('TDESKTOP_API_ID', 'TDESKTOP_API_HASH')},
             'full_build_executed': False, 'runtime_test_executed': False}
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    (output / 'preflight.json').write_text(json.dumps(value, indent=2) + '\n')
    print(json.dumps(value, indent=2))
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as stream:
            stream.write('## Linux builder preflight\n\n```json\n' + json.dumps(value, indent=2) + '\n```\n')
    return value

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    report(parser.parse_args().output)
