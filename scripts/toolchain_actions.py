#!/usr/bin/env python3
"""One-job trusted local registry recovery/publication using Actions' package token."""
import argparse,json,os,shutil,subprocess,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REPO='ghostbase-sg/jerkgram-desktop-builder'
GH=shutil.which('gh') or str(Path.home()/'.local/bin/gh')

def dispatch_body(ref,operation):
    if operation not in ('publish','restore-registry'):raise ValueError('Only explicit toolchain operations are allowed')
    return {'ref':ref,'inputs':{'retain_toolchain':True,'toolchain_operation':operation}}

def api(path,method='GET',body=None):
    args=[GH,'api','--method',method,path]
    if body is not None:args+=['--input','-']
    p=subprocess.run(args,input=json.dumps(body) if body is not None else None,text=True,capture_output=True)
    if p.returncode:raise ValueError('GitHub API request failed; credentials/output omitted: '+method+' '+path)
    return json.loads(p.stdout) if p.stdout.strip() else None

def start(runner,evidence,operation):
    runner,evidence=Path(runner).resolve(),Path(evidence).resolve()
    if not (runner/'config.sh').is_file() or not (runner/'run.sh').is_file():raise ValueError('Existing official Actions runner installation required')
    if (runner/'.runner').exists() or (runner/'.credentials').exists():raise ValueError('Runner is already configured; do not replace an existing registration')
    if evidence.exists():raise ValueError('New evidence directory required')
    if subprocess.check_output(['git','-C',str(ROOT),'status','--porcelain'],text=True).strip():raise ValueError('Commit/push the reviewed workflow before registration')
    ref=subprocess.check_output(['git','-C',str(ROOT),'branch','--show-current'],text=True).strip();body=dispatch_body(ref,operation)
    head=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()
    if api('repos/'+REPO+'/commits/'+ref)['sha']!=head:raise ValueError('Local workflow commit is not pushed')
    evidence.mkdir(parents=True,mode=0o700);name='jerkgram-toolchain-'+str(int(time.time()))
    token=api('repos/'+REPO+'/actions/runners/registration-token','POST')['token']
    p=subprocess.run([str(runner/'config.sh'),'--url','https://github.com/'+REPO,'--token',token,'--name',name,'--labels','jerkgram-toolchain-publisher','--ephemeral','--unattended','--disableupdate','--work','_work'],cwd=runner,capture_output=True,text=True)
    if p.returncode:raise ValueError('Runner configuration failed; sensitive output omitted')
    with (evidence/'runner.log').open('wb') as log:
        child=subprocess.Popen([str(runner/'run.sh')],cwd=runner,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    record={'runner_name':name,'runner_dir':str(runner),'listener_pid':child.pid,'operation':operation,'ref':ref,'head':head,'started':time.time(),'one_job':True}
    state=evidence/'runner.json';state.write_text(json.dumps(record,indent=2)+'\n')
    try:api('repos/'+REPO+'/actions/workflows/linux-preflight.yml/dispatches','POST',body)
    except Exception:
        child.terminate();cleanup(state);raise
    return record

def cleanup(state):
    state=Path(state);record=json.loads(state.read_text());name=record['runner_name'];runner=Path(record['runner_dir'])
    if not name.startswith('jerkgram-toolchain-') or record.get('one_job') is not True:raise ValueError('Not an owned ephemeral toolchain runner')
    matches=[r for r in api('repos/'+REPO+'/actions/runners?per_page=100')['runners'] if r['name']==name]
    for r in matches:
        if r['busy']:raise ValueError('Owned runner still busy; wait for the single job')
        api('repos/'+REPO+'/actions/runners/'+str(r['id']),'DELETE')
    if (runner/'.runner').exists() or (runner/'.credentials').exists():
        token=api('repos/'+REPO+'/actions/runners/remove-token','POST')['token']
        p=subprocess.run([str(runner/'config.sh'),'remove','--token',token],cwd=runner,capture_output=True,text=True)
        if p.returncode:raise ValueError('Local runner cleanup failed; inspect configuration without exposing credentials')
    if (runner/'.runner').exists() or (runner/'.credentials').exists():raise ValueError('Runner credential files still present')
    record.update(cleanup_verified=True,finished=time.time());state.write_text(json.dumps(record,indent=2)+'\n');return {'cleanup_verified':True,'runner_name':name}

def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='action',required=True)
    a=sub.add_parser('start');a.add_argument('--runner-dir',required=True);a.add_argument('--evidence',required=True);a.add_argument('--operation',choices=('publish','restore-registry'),required=True)
    a=sub.add_parser('cleanup');a.add_argument('--state',required=True)
    a=p.parse_args();result=start(a.runner_dir,a.evidence,a.operation) if a.action=='start' else cleanup(a.state);print(json.dumps(result,indent=2))
if __name__=='__main__':main()
