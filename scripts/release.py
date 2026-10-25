#!/usr/bin/env python3
"""Authorized local Release campaign via the pinned container, with config gate."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import threading
import time
import identity

ROOT = Path(__file__).resolve().parents[1]


def check_configuration(out):
    out = Path(out)
    cache = (out/'CMakeCache.txt').read_text()
    for name,value in {'DESKTOP_APP_DISABLE_AUTOUPDATE':'ON'}.items():
        if not re.search(r'^'+name+r':BOOL='+value+r'$',cache,re.M):
            raise ValueError('Required build setting is missing: '+name)
    generated=(out/'CMakeFiles/impl-Release.ninja').read_text()
    match=re.search(r'^build Release/Jerkgram:.*\n((?:[ \t].*\n|\n)*)',generated,re.M)
    if not match:
        raise ValueError('Expected Release/Jerkgram output edge is absent')
    edge=match.group(1)
    flags=' '.join(re.findall(r'^  (?:FLAGS|LINK_FLAGS) = (.*)$',edge,re.M))
    lto=re.findall(r'(?<!\S)-flto(?:=[^\s]+)?',flags)
    compile_flags = re.findall(r'^  FLAGS = (.*)$', edge, re.M)
    if not any(re.search(r'(?<!\S)-flto(?:=|\s|$)', value) for value in compile_flags):
        raise ValueError('Effective Release LTO flags are absent')
    if not lto or lto[-1]!='-flto=1' or '--param=lto-max-streaming-parallelism=1' not in flags:
        raise ValueError('Final LTO concurrency is not bounded to one')
    for name in ('Core', 'Gui', 'Widgets'):
        if 'libQt6'+name+'.a' not in edge:
            raise ValueError('Expected static Qt library is absent: '+name)
    return True


def stream_run(args, log, secrets):
    with log.open('w') as output:
        child=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        for line in child.stdout:
            for value in secrets:
                line=line.replace(value,'[REDACTED]')
            output.write(line);output.flush()
            print(line,end='',flush=True)
        status=child.wait()
        if status:
            raise ValueError('Container command failed, exit '+str(status)+'; see redacted log')


def monitor(stop, path, summary):
    with path.open('w') as stream:
        while not stop.is_set():
            mem={x.split(':')[0]:int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines() if x.split(':')[0] in ('MemTotal','MemAvailable','SwapTotal','SwapFree')}
            processes=[]
            for p in Path('/proc').iterdir():
                if not p.name.isdigit():continue
                try:
                    name=(p/'comm').read_text().strip()
                    if name not in ('lto1','lto1-wpa-stream','g++','ld','ld.bfd','collect2'):continue
                    status=(p/'status').read_text()
                    m=re.search(r'^VmRSS:\s+(\d+)',status,re.M)
                    processes.append({'pid':int(p.name),'name':name,'rss_bytes':int(m[1])*1024 if m else 0})
                except (OSError,ProcessLookupError):continue
            summary['peak_host_used_bytes']=max(summary.get('peak_host_used_bytes',0),mem['MemTotal']-mem['MemAvailable'])
            summary['peak_swap_used_bytes']=max(summary.get('peak_swap_used_bytes',0),mem['SwapTotal']-mem['SwapFree'])
            summary['peak_lto_processes']=max(summary.get('peak_lto_processes',0),sum(p['name'].startswith('lto1') for p in processes))
            stream.write(json.dumps({'time':time.time(),'memory':mem,'processes':processes})+'\n');stream.flush()
            stop.wait(3)


def run(source, evidence, image='tdesktop:centos_env', jobs=2, configure_only=False):
    source,evidence=Path(source).resolve(),Path(evidence).resolve()
    expected=json.loads((ROOT/'PINNED_UPSTREAM').read_text())['commit']
    if identity.verify(source,expected,ROOT)!='materialized':raise ValueError('Source is not verified materialized output')
    if source.name!='telegram-desktop-d1':raise ValueError('Build requires the separate telegram-desktop-d1 checkout')
    config=identity.load(ROOT,expected)
    values=[os.environ.get(k,'') for k in ('TDESKTOP_API_ID','TDESKTOP_API_HASH')]
    if not re.fullmatch(r'[1-9][0-9]*',values[0]) or not re.fullmatch(r'[0-9a-fA-F]{32}',values[1]):
        raise ValueError('API credentials absent/invalid; values omitted')
    if jobs<1 or jobs>4:raise ValueError('Use 1–4 bounded compile jobs')
    evidence.mkdir(parents=True,exist_ok=True)
    image_id=subprocess.check_output(['docker','image','inspect','--format={{.Id}}',image],text=True).strip()
    args=['docker','run','--rm','-i','-u',str(os.getuid()),'-v',str(source)+':/usr/src/tdesktop',
          '-e','TDESKTOP_API_ID','-e','TDESKTOP_API_HASH','-e','CMAKE_BUILD_PARALLEL_LEVEL='+str(jobs),image,'bash','-c']
    settings=' '.join('-D '+k+'='+v for k,v in config['cmake'].items())
    command='set -e\ncd /usr/src/tdesktop/Telegram\n./configure.sh -D TDESKTOP_API_TEST=OFF -D "TDESKTOP_API_ID=$TDESKTOP_API_ID" -D "TDESKTOP_API_HASH=$TDESKTOP_API_HASH" '+settings+' -D "CMAKE_EXE_LINKER_FLAGS_RELEASE='+config['release_link_flags']+'"\n'
    start=time.time()
    stream_run(args+[command],evidence/'configure.log',values)
    check_configuration(source/'out')
    (evidence/'config-verified.json').write_text(json.dumps({'upstream':expected,'image_id':image_id,'config_sha256':identity.sha(ROOT/'D1_CONFIG.json'),'configuration':'Release','updater_disabled':True,'lto_workers':1,'qt_linkage':'static Core/Gui/Widgets verified in generated edge','requested_cmake':config['cmake']},indent=2)+'\n')
    if configure_only:return
    stop=threading.Event();summary={}
    thread=threading.Thread(target=monitor,args=(stop,evidence/'memory.jsonl',summary),daemon=True)
    thread.start()
    result={'status':'failed','started':start,'image_id':image_id,'configuration':'Release','compile_jobs':jobs}
    try:
        stream_run(args+['set -e\ncd /usr/src/tdesktop\ncmake --build out --config Release --target Telegram\n'],evidence/'compile.log',values)
        binary=source/'out/Release/Jerkgram'
        if not binary.is_file():raise ValueError('Expected binary was not produced')
        result.update(status='compiled',binary=str(binary),binary_bytes=binary.stat().st_size,binary_sha256=identity.sha(binary))
    finally:
        stop.set();thread.join()
        result.update(duration_seconds=time.time()-start,finished=time.time(),resources=summary)
        (evidence/'build.json').write_text(json.dumps(result,indent=2)+'\n')
    identity.verify(source,expected,ROOT)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',required=True)
    parser.add_argument('--evidence',required=True)
    parser.add_argument('--jobs',type=int,default=2)
    parser.add_argument('--configure-only',action='store_true')
    opts=parser.parse_args()
    run(opts.source,opts.evidence,jobs=opts.jobs,configure_only=opts.configure_only)
