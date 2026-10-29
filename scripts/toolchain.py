#!/usr/bin/env python3
"""Pinned upstream toolchain recovery. Never mounts product source into an image build."""
import argparse,contextlib,hashlib,json,os,re,shutil,subprocess,sys,tarfile,tempfile,threading,time,zlib
from pathlib import PurePosixPath
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RECIPE=ROOT/'toolchains/recipe.json'

def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def verify_inputs(source,recipe):
    source=Path(source).resolve()
    for name,digest in recipe['inputs'].items():
        p=source/name
        if p.is_symlink() or not p.resolve().is_relative_to(source) or sha(p)!=digest:raise ValueError('Toolchain input drift: '+name)
        if p.name=='Dockerfile':
            for line in p.read_text().splitlines():
                if re.match(r'\s*(COPY|ADD)\s',line,re.I) and not re.match(r'\s*COPY\s+(?:--link\s+)?--from=',line,re.I):
                    raise ValueError('Local or external context input forbidden')

def epel_https(data):
    anchor=b'dnf config-manager --set-enabled powertools'
    if data.count(anchor)!=1:raise ValueError('Upstream DNF anchor changed')
    override=b"dnf config-manager --save --setopt=epel.metalink= --setopt='epel.baseurl=https://dl.fedoraproject.org/pub/epel/$releasever/Everything/$basearch/'"
    first=b'dnf -y install epel-release'
    if data.count(first)!=1:raise ValueError('Upstream initial DNF anchor changed')
    guard=b'if [ -f /var/cache/dnf/metadata_lock.pid ] && [ "$(cat /var/cache/dnf/metadata_lock.pid)" = 1 ] && [ "$(cat /proc/1/comm)" = bash ]; then rm /var/cache/dnf/metadata_lock.pid; fi'
    return data.replace(first,guard+b'\n'+first).replace(anchor,override+b'\n'+anchor)

def render(source,recipe,python):
    verify_inputs(source,recipe)
    if subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()!=recipe['upstream_commit']:
        raise ValueError('Toolchain source does not match upstream pin')
    env=dict(os.environ,**recipe['render_env'],PYTHONDONTWRITEBYTECODE='1')
    version=subprocess.check_output([python,'-c','import jinja2;print(jinja2.__version__)'],env=env,text=True).strip()
    if version!='3.1.6':raise ValueError('Use upstream-locked Jinja2 3.1.6')
    data=subprocess.check_output([python,str(Path(source)/recipe['generator'])],env=env)
    if recipe.get('epel_https'):data=epel_https(data)
    if b'{%' in data or b'{{' in data:raise ValueError('Unrendered toolchain template')
    return data

def inspect(image):
    data=json.loads(subprocess.check_output(['docker','image','inspect',image]))[0]
    env=data['Config'].get('Env',[])
    if any(re.search(r'(SECRET|TOKEN|PASSWORD|TDESKTOP_API)',x.split('=',1)[0],re.I) for x in env):
        raise ValueError('Unexpected sensitive image environment key')
    command='''python3 - <<'CHECK'
import json,subprocess,os,pathlib
commands={'gcc':['g++','-dumpfullversion','-dumpversion'],'compiler':['g++','--version'],'cmake':['cmake','--version'],'ninja':['ninja','--version'],'qt':['pkg-config','--modversion','Qt6Core'],'lld':['ld.lld','--version']}
r={k:subprocess.check_output(v,text=True).splitlines()[0] for k,v in commands.items()}
r['flags']={k:os.environ.get(k) for k in ('CC','CXX','CFLAGS','CXXFLAGS','LDFLAGS','AR','RANLIB')}
r['source_mount_empty']=not any(pathlib.Path('/usr/src/tdesktop').iterdir())
print(json.dumps(r))
CHECK'''
    versions=json.loads(subprocess.check_output(['docker','run','--rm','--entrypoint','bash',image,'-c',command]))
    if not versions['source_mount_empty']:raise ValueError('Toolchain contains product source/output')
    return {'image_id':data['Id'],'size_bytes':data['Size'],'repo_digests':data.get('RepoDigests',[]),'versions':versions}

