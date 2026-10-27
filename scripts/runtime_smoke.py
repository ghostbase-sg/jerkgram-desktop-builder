#!/usr/bin/env python3
"""Synthetic-only coexistence evidence; run under one private dbus-run-session."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import threading
import time


def observe(pids):
    rows=json.loads(subprocess.check_output(['hyprctl','clients','-j'],text=True))
    return [{k:r.get(k) for k in ('pid','mapped','hidden','title','class','initialClass','xwayland','address','at','size')}
            for r in rows if r.get('pid') in pids]


def wait(check,seconds=45):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        value=check()
        if value:return value
        time.sleep(.5)
    raise RuntimeError('Runtime observation timed out')


def snapshot(files):
    return {str(p):[hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_mtime_ns] for p in files}


class Registrar:
    def __init__(self):
        from gi.repository import Gio,GLib
        self.G,self.IO=GLib,Gio;self.conn=Gio.bus_get_sync(Gio.BusType.SESSION,None);self.menus={}
        xml='''<node><interface name="com.canonical.AppMenu.Registrar">
        <method name="RegisterWindow"><arg type="u" direction="in"/><arg type="o" direction="in"/></method>
        <method name="UnregisterWindow"><arg type="u" direction="in"/></method>
        <method name="GetMenuForWindow"><arg type="u" direction="in"/><arg type="s" direction="out"/><arg type="o" direction="out"/></method>
        <method name="GetMenus"><arg type="a(uso)" direction="out"/></method>
        <signal name="WindowRegistered"><arg type="u"/><arg type="s"/><arg type="o"/></signal>
        <signal name="WindowUnregistered"><arg type="u"/></signal></interface></node>'''
        info=Gio.DBusNodeInfo.new_for_xml(xml)
        self.conn.register_object('/com/canonical/AppMenu/Registrar',info.interfaces[0],self.method,None,None)
        self.call('org.freedesktop.DBus','/org/freedesktop/DBus','org.freedesktop.DBus','RequestName',GLib.Variant('(su)',('com.canonical.AppMenu.Registrar',0)))
        self.loop=GLib.MainLoop();threading.Thread(target=self.loop.run,daemon=True).start()

    def call(self,dest,path,iface,method,args):
        return self.conn.call_sync(dest,path,iface,method,args,None,self.IO.DBusCallFlags.NONE,5000,None).unpack()

    def method(self,connection,sender,path,iface,method,params,invocation):
        a=params.unpack();G=self.G
        if method=='RegisterWindow':
            self.menus[(sender,a[0])]=a[1];invocation.return_value(G.Variant('()',()))
            connection.emit_signal(None,path,iface,'WindowRegistered',G.Variant('(uso)',(a[0],sender,a[1])))
        elif method=='UnregisterWindow':
            self.menus.pop((sender,a[0]),None);invocation.return_value(G.Variant('()',()))
        elif method=='GetMenuForWindow':
            row=next(((s,p) for (s,w),p in self.menus.items() if w==a[0]),('', '/'))
            invocation.return_value(G.Variant('(so)',row))
        else:invocation.return_value(G.Variant('(a(uso))',([(w,s,p) for (s,w),p in self.menus.items()],)))

    def names(self):return self.call('org.freedesktop.DBus','/org/freedesktop/DBus','org.freedesktop.DBus','ListNames',None)[0]

    def pid(self,name):
        return self.call('org.freedesktop.DBus','/org/freedesktop/DBus','org.freedesktop.DBus','GetConnectionUnixProcessID',self.G.Variant('(s)',(name,)))[0]

    def about(self,pid):
        for (sender,window),path in list(self.menus.items()):
            if self.pid(sender)!=pid:continue
            tree=self.call(sender,path,'com.canonical.dbusmenu','GetLayout',self.G.Variant('(iias)',(0,-1,[])))[1]
            def search(node):
                if hasattr(node,'unpack'):node=node.unpack()
                ident,props,children=node;label=props.get('label','')
                if hasattr(label,'unpack'):label=label.unpack()
                if 'About' in label and 'Jerkgram' in label:return ident
                for child in children:
                    found=search(child)
                    if found is not None:return found
            ident=search(tree)
            if ident is not None:
                self.call(sender,path,'com.canonical.dbusmenu','Event',self.G.Variant('(isvu)',(ident,'clicked',self.G.Variant('i',0),0)))
                return True
        return False


def capture(pid,path):
    window=wait(lambda:next((r for r in observe({pid}) if r['mapped'] and not r['hidden']),None))
    subprocess.run(['hyprctl','dispatch','hl.dsp.focus({ window = '+json.dumps('address:'+window['address'])+' })'],check=True,stdout=subprocess.DEVNULL)
    time.sleep(.7);x,y=window['at'];w,h=window['size']
    subprocess.run(['grim','-g',f'{x},{y} {w}x{h}',str(path)],check=True)
    return window


def run(binary,stock,root,evidence,platform):
    root,evidence=Path(root).resolve(),Path(evidence).resolve();binary,stock=Path(binary).resolve(),Path(stock).resolve()
    if not str(root).startswith('/tmp/jerkgram-d1-runtime-') or root.exists():raise ValueError('New synthetic runtime root required')
    if not binary.is_file() or binary.name!='Jerkgram' or not stock.is_file() or stock.name!='Telegram':raise ValueError('Compiled binary paths required')
    root.mkdir(mode=0o700);evidence.mkdir(parents=True,exist_ok=True)
    home,data,config,cwd,sw=(root/n for n in ('home','data','config','cwd','stock-work'))
    for p in (home,data,config,cwd,sw):p.mkdir()
    files=[]
    for p in (home/'.TelegramDesktop/tdata/settings0',data/'TelegramDesktop/tdata/settings0',cwd/'data',cwd/'data_config',cwd/'tdata/config',data/'applications/org.telegram.desktop.desktop',config/'mimeapps.list'):
        p.parent.mkdir(parents=True,exist_ok=True);p.write_text('Synthetic Telegram sentinel\n');files.append(p)
    (config/'mimeapps.list').write_text('[Default Applications]\nx-scheme-handler/tg=org.telegram.desktop.desktop;\nx-scheme-handler/ton=org.telegram.desktop.desktop;\nx-scheme-handler/tonsite=org.telegram.desktop.desktop;\n')
    adjacent=[]
    for name in ('TelegramForcePortable','TelegramAlpha_data','TelegramBeta_data'):
        folder=binary.parent/name
        if folder.exists():raise ValueError('Unexpected adjacent profile directory; refusing to inspect it')
        (folder/'tdata').mkdir(parents=True)
        sentinel=folder/'tdata/settings0';sentinel.write_text('Synthetic adjacent Telegram sentinel\n')
        files.append(sentinel);adjacent.append(folder)
    original=snapshot(files)
    env=dict(os.environ,HOME=str(home),XDG_DATA_HOME=str(data),XDG_CONFIG_HOME=str(config),XDG_CACHE_HOME=str(root/'cache'),QT_QPA_PLATFORM=platform,LANG='C.UTF-8',LC_ALL='C.UTF-8',LANGUAGE='en')
    (sw/'externalupdater.d').mkdir();(sw/'externalupdater.d/test').write_text(str(stock)+'\n')
    menu=Registrar();children=[];handles=[]
    result={'platform':platform,'synthetic_root':str(root),'session_bus':'one private shared bus','gates':{},'pending':[],'status':'FAILED'}
    def launch(path,args,label):
        f=(evidence/(label+'.stderr.log')).open('wb');handles.append(f)
        child=subprocess.Popen([str(path),*args],cwd=(sw if path==stock else cwd),env=env,stdout=f,stderr=subprocess.STDOUT);children.append(child);return child
    try:
        app=launch(binary,[],'jerkgram');wait(lambda:observe({app.pid}));time.sleep(3)
        if snapshot(files)!=original:raise RuntimeError('Synthetic Telegram/default-handler sentinel modified')
        profile=data/'JerkgramDesktop/tdata'
        if not profile.is_dir():raise RuntimeError('Own default profile missing')
        result['gates'].update(profile=str(profile),legacy_and_url_sentinels_untouched=True)
        log=data/'JerkgramDesktop/log.txt'
        if log.exists():
            result['application_log_fields']=[line for line in log.read_text(errors='replace').splitlines() if any(field in line for field in ('App ID:', 'Working dir:', 'Launched version:', 'Executable dir:'))]
        result['welcome']=capture(app.pid,evidence/'welcome.png')
        if menu.about(app.pid):time.sleep(1);result['about']=capture(app.pid,evidence/'about.png')
        else:result['pending'].append('About menu activation unavailable; manual evidence still required')
        official=launch(stock,['-workdir',str(sw),'-noupdate'],'stock');wait(lambda:observe({official.pid}))
        if app.poll() is not None or official.poll() is not None:raise RuntimeError('Coexistence process exited')
        result['gates']['coexistence_pids']={'Jerkgram':app.pid,'Telegram':official.pid}
        for path,args,label in ((binary,[],'jerkgram-repeat'),(stock,['-workdir',str(sw),'-noupdate'],'stock-repeat')):
            child=launch(path,args,label);child.wait(timeout=20)
            if child.returncode!=0:raise RuntimeError('Repeated launch failed')
        if app.poll() is not None or official.poll() is not None:raise RuntimeError('Repeat launch replaced original process')
        result['gates']['repeated_launch_independent']=True
        names=menu.names()
        for name in ('com.jerkgram.desktop','org.telegram.desktop'):
            if name not in names:raise RuntimeError('Gio identity missing: '+name)
        result['gates']['gio_identities']={n:menu.pid(n) for n in ('com.jerkgram.desktop','org.telegram.desktop')}
        for name,path in (('com.jerkgram.desktop','/com/jerkgram/desktop'),('org.telegram.desktop','/org/telegram/desktop')):
            menu.call(name,path,'org.freedesktop.Application','Activate',menu.G.Variant('(a{sv})',({},)))
        result['gates']['live_dbus_activation']=True
        result['windows']=observe({app.pid,official.pid})
        if 'org.mpris.MediaPlayer2.JerkgramDesktop' in names:result['gates']['mpris']='org.mpris.MediaPlayer2.JerkgramDesktop'
        else:result['pending'].append('MPRIS playback bus not present at welcome; authenticated media check pending')
        refusal=subprocess.run([str(binary),'-installupdate',str(root/'nonexistent-package')],cwd=cwd,env=env,capture_output=True,text=True,timeout=20)
        (evidence/'installupdate-refusal.log').write_text(refusal.stdout+refusal.stderr)
        if refusal.returncode==0 or 'Automatic updates are disabled' not in refusal.stderr:raise RuntimeError('Disabled updater did not refuse safely')
        result['gates']['installupdate_refused']=True
        result['gates']['alive_at_end']=app.poll() is None and official.poll() is None
        result['pending']+=['Authenticated notification/MTP behavior not claimed','Tray requires a notifier host on this private bus']
        # Sequential same-product profile tests: do not hide fixed Gio-name constraints.
        app.terminate();app.wait(timeout=10)
        official.terminate();official.wait(timeout=10)
        wait(lambda:'com.jerkgram.desktop' not in menu.names(),15)
        portable=binary.parent/'JerkgramForcePortable'
        if portable.exists():raise ValueError('Unexpected Jerkgram portable directory; refusing to inspect it')
        portable.mkdir();adjacent.append(portable)
        portable_app=launch(binary,[],'jerkgram-portable');wait(lambda:observe({portable_app.pid}));time.sleep(2)
        if not (portable/'tdata').is_dir():raise RuntimeError('Own portable profile was not selected')
        result['gates']['portable_profile']=str(portable/'tdata')
        portable_app.terminate();portable_app.wait(timeout=10)
        wait(lambda:'com.jerkgram.desktop' not in menu.names(),15)
        advanced=root/'advanced';advanced.mkdir()
        override=launch(binary,['-workdir',str(advanced)],'jerkgram-workdir');wait(lambda:observe({override.pid}));time.sleep(2)
        if not (advanced/'tdata').is_dir():raise RuntimeError('Explicit workdir was not preserved')
        result['gates']['explicit_workdir']=str(advanced/'tdata')
        legacy_files=[f for f in files if f!=config/'mimeapps.list']
        if snapshot(legacy_files)!={str(f):original[str(f)] for f in legacy_files}:raise RuntimeError('Legacy sentinel changed during profile tests')
        result['status']='RUNTIME COEXISTENCE PASSED'
    except Exception as error:
        result['error']=str(error);raise
    finally:
        for child in children:
            if child.poll() is None:child.terminate()
        for child in children:
            try:child.wait(timeout=10)
            except subprocess.TimeoutExpired:child.kill();child.wait()
        for f in handles:f.close()
        if result['status']=='RUNTIME COEXISTENCE PASSED':
            import shutil
            for folder in adjacent:shutil.rmtree(folder)
        result['finished']=time.time();(evidence/'runtime.json').write_text(json.dumps(result,indent=2)+'\n');menu.loop.quit()
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--binary',required=True);p.add_argument('--stock',required=True);p.add_argument('--root',required=True);p.add_argument('--evidence',required=True);p.add_argument('--platform',choices=('xcb','wayland'),default='xcb')
    a=p.parse_args();run(a.binary,a.stock,a.root,a.evidence,a.platform)
