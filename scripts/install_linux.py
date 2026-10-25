#!/usr/bin/env python3
"""Explicit user-local launcher integration. Dry-run by default; no MIME defaults."""
import argparse
import json
import os
from pathlib import Path
import re
import shlex

APP_ID='com.jerkgram.desktop'


def desktop_argument(value):
    if '\n' in value or '\r' in value:raise ValueError('Invalid executable path')
    # Escape for Exec quoting, then for the desktop keyfile string layer.
    value=value.replace('%','%%')
    for ch in ('\\','"','`','$'):
        value=value.replace(ch,'\\'+ch)
    return '"'+value.replace('\\','\\\\')+'"'


def install(package, xdg, apply=False):
    package,xdg=Path(package).resolve(),Path(xdg).resolve()
    executable=package/'Jerkgram'
    if not executable.is_file():raise ValueError('Jerkgram executable is absent')
    template=(package/'integration'/f'{APP_ID}.desktop').read_text()
    quoted=desktop_argument(str(executable))
    lines=[]
    for line in template.splitlines():
        if line.startswith('Exec=Jerkgram'):line='Exec='+quoted+line[len('Exec=Jerkgram'):]
        elif line.startswith('TryExec='):line='TryExec='+str(executable).replace('\\','\\\\')
        lines.append(line)
    plan={f'applications/{APP_ID}.desktop':('\n'.join(lines)+'\n').encode(),
          f'dbus-1/services/{APP_ID}.service':('[D-BUS Service]\nName='+APP_ID+'\nExec='+shlex.quote(str(executable))+'\n').encode()}
    for icon in (package/'integration/icons').glob('icon*.png'):
        m=re.fullmatch(r'icon(16|32|48|64|128|256|512)(@2x)?\.png',icon.name)
        if not m:raise ValueError('Unexpected icon derivative')
        size=m[1];scale='@2' if m[2] else ''
        plan[f'icons/hicolor/{size}x{size}{scale}/apps/{APP_ID}.png']=icon.read_bytes()
    for suffix,state in (('',''),('_attention','-attention'),('_mute','-mute')):
        p=package/'integration/icons'/f'tray_monochrome{suffix}.svg'
        if p.exists():plan[f'icons/hicolor/symbolic/apps/{APP_ID}{state}-symbolic.svg']=p.read_bytes()
    # Validate the entire destination plan before writing any integration file.
    for name in plan:
        target=xdg/name
        if any(p.is_symlink() for p in (target,*target.parents)):
            raise ValueError('Symlink in integration destination')
    if apply:
        for name,data in plan.items():
            target=xdg/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    return sorted(str(xdg/name) for name in plan)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--package',type=Path,default=Path(__file__).resolve().parent)
    parser.add_argument('--xdg-data-home',type=Path,default=Path(os.getenv('XDG_DATA_HOME',str(Path.home()/'.local/share'))))
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args();print(json.dumps({'applied':args.apply,'owned_paths':install(args.package,args.xdg_data_home,args.apply)},indent=2))
