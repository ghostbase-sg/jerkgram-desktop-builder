#!/usr/bin/env python3
"""Digest-pinned toolchain archive fallback when the registry transport is unavailable."""
import argparse,concurrent.futures,hashlib,json,re,shutil,subprocess,tempfile,threading,time
from pathlib import Path
import toolchain
ROOT=Path(__file__).resolve().parents[1]
REPO='ghostbase-sg/jerkgram-desktop-builder'
GH=shutil.which('gh') or str(Path.home()/'.local/bin/gh')
MANIFEST='toolchain-archive-manifest.json'

def sha(p):return toolchain.sha(p)
def encoded(value):return (json.dumps(value,sort_keys=True,indent=2)+'\n').encode()
def api(path,method='GET',body=None):
    args=[GH,'api','--method',method,path]
    if body is not None:args+=['--input','-']
    for attempt in range(3):
        try:return json.loads(subprocess.check_output(args,input=encoded(body) if body is not None else None,stderr=subprocess.PIPE))
        except subprocess.CalledProcessError as exc:
            message=(exc.stderr or b'').decode(errors='replace')
            if method!='GET' or attempt==2 or not any(x in message for x in ('TLS handshake timeout','connection reset','unexpected EOF','HTTP 502','HTTP 503','HTTP 504')):raise
            time.sleep(attempt+1)
def valid_name(name):
    if Path(name).name!=name or name in ('','.','..'):raise ValueError('Unsafe archive asset name')
    return name

def plan(archive,image_id,chunk_bytes=128*1024**2):
    archive=Path(archive)
    if archive.is_symlink() or not archive.is_file() or not re.fullmatch('sha256:[a-f0-9]{64}',image_id):raise ValueError('Expected regular checked archive and image ID')
    if not 1<=chunk_bytes<=128*1024**2:raise ValueError('Use bounded chunks at most128MiB')
    whole=hashlib.sha256();parts=[];offset=0
    with archive.open('rb') as f:
        while True:
            h=hashlib.sha256();size=0
            while size<chunk_bytes:
                data=f.read(min(1024**2,chunk_bytes-size))
                if not data:break
                h.update(data);whole.update(data);size+=len(data)
            if not size:break
            parts.append({'name':valid_name(archive.name)+'.part-'+str(len(parts)).zfill(4),'offset':offset,'bytes':size,'sha256':h.hexdigest()});offset+=size
    if not parts:raise ValueError('Empty archive')
    return {'schema':1,'archive_name':archive.name,'archive_bytes':offset,'archive_sha256':whole.hexdigest(),'image_id':image_id,'parts':parts}

def validate(value):
    valid_name(value['archive_name']);offset=0;names=set()
    for part in value['parts']:
        name=valid_name(part['name'])
        if name in names or part['offset']!=offset or not 0<part['bytes']<=128*1024**2 or not re.fullmatch('[a-f0-9]{64}',part['sha256']):raise ValueError('Invalid chunk manifest')
        names.add(name);offset+=part['bytes']
    if not names or offset!=value['archive_bytes']:raise ValueError('Missing archive chunks')

def spool(archive,part,destination):
    with Path(archive).open('rb') as source,Path(destination).open('xb') as output:
        source.seek(part['offset']);remaining=part['bytes'];h=hashlib.sha256()
        while remaining:
            data=source.read(min(1024**2,remaining))
            if not data:raise ValueError('Truncated original archive')
            output.write(data);h.update(data);remaining-=len(data)
    if h.hexdigest()!=part['sha256']:raise ValueError('Original archive changed during upload')

def join(parts,value,destination):
    validate(value);destination=Path(destination);partial=destination.with_name(destination.name+'.partial')
    if destination.exists() or partial.exists():raise ValueError('Refuse to overwrite recovery output')
    h=hashlib.sha256()
    with partial.open('xb') as output:
        for part in value['parts']:
            path=Path(parts)/part['name']
            if path.stat().st_size!=part['bytes'] or sha(path)!=part['sha256']:raise ValueError('Missing/tampered archive chunk')
            with path.open('rb') as source:
                while data:=source.read(1024**2):output.write(data);h.update(data)
    if h.hexdigest()!=value['archive_sha256']:raise ValueError('Reassembled archive checksum mismatch')
    partial.rename(destination)

def asset_matches(asset,part):return asset.get('name')==part['name'] and asset.get('size')==part['bytes'] and asset.get('digest')=='sha256:'+part['sha256']

def release(tag):
    return next((r for r in api('repos/'+REPO+'/releases?per_page=100') if r['tag_name']==tag),None)

def ensure_release(tag,head):
    info=release(tag)
    if info is not None:return info
    notes='Pinned upstream Linux dependencies only; no product source/output/profiles/API credentials. Infrastructure retention, not a product release. Recover with the builder lock and scripts/archive_release.py; verify every SHA256 before loading.'
    return api('repos/'+REPO+'/releases',method='POST',body={'tag_name':tag,'target_commitish':head,'name':'Pinned Linux toolchain v7.3.1 '+tag.rsplit('-',1)[-1],'body':notes,'draft':True,'prerelease':True,'make_latest':'false'})