def compatible(info,recipe):
    for key,value in recipe['expected_compatibility'].items():
        if info['versions'].get(key)!=value:raise ValueError('Recovered toolchain differs from measured D1B '+key)
    return True

def probe(image,source,output):
    info=inspect(image);compatible(info,json.loads(RECIPE.read_text()))
    source=Path(source).resolve();objects=list((source/'out/Telegram/CMakeFiles').glob('Telegram.dir/Release/SourceFiles/intro/intro_start.cpp.o'))
    if len(objects)!=1:raise ValueError('Expected preserved production object for native fallback probe')
    obj=objects[0];before=sha(obj)
    command='''set -euo pipefail
cd "$(mktemp -d /tmp/jerkgram-compat-XXXXXX)"
printf '#include <QtCore/QCoreApplication>\\n#include <QtCore/QLibraryInfo>\\n#include <cstdio>\\nint main(int argc,char **argv){QCoreApplication a(argc,argv); std::puts(qVersion()); return 0;}\\n' > probe.cpp
g++ -std=c++20 -O2 -fPIC -fno-lto -fno-use-linker-plugin -fuse-ld=lld -static-libstdc++ -static-libgcc probe.cpp $(pkg-config --cflags --libs Qt6Core) -o probe
./probe
file probe
g++ -nostdlib -no-pie -fno-lto -fno-use-linker-plugin -fuse-ld=lld -Wl,-r /probe/old.o -o native-fallback.o
file native-fallback.o
'''
    start=time.time();p=subprocess.run(['docker','run','--rm','--volume',str(obj)+':/probe/old.o:ro','--entrypoint','bash',image,'-c',command],capture_output=True,text=True)
    report={'image':info,'duration_seconds':time.time()-start,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'old_object_sha256':before,'old_object_preserved':sha(obj)==before,'scope':'tiny Qt6Core native executable and partial native link of one preserved fat-LTO object; no production target build'}
    Path(output).write_text(json.dumps(report,indent=2)+'\n')
    if p.returncode or not report['old_object_preserved']:raise ValueError('Compatibility probe failed; inspect saved output')
    return report

