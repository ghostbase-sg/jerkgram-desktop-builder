#!/usr/bin/env python3
"""Container entry point. Credentials remain in the existing CMake configuration."""
import argparse,os,re,subprocess
from pathlib import Path
from build_profile import dev_flags,load

def entries(cache):
    text=Path(cache).read_text();result={}
    for name in ('TDESKTOP_API_ID','TDESKTOP_API_HASH'):
        m=re.search(r'^'+name+r':[^=]+=(.*)$',text,re.M)
        if not m:raise ValueError('Existing configured API is missing; values omitted')
        result[name]=m[1]
    return result

def execute(operation,jobs):
    os.umask(0o077)
    source=Path('/usr/src/tdesktop');out=source/'out/dev-fast';config=load()['dev-fast']
    values=entries(source/'out/CMakeCache.txt')
    env=dict(os.environ,CFLAGS=dev_flags(os.environ['CFLAGS']),CXXFLAGS=dev_flags(os.environ['CXXFLAGS']),JERKGRAM_PRODUCTION_OUT=str(source/'out'),PYTHONDONTWRITEBYTECODE='1')
    if operation=='configure':
        args=['cmake','-S',str(source),'-B',str(out),'-G','Ninja','-DCMAKE_BUILD_TYPE=Release','-DCMAKE_EXPORT_COMPILE_COMMANDS=ON','-DCMAKE_EXE_LINKER_FLAGS_RELEASE='+config['link_flags'],'-C','/opt/jerkgram-builder/cmake/reuse_credentials.cmake']
        args+=['-D'+k+'='+v for k,v in config['cmake'].items()]
    else:
        if entries(out/'CMakeCache.txt')!=values:raise ValueError('Dev/production configured API differs; values omitted')
        args=['cmake','--build',str(out),'--target','Telegram','--parallel',str(jobs)]
    p=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,env=env)
    for line in p.stdout:
        for value in sorted(values.values(),key=len,reverse=True):line=line.replace(value,'[REDACTED]')
        print(line,end='',flush=True)
    code=p.wait()
    if code:raise SystemExit(code)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('operation',choices=('configure','build'));p.add_argument('--jobs',type=int,default=2);a=p.parse_args();execute(a.operation,a.jobs)