def publish(archive,output):
    archive=Path(archive).resolve();output=Path(output).resolve();lock=json.loads((ROOT/'toolchains/lock.json').read_text());value=plan(archive,lock['image_id'])
    if value['archive_sha256']!=lock['archive_sha256']:raise ValueError('Archive is not the pinned checked backup')
    tag='toolchain-v7.3.1-'+lock['image_id'][7:19];started=time.time()
    with tempfile.TemporaryDirectory(prefix='jerkgram-toolchain-upload-') as temp:
        temp=Path(temp);manifest=temp/MANIFEST;manifest.write_bytes(encoded(value))
        head=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip();info=ensure_release(tag,head)
        existing={a['name']:a for a in api('repos/'+REPO+'/releases/'+str(info['id'])+'/assets?per_page=100')};done=[];mutex=threading.Lock()
        def upload(part):
            if part['name'] in existing:
                if not asset_matches(existing[part['name']],part):raise ValueError('Existing versioned release asset differs: '+part['name'])
            else:
                with tempfile.TemporaryDirectory(prefix='chunk-',dir=temp) as chunk:
                    path=Path(chunk)/part['name'];spool(archive,part,path)
                    subprocess.run([GH,'release','upload',tag,str(path),'--repo',REPO],check=True)
            with mutex:
                done.append(part['name']);output.write_bytes(encoded({'status':'uploading','tag':tag,'complete_parts':len(done),'parts':len(value['parts']),'started':started}))
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(upload,value['parts']))
        m={'name':MANIFEST,'bytes':manifest.stat().st_size,'sha256':sha(manifest)}
        if MANIFEST in existing:
            if not asset_matches(existing[MANIFEST],m):raise ValueError('Existing recovery manifest differs')
        else:subprocess.run([GH,'release','upload',tag,str(manifest),'--repo',REPO],check=True)
        assets={a['name']:a for a in api('repos/'+REPO+'/releases/'+str(info['id'])+'/assets?per_page=100')}
        if any(not asset_matches(assets.get(p['name'],{}),p) for p in value['parts']+[m]):raise ValueError('Remote asset checksum verification failed')
        subprocess.run([GH,'release','edit',tag,'--repo',REPO,'--draft=false','--latest=false'],check=True)
        result={'status':'published','repository':REPO,'tag':tag,'url':info['html_url'],'release_id':info['id'],'manifest_name':MANIFEST,'manifest_sha256':sha(manifest),'archive_sha256':value['archive_sha256'],'parts':len(value['parts']),'archive_bytes':value['archive_bytes'],'remote_digests_verified':True,'duration_seconds':time.time()-started}
        output.write_bytes(encoded(result));return result

def recover(output,verify_only=False,destination=None):
    lock=json.loads((ROOT/'toolchains/lock.json').read_text());pin=lock['archive_release']
    if pin['repository']!=REPO or not re.fullmatch(r'toolchain-v7\.3\.1-[a-f0-9]{12}',pin['tag']):raise ValueError('Unexpected recovery destination')
    started=time.time();destination=Path(destination).resolve() if destination else None
    if not verify_only and destination is None:raise ValueError('New output archive path required')
    if destination:destination.parent.mkdir(parents=True,exist_ok=True)
    partial=destination.with_name(destination.name+'.partial') if destination else None
    if destination and (destination.exists() or partial.exists()):raise ValueError('Refuse to overwrite archive')
    with tempfile.TemporaryDirectory(prefix='jerkgram-toolchain-download-') as temp:
        temp=Path(temp)
        def download(name):
            subprocess.run([GH,'release','download',pin['tag'],'--repo',REPO,'--pattern',name,'--dir',str(temp)],check=True);return temp/name
        manifest=download(MANIFEST)
        if sha(manifest)!=pin['manifest_sha256']:raise ValueError('Remote manifest differs from committed pin')
        value=json.loads(manifest.read_text());validate(value)
        if value['image_id']!=lock['image_id'] or value['archive_sha256']!=lock['archive_sha256']:raise ValueError('Remote archive identity differs')
        h=hashlib.sha256();sink=partial.open('xb') if partial else None
        try:
            for i,part in enumerate(value['parts']):
                path=download(part['name'])
                if path.stat().st_size!=part['bytes'] or sha(path)!=part['sha256']:raise ValueError('Remote chunk checksum mismatch')
                with path.open('rb') as source:
                    while data:=source.read(1024**2):
                        h.update(data)
                        if sink:sink.write(data)
                path.unlink() # Only this invocation's disposable download spool, never retained backups/evidence.
                Path(output).write_bytes(encoded({'status':'verifying_remote','complete_parts':i+1,'parts':len(value['parts']),'started':started}))
        finally:
            if sink:sink.close()
        if h.hexdigest()!=lock['archive_sha256']:raise ValueError('Complete remote archive checksum mismatch')
        result={'status':'remote_archive_verified','archive_sha256':h.hexdigest(),'bytes':value['archive_bytes'],'parts':len(value['parts']),'duration_seconds':time.time()-started,'verify_only':verify_only}
        if not verify_only:
            partial.rename(destination);metadata=destination.with_suffix(destination.suffix+'.json');metadata.write_bytes(encoded({'image_id':lock['image_id'],'archive_sha256':lock['archive_sha256']}));result['restored_image']=toolchain.restore_archive(destination,metadata)
        Path(output).write_bytes(encoded(result));return result

if __name__=='__main__':
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='operation',required=True)
    a=sub.add_parser('publish');a.add_argument('--archive',required=True);a.add_argument('--output',required=True)
    a=sub.add_parser('recover');a.add_argument('--output',required=True);a.add_argument('--archive');a.add_argument('--verify-only',action='store_true')
    a=p.parse_args();print(json.dumps(publish(a.archive,a.output) if a.operation=='publish' else recover(a.output,a.verify_only,a.archive),indent=2))