def rebuild(source,evidence,python,execute=False):
    source,evidence=Path(source).resolve(),Path(evidence).resolve();evidence.mkdir(parents=True,exist_ok=True)
    recipe=json.loads(RECIPE.read_text());data=render(source,recipe,python)
    (evidence/'Dockerfile.rendered').write_bytes(data)
    report={'status':'rendered','recipe_sha256':sha(RECIPE),'rendered_sha256':sha(evidence/'Dockerfile.rendered'),'upstream_commit':recipe['upstream_commit'],'render_env':recipe['render_env'],'source_inputs':recipe['inputs']}
    if not execute:
        (evidence/'restore.json').write_text(json.dumps(report,indent=2)+'\n');return report
    from release import monitor
    start=time.time();disk=shutil.disk_usage(source);summary={};stop=threading.Event();thread=threading.Thread(target=monitor,args=(stop,evidence/'memory.jsonl',summary),daemon=True);thread.start()
    try:
        builder='jerkgram-toolchain'
        check=subprocess.run(['docker','buildx','inspect',builder],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        if check.returncode:
            subprocess.run(['docker','buildx','create','--name',builder,'--driver','docker-container','--buildkitd-config',str(ROOT/'toolchains/buildkitd.toml'),'--driver-opt','memory=24g','--bootstrap'],check=True)
        with tempfile.TemporaryDirectory(prefix='jerkgram-toolchain-context-') as tmp:
            p=Path(tmp);(p/'Dockerfile').write_bytes(data)
            subprocess.run(['docker','buildx','build','--builder',builder,'--load','--progress=plain','--tag','tdesktop:centos_env','--label','org.opencontainers.image.source=https://github.com/ghostbase-sg/jerkgram-desktop-builder','--label','org.opencontainers.image.revision='+recipe['upstream_commit'],str(p)],check=True)
        report.update(status='restored',**inspect('tdesktop:centos_env'))
    except Exception as exc:
        report.update(status='failed',error=str(exc));raise
    finally:
        stop.set();thread.join();report.update(started=start,finished=time.time(),duration_seconds=time.time()-start,resources=summary,disk_used_delta_bytes=disk.free-shutil.disk_usage(source).free)
        (evidence/'restore.json').write_text(json.dumps(report,indent=2)+'\n')
    return report

def verify_save(stream,expected):
    # Docker 29/containerd image IDs can name an OCI index, not its native config.
    digests={};diffs={};metadata={};metadata_bytes=0
    with tarfile.open(fileobj=stream,mode='r|*') as archive:
        for item in archive:
            path=PurePosixPath(item.name)
            if path.is_absolute() or '..' in path.parts or item.issym() or item.islnk():raise ValueError('Unsafe outer image archive member')
            if item.isdir():continue
            if not item.isfile():raise ValueError('Unexpected outer image archive member')
            file=archive.extractfile(item);h=hashlib.sha256();native=hashlib.sha256();chunks=[];decoder=None;first=True;save=False
            while chunk:=file.read(1024**2):
                if first:
                    save=item.name=='manifest.json' or (item.size<=2*1024**2 and chunk.lstrip().startswith(b'{'))
                    if chunk.startswith(b'\x1f\x8b'):decoder=zlib.decompressobj(16+zlib.MAX_WBITS)
                    first=False
                h.update(chunk)
                if save:
                    metadata_bytes+=len(chunk)
                    if metadata_bytes>32*1024**2:raise ValueError('Oversized image metadata')
                    chunks.append(chunk)
                if decoder:
                    tail=chunk
                    while True:
                        data=decoder.decompress(tail,4*1024**2);native.update(data);tail=decoder.unconsumed_tail
                        if not tail and len(data)<4*1024**2:break
                else:native.update(chunk)
            if decoder and not decoder.eof:raise ValueError('Truncated compressed image blob')
            digests[item.name]=h.hexdigest();diffs[item.name]=native.hexdigest()
            if item.name.startswith('blobs/sha256/') and item.name.rsplit('/',1)[1]!=h.hexdigest():raise ValueError('OCI blob digest mismatch')
            if save:metadata[item.name]=b''.join(chunks)
    manifest=json.loads(metadata['manifest.json'])
    if len(manifest)!=1:raise ValueError('Expected exactly one native toolchain image')
    image=manifest[0];config_path=image['Config'];config_digest='sha256:'+digests[config_path]
    config=json.loads(metadata[config_path]);layers=image['Layers'];wanted=config['rootfs']['diff_ids']
    if config_digest!=expected:
        def native_manifest(digest,depth=0):
            if depth>4:raise ValueError('Nested OCI index exceeds limit')
            name='blobs/sha256/'+digest.removeprefix('sha256:')
            if 'sha256:'+digests.get(name,'')!=digest:raise ValueError('Missing OCI identity blob')
            node=json.loads(metadata[name])
            if 'config' in node:
                if node['config']['digest']!=config_digest:raise ValueError('Wrong native config in OCI index')
                return node
            candidates=[x for x in node.get('manifests',[]) if x.get('platform',{}).get('os')=='linux' and x.get('platform',{}).get('architecture')=='amd64']
            if len(candidates)!=1:raise ValueError('Expected one Linux amd64 OCI child')
            return native_manifest(candidates[0]['digest'],depth+1)
        node=native_manifest(expected)
        for entry in node['layers']:
            digest=entry['digest']
            if 'sha256:'+digests.get('blobs/sha256/'+digest[7:],'')!=digest:raise ValueError('Missing native OCI layer')
    if len(layers)!=len(wanted) or not layers:raise ValueError('Missing image layers')
    for name,digest in zip(layers,wanted):
        if 'sha256:'+diffs.get(name,'')!=digest:raise ValueError('Missing/tampered native image layer: '+name)
    return {'image_id':expected,'config_digest':config_digest,'layers':len(layers),'complete':True,'platform':'linux/amd64'}

def archive_verify(path,expected):
    p=subprocess.Popen(['zstd','--decompress','--stdout',str(path)],stdout=subprocess.PIPE)
    try:result=verify_save(p.stdout,expected)
    finally:
        p.stdout.close();code=p.wait()
    if code:raise ValueError('Archive decompression failed')
    return result

def backup(image,output):
    image_info=inspect(image);expected=image_info['image_id'];output=Path(output).resolve()
    if output.is_relative_to(ROOT) or output.exists():raise ValueError('Use a new backup path outside builder')
    output.parent.mkdir(parents=True,exist_ok=True,mode=0o700);partial=output.with_name(output.name+'.partial')
    if partial.exists():raise ValueError('Partial backup already exists; preserve/inspect it')
    start=time.time();producer=subprocess.Popen(['docker','image','save',expected],stdout=subprocess.PIPE)
    try:
        consumer=subprocess.run(['zstd','-T2','-3','--quiet','-o',str(partial)],stdin=producer.stdout)
    finally:producer.stdout.close();status=producer.wait()
    if status or consumer.returncode:raise ValueError('Toolchain archive pipeline failed')
    checked=archive_verify(partial,expected);partial.rename(output)
    report={'schema':1,'archive_name':output.name,'archive_bytes':output.stat().st_size,'archive_sha256':sha(output),'image_id':expected,'image':image_info,'verification':checked,'duration_seconds':time.time()-start}
    output.with_suffix(output.suffix+'.json').write_text(json.dumps(report,indent=2)+'\n');return report

def restore_archive(path,metadata):
    path=Path(path).resolve();meta=json.loads(Path(metadata).read_text());expected=meta['image_id']
    if sha(path)!=meta['archive_sha256']:raise ValueError('Backup checksum mismatch')
    archive_verify(path,expected)
    p=subprocess.Popen(['zstd','--decompress','--stdout',str(path)],stdout=subprocess.PIPE)
    try:q=subprocess.run(['docker','image','load'],stdin=p.stdout)
    finally:p.stdout.close();status=p.wait()
    if status or q.returncode:raise ValueError('Docker image restore failed')
    result=inspect(expected)
    if result['image_id']!=expected:raise ValueError('Restored wrong image')
    subprocess.run(['docker','tag',expected,'tdesktop:centos_env'],check=True);return result

@contextlib.contextmanager
def registry_environment():
    with tempfile.TemporaryDirectory(prefix='jerkgram-registry-auth-') as tmp:
        env=dict(os.environ,DOCKER_CONFIG=tmp)
        token=os.environ.get('GHCR_TOKEN','')
        if token:
            p=subprocess.run(['docker','login','ghcr.io','--username','ghostbase-sg','--password-stdin'],input=token,text=True,env=env,capture_output=True)
            if p.returncode:raise ValueError('Registry login failed; token value omitted')
        yield env

def remote_manifest(reference,env):
    value=json.loads(subprocess.check_output(['docker','buildx','imagetools','inspect','--raw',reference],env=env))
    if 'manifests' in value:
        entry=next(x for x in value['manifests'] if x.get('platform',{}).get('os')=='linux' and x.get('platform',{}).get('architecture')=='amd64')
        repository=reference.split('@')[0].rsplit(':',1)[0] if '@' not in reference else reference.split('@')[0]
        return remote_manifest(repository+'@'+entry['digest'],env)
    return value

def publish(output):
    if os.environ.get('GITHUB_EVENT_NAME')!='workflow_dispatch' or os.environ.get('GITHUB_REPOSITORY')!='ghostbase-sg/jerkgram-desktop-builder' or os.environ.get('GITHUB_ACTOR')!='ghostbase-sg':
        raise ValueError('Publish only from the trusted explicit Actions workflow')
    lock=json.loads((ROOT/'toolchains/lock.json').read_text());expected=lock['image_id'];info=inspect(expected)
    tag='ghcr.io/ghostbase-sg/jerkgram-desktop-toolchain:v7.3.1-prod-'+expected[7:19]
    with registry_environment() as env:
        previous=subprocess.run(['docker','buildx','imagetools','inspect','--raw',tag],env=env,capture_output=True)
        if previous.returncode==0:
            if remote_manifest(tag,env)['config']['digest']!=lock['config_digest']:raise ValueError('Versioned registry tag already names another image')
        subprocess.run(['docker','tag',expected,tag],check=True)
        subprocess.run(['docker','push',tag],env=env,check=True)
        digests=json.loads(subprocess.check_output(['docker','image','inspect','--format={{json .RepoDigests}}',expected]))
        reference=next(x for x in digests if x.startswith('ghcr.io/ghostbase-sg/jerkgram-desktop-toolchain@'))
        remote=remote_manifest(reference,env)
        if remote['config']['digest']!=lock['config_digest']:raise ValueError('Published registry config differs')
    result={'image_id':expected,'version_tag':tag,'registry_reference':reference,'largest_layer_bytes':max(x['size'] for x in remote['layers']),'compressed_layer_bytes':sum(x['size'] for x in remote['layers']),'layers':len(remote['layers']),'image':info}
    Path(output).write_text(json.dumps(result,indent=2)+'\n');return result

def restore_registry(verify_remote=False):
    lock=json.loads((ROOT/'toolchains/lock.json').read_text());expected=lock['image_id']
    if not verify_remote and subprocess.run(['docker','image','inspect',expected],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0:
        return {'status':'already_cached','image_id':expected}
    reference=lock.get('registry_reference','')
    if not re.fullmatch(r'ghcr\.io/ghostbase-sg/jerkgram-desktop-toolchain@sha256:[0-9a-f]{64}',reference):raise ValueError('No verified pinned registry recovery reference')
    with registry_environment() as env:
        remote=remote_manifest(reference,env)
        if remote['config']['digest']!=lock['config_digest']:raise ValueError('Remote image identity mismatch')
        subprocess.run(['docker','pull','--platform','linux/amd64',reference],env=env,check=True)
    result=inspect(expected)
    if result['image_id']!=expected:raise ValueError('Pulled wrong image')
    subprocess.run(['docker','tag',expected,'tdesktop:centos_env'],check=True);result.update(status='remote_digest_pulled_and_verified',registry_reference=reference);return result

def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='operation',required=True)
    b=sub.add_parser('rebuild');b.add_argument('--source',required=True);b.add_argument('--evidence',required=True);b.add_argument('--renderer-python',default=sys.executable);b.add_argument('--execute',action='store_true')
    i=sub.add_parser('inspect');i.add_argument('--image',default='tdesktop:centos_env')
    a=sub.add_parser('backup');a.add_argument('--image',default='tdesktop:centos_env');a.add_argument('--output',required=True)
    a=sub.add_parser('restore-archive');a.add_argument('--archive',required=True);a.add_argument('--metadata',required=True)
    a=sub.add_parser('probe');a.add_argument('--image',default='tdesktop:centos_env');a.add_argument('--source',required=True);a.add_argument('--output',required=True)
    a=sub.add_parser('publish');a.add_argument('--output',required=True)
    a=sub.add_parser('restore-registry');a.add_argument('--output');a.add_argument('--verify-remote',action='store_true')
    a=p.parse_args()
    if a.operation=='probe':result=probe(a.image,a.source,a.output)
    elif a.operation=='publish':result=publish(a.output)
    elif a.operation=='restore-registry':result=restore_registry(a.verify_remote)
    elif a.operation=='inspect':result=inspect(a.image)
    elif a.operation=='backup':result=backup(a.image,a.output)
    elif a.operation=='restore-archive':result=restore_archive(a.archive,a.metadata)
    else:result=rebuild(a.source,a.evidence,a.renderer_python,a.execute)
    if a.operation=='restore-registry' and a.output:Path(a.output).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
