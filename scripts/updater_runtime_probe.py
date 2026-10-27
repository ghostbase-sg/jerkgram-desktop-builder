#!/usr/bin/env python3
"""Bounded synthetic welcome updater probe. No DWARF loading, no real profiles."""
import argparse,json,os,re,signal,subprocess,sys,tempfile,time
from pathlib import Path


def discovery_hit(text):
    return bool(re.search(r'^UPDATER_HIT ', text, re.M))


def probe(binary,evidence):
    b,e=Path(binary).resolve(),Path(evidence).resolve()
    if b.name!='Jerkgram' or not b.is_file():raise ValueError('Compiled Jerkgram ELF required')
    e.mkdir(parents=True,exist_ok=True);r=Path(tempfile.mkdtemp(prefix='jerkgram-d1-updater-probe-'))
    env=dict(os.environ,HOME=str(r/'home'),XDG_DATA_HOME=str(r/'data'),XDG_CONFIG_HOME=str(r/'config'),XDG_CACHE_HOME=str(r/'cache'),QT_QPA_PLATFORM='xcb',DEBUGINFOD_URLS='',LC_ALL='C.UTF-8')
    for n in ('home','data','config','cache'):(r/n).mkdir()
    gdb=r/'probe.gdb';lines=['set pagination off','set confirm off','set debuginfod enabled off','set auto-load off','set startup-with-shell off','set print thread-events off']
    for idx,(name,marker) in enumerate([('Core::(anonymous namespace)::HttpChecker::start()','HTTP'),('Core::(anonymous namespace)::MtpChecker::start()','MTP'),('Core::UpdateChecker::UpdateChecker()','CHECKER_CONSTRUCTION')]):
     lines += ["break '"+name+"'",'commands','silent','printf "UPDATER_HIT '+marker+'\\n"','quit '+str(41+idx),'end']
    lines += ['run','printf "PROBE_OBSERVATION_END\\n"','info breakpoints','kill','quit 0'];gdb.write_text('\n'.join(lines)+'\n')
    log=e/'updater-probe.log'
    with log.open('w') as out:
     p=subprocess.Popen(['gdb','-nx','--readnever','-batch',str(b),'-x',str(gdb)],env=env,cwd=r,stdout=out,stderr=subprocess.STDOUT)
     end=time.monotonic()+90;pid=None;names=set();window=None
     while time.monotonic()<end and p.poll() is None:
      windows=json.loads(subprocess.check_output(['hyprctl','clients','-j'],text=True))
      window=next((w for w in windows if w.get('class')=='JerkgramDesktop' and w.get('title')=='Jerkgram'),None)
      if window:
       status=Path('/proc/'+str(window['pid'])+'/status').read_text()
       if any(x.startswith('PPid:') and int(x.split()[1])==p.pid for x in status.splitlines()):pid=window['pid'];break
      time.sleep(.5)
     if not pid:
      p.terminate();p.wait(timeout=10);raise RuntimeError('Probe did not reach a test welcome window; inspect log')
     start=time.monotonic()
     while time.monotonic()-start<35 and p.poll() is None:
      proc={}
      for entry in Path('/proc').iterdir():
       if not entry.name.isdigit():continue
       try:
        text=(entry/'status').read_text();parent=int(next(x.split()[1] for x in text.splitlines() if x.startswith('PPid:')));name=(entry/'comm').read_text().strip();proc[int(entry.name)]=(parent,name)
       except (OSError,StopIteration,ValueError):continue
      owned={pid};changed=True
      while changed:
       new={i for i,(parent,name) in proc.items() if parent in owned};changed=not new.issubset(owned);owned|=new
      names|={proc[i][1] for i in owned if i in proc};time.sleep(.2)
     if p.poll() is None:os.kill(p.pid,signal.SIGINT)
     code=p.wait(timeout=30)
    text=log.read_text(errors='replace');assert code==0,(code,text[-1500:]);assert 'PROBE_OBSERVATION_END' in text and not discovery_hit(text)
    assert text.count('Breakpoint ')>=3,text[-2000:]
    assert 'Updater' not in names and 'Packer' not in names
    result={'status':'PASS','scope':'35 seconds at synthetic unauthenticated welcome; no claim about later authenticated traffic','method':'live GDB breakpoints on HTTP/MTP discovery start and UpdateChecker construction, terminate own inferior after SIGINT','breakpoints':['HttpChecker::start','MtpChecker::start','UpdateChecker::UpdateChecker'],'discovery_hits':0,'observed_process_names':sorted(names),'test_pid':pid,'gdb_exit':code,'synthetic_root':str(r)}
    (e/'updater-probe.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--binary',required=True)
    parser.add_argument('--evidence',required=True)
    parser.add_argument('--inner-private-bus',action='store_true',help=argparse.SUPPRESS)
    args=parser.parse_args()
    if args.inner_private_bus:
        probe(args.binary,args.evidence)
    else:
        root=Path(tempfile.mkdtemp(prefix='jerkgram-d1-probe-bus-'))
        env=dict(os.environ,HOME=str(root),XDG_DATA_HOME=str(root/'data'),XDG_CONFIG_HOME=str(root/'config'),XDG_CACHE_HOME=str(root/'cache'))
        raise SystemExit(subprocess.call(['dbus-run-session','--',sys.executable,str(Path(__file__).resolve()),'--binary',str(Path(args.binary).resolve()),'--evidence',str(Path(args.evidence).resolve()),'--inner-private-bus'],env=env))
