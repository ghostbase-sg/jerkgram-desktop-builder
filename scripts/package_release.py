#!/usr/bin/env python3
"""Allowlist-only alpha archive; never strip the build output."""
import argparse
import io
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tarfile
import tempfile
import identity

ROOT=Path(__file__).resolve().parents[1]


def create_archive(binary, output, files, provenance, epoch):
    binary,output=Path(binary).resolve(),Path(output).resolve()
    if output.exists():raise ValueError('Artifact destination exists')
    version=provenance['version']
    if not re.fullmatch(r'[0-9A-Za-z.-]+',version):raise ValueError('Invalid release version')
    for name in files:
        parts=PurePosixPath(name)
        if parts.is_absolute() or '..' in parts.parts or name.startswith(('tdata/','out/')):
            raise ValueError('Unsafe package member')
    with binary.open('rb') as stream:header=stream.read(20)
    if header[:6]!=b'\x7fELF\x02\x01' or header[18:20]!=b'\x3e\x00':raise ValueError('Expected ELF64 x86-64 binary')
    original=identity.sha(binary)
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent,prefix='.jerkgram-package-') as temp:
        stage=Path(temp);copy=stage/'Jerkgram';shutil.copy2(binary,copy)
        subprocess.run(['strip','--strip-all',str(copy)],check=True)
        name=f'jerkgram-desktop-{version}-linux-x86_64.tar.xz'
        archive=stage/name
        with tarfile.open(archive,'w:xz',preset=6) as tf:
            def add(member,stream,size,mode):
                info=tarfile.TarInfo('Jerkgram/'+member);info.size=size;info.mode=mode;info.mtime=epoch
                tf.addfile(info,stream)
            with copy.open('rb') as stream:add('Jerkgram',stream,copy.stat().st_size,0o755)
            for member,data in sorted(files.items()):add(member,io.BytesIO(data),len(data),0o644)
        if identity.sha(binary)!=original:raise ValueError('Unstripped build output changed')
        report=dict(provenance,binary={'original_sha256':original,'original_bytes':binary.stat().st_size,
                                     'stripped_sha256':identity.sha(copy),'stripped_bytes':copy.stat().st_size},
                    artifact={'name':name,'bytes':archive.stat().st_size,'sha256':identity.sha(archive)})
        output.mkdir();shutil.copy2(archive,output/name)
        (output/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
        (output/'SHA256SUMS').write_text(report['artifact']['sha256']+'  '+name+'\n')
    return output/'manifest.json'


def integration_assets(root, config):
    root=Path(root)
    folder=root/'payloads/linux-identity/generated'
    declared={x['path']:x for x in config['payloads'] if x['path'].startswith('payloads/linux-identity/generated/')}
    actual={str(p.relative_to(root)) for p in folder.iterdir() if p.name.endswith('.png') or p.name.startswith('tray')}
    if actual!=set(declared):raise ValueError('Undeclared or missing integration asset')
    result={}
    for path,item in sorted(declared.items()):
        p=identity.safe(root,path)
        if identity.sha(p)!=item['sha256']:raise ValueError('Integration asset hash mismatch')
        if p.name.startswith('icon') or p.name.startswith('tray'):
            result['integration/icons/'+p.name]=p.read_bytes()
    return result


def source_notices(source):
    source=Path(source).resolve()
    names=subprocess.check_output(['git','-C',str(source),'ls-files','--recurse-submodules','-z','--',
                                   '*LICENSE*','*COPYING*','*NOTICE*','*COPYRIGHT*','*PATENTS*']).decode().split('\0')
    return {'licenses/source/'+name:identity.safe(source,name).read_bytes() for name in names if name}


def package(source,evidence,output):
    source,evidence=Path(source).resolve(),Path(evidence).resolve()
    if Path(output).resolve().is_relative_to(source):raise ValueError('Package outside source tree only')
    pin=json.loads((ROOT/'PINNED_UPSTREAM').read_text());config=identity.load(ROOT,pin['commit'])
    if identity.verify(source,pin['commit'],ROOT)!='materialized':raise ValueError('Unverified source')
    build=json.loads((evidence/'build.json').read_text());verified=json.loads((evidence/'config-verified.json').read_text())
    binary=source/'out/Release/Jerkgram'
    if build['status']!='compiled' or identity.sha(binary)!=build['binary_sha256'] or verified['config_sha256']!=identity.sha(ROOT/'D1_CONFIG.json'):
        raise ValueError('Build evidence does not match binary/configuration')
    assets=ROOT/'payloads/linux-identity'
    files={'LICENSE':(source/'LICENSE').read_bytes(),'NOTICE.txt':
           b'Jerkgram Desktop: independent client based on Telegram Desktop 7.3.1.\nTelegram API and upstream GPL attribution retained.\nThis alpha has no automatic updater. Do not use official Telegram updates for it.\nBuilder/overlay source: https://github.com/ghostbase-sg/jerkgram-desktop-builder\n',
           'install_linux.py':(ROOT/'scripts/install_linux.py').read_bytes(),
           'README.txt':b'Run ./Jerkgram. Default profile: XDG_DATA_HOME/JerkgramDesktop.\nAdjacent JerkgramForcePortable opts into portable data. No profile is shipped.\nOptional integration: python3 install_linux.py --apply (inspect without --apply first).\nUpdates: manual Jerkgram releases only.\n'}
    if (source/'LEGAL').is_file():files['LEGAL']=(source/'LEGAL').read_bytes()
    for name in ('com.jerkgram.desktop.desktop','com.jerkgram.desktop.service'):
        files['integration/'+name]=(assets/name).read_bytes()
    files.update(integration_assets(ROOT,config))
    files.update(source_notices(source))
    active_path=evidence/'active-run.json'
    workflow=json.loads(active_path.read_text()) if active_path.exists() else {}
    manifest={'schema':1,'version':config['version'],'upstream':pin,
              'builder_sha':workflow.get('builder_sha',identity.git(ROOT,'rev-parse','HEAD')),
              'workflow_run_id':workflow.get('run_id'),'packager_builder_sha':identity.git(ROOT,'rev-parse','HEAD'),'builder_dirty':bool(identity.git(ROOT,'status','--porcelain')),
              'overlay_config_sha256':identity.sha(ROOT/'D1_CONFIG.json'),'patches':config['patches'],
              'payloads':config['payloads'],'notice_members':[n for n in sorted(files) if n.startswith('licenses/')],'updater_policy':'disabled; manual releases only',
              'build_configuration':verified,'build':build,'runtime_evidence':'see separate runtime report; packaging asserts none'}
    epoch=int(identity.git(source,'show','-s','--format=%ct','HEAD'))
    return create_archive(binary,output,files,manifest,epoch)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source',required=True);parser.add_argument('--evidence',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args();print(package(args.source,args.evidence,args.output))
