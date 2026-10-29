#!/usr/bin/env python3
"""Measured no-behavior incremental changes; exact source restoration even on failure."""
import argparse,contextlib,json,os,time
from pathlib import Path
import build_profile as bp
import identity

@contextlib.contextmanager
def temporary_change(source,names,comment=False):
    saved={}
    try:
        for name in names:
            p=identity.safe(Path(source).resolve(),name)
            if not name.startswith('Telegram/SourceFiles/') or p.suffix not in ('.cpp','.h') or not p.is_file():raise ValueError('Benchmark edit outside source scope')
            stat=p.stat();data=p.read_bytes();saved[p]=(data,stat.st_atime_ns,stat.st_mtime_ns)
            if comment:p.write_bytes(data+b'\n// Jerkgram dev-loop benchmark: no behavior change.\n')
            os.utime(p,ns=(stat.st_atime_ns,max(time.time_ns(),stat.st_mtime_ns+1)))
        yield
    finally:
        for p,(data,atime,mtime) in saved.items():
            if p.read_bytes()!=data:p.write_bytes(data)
            os.utime(p,ns=(atime,mtime))

def benchmark(source,evidence,jobs=2):
    source,evidence=Path(source).resolve(),Path(evidence).resolve();bp.verify_source(source)
    if evidence.exists():raise ValueError('New benchmark evidence directory required')
    evidence.mkdir(parents=True);results={};status='running'
    cpp='Telegram/SourceFiles/intro/intro_start.cpp';about='Telegram/SourceFiles/boxes/about_box.cpp';header='Telegram/SourceFiles/intro/intro_start.h';owner='Telegram/SourceFiles/platform/linux/specific_linux.cpp'
    cases=[('no-op',[],False,0),('one-tu',[cpp],False,1),('two-tu',[cpp,about],False,2),('narrow-header',[header],False,None),('typical-small-patch',[owner],True,1)]
    try:
        for name,paths,comment,count in cases:
            bp.verify_source(source)
            with temporary_change(source,paths,comment=comment):
                result=bp.build(source,evidence/name,jobs,paths if comment else ())
            bp.verify_source(source)
            results[name]=result
            if count is not None and result['recompiled']!=count:raise ValueError(name+': unexpected compile fanout; inspect preserved records')
            if name=='narrow-header' and result['recompiled']>12:raise ValueError('Unexpected broad header fanout; stop benchmark')
            (evidence/'summary.json').write_text(json.dumps({'status':status,'results':results},indent=2)+'\n')
        # Rebuild the original bytes after the real comment edit, without leaving a cache
        # whose debug checksum describes the temporary comment. This cost is separate.
        with temporary_change(source,[owner]):results['restore-exact-source']=bp.build(source,evidence/'restore-exact-source',jobs)
        bp.verify_source(source);status='PASS'
    except Exception:
        status='FAILED'
        raise
    finally:
        restored=False
        try:
            bp.verify_source(source);restored=True
        except Exception:
            status='FAILED'
        (evidence/'summary.json').write_text(json.dumps({'status':status,'results':results,'source_restored':restored},indent=2)+'\n')
    print(json.dumps({'status':status,'cases':{k:{f:v[f] for f in ('duration_seconds','recompiled','link_seconds','build_tree_delta_bytes')} for k,v in results.items()}},indent=2))
    return results

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--evidence',required=True);p.add_argument('--jobs',type=int,default=2);a=p.parse_args();benchmark(a.source,a.evidence,a.jobs)
