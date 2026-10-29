#!/usr/bin/env python3
"""DEV-only launch smoke in synthetic HOME/XDG and a private session bus."""
import argparse,json,os,subprocess,time
from pathlib import Path
from runtime_smoke import Registrar,observe,wait,capture,snapshot

def run(binary,root,evidence,platform='xcb'):
    binary=Path(binary).resolve();root=Path(root).resolve();evidence=Path(evidence).resolve()
    if binary.name!='Jerkgram' or binary.parent.name!='dev-fast' or not binary.is_file():raise ValueError('Expected DEV Jerkgram binary')
    if not str(root).startswith('/tmp/jerkgram-dev-runtime-') or root.exists():raise ValueError('New synthetic runtime root required')
    if evidence.exists():raise ValueError('Use a new evidence directory')
    root.mkdir(mode=0o700);evidence.mkdir(parents=True)
    for name in ('home','data','config','cache','cwd'):(root/name).mkdir()
    sentinel=root/'data/TelegramDesktop/tdata/settings0';sentinel.parent.mkdir(parents=True);sentinel.write_text('Synthetic official Telegram sentinel\n');before=snapshot([sentinel])
    env=dict(os.environ,HOME=str(root/'home'),XDG_DATA_HOME=str(root/'data'),XDG_CONFIG_HOME=str(root/'config'),XDG_CACHE_HOME=str(root/'cache'),QT_QPA_PLATFORM=platform,LANG='C.UTF-8',LC_ALL='C.UTF-8',LANGUAGE='en')
    menu=Registrar();app=None;result={'status':'FAILED','platform':platform,'synthetic_root':str(root),'binary':str(binary)}
    try:
        with (evidence/'stderr.log').open('wb') as log:
            app=subprocess.Popen([str(binary)],cwd=root/'cwd',env=env,stdout=log,stderr=subprocess.STDOUT)
        window=wait(lambda:next((w for w in observe({app.pid}) if w['mapped'] and not w['hidden']),None));time.sleep(3)
        if app.poll() is not None:raise RuntimeError('Immediate process exit')
        if not (root/'data/JerkgramDesktop/tdata').is_dir():raise RuntimeError('Own default profile missing')
        wait(lambda:'com.jerkgram.desktop' in menu.names())
        if menu.pid('com.jerkgram.desktop')!=app.pid:raise RuntimeError('Wrong D-Bus identity owner')
        result['welcome']=capture(app.pid,evidence/'welcome.png')
        if platform=='xcb':
            wait(lambda:menu.about(app.pid));time.sleep(1);result['about']=capture(app.pid,evidence/'about.png')
        refusal=subprocess.run([str(binary),'-installupdate',str(root/'absent-update')],env=env,cwd=root/'cwd',capture_output=True,text=True,timeout=20)
        (evidence/'update-refusal.log').write_text(refusal.stdout+refusal.stderr)
        if refusal.returncode==0 or 'Automatic updates are disabled' not in refusal.stderr:raise RuntimeError('Updater refusal gate failed')
        if snapshot([sentinel])!=before:raise RuntimeError('Synthetic official Telegram sentinel changed')
        if app.poll() is not None:raise RuntimeError('Process crashed during smoke')
        result.update(status='DEV RUNTIME PASSED',pid=app.pid,own_profile=True,own_dbus=True,updater_refused=True,official_sentinel_preserved=True,authenticated_behavior_tested=False)
    except Exception as exc:
        result['error']=str(exc);raise
    finally:
        if app and app.poll() is None:
            app.terminate()
            try:app.wait(timeout=10)
            except subprocess.TimeoutExpired:app.kill();app.wait()
        menu.loop.quit();result['finished']=time.time();(evidence/'runtime.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2));return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--binary',required=True);p.add_argument('--root',required=True);p.add_argument('--evidence',required=True);p.add_argument('--platform',choices=('xcb','wayland'),default='xcb');a=p.parse_args();run(a.binary,a.root,a.evidence,a.platform)
