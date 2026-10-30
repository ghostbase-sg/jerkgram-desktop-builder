#!/usr/bin/env python3
"""Explicit dev-fast/production routing. Production never runs by default."""
import argparse,collections,hashlib,json,os,re,shlex,shutil,subprocess,threading,time
from pathlib import Path
import identity,release

ROOT=Path(__file__).resolve().parents[1]

def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def load():
    value=json.loads((ROOT/'BUILD_PROFILES.json').read_text());prod=json.loads((ROOT/'D1_CONFIG.json').read_text())
    if value['schema']!=1 or value['dev-fast']['lto'] or not value['production']['lto']:raise ValueError('Invalid profile policy')
    if value['production']['link_flags']!=prod['release_link_flags'] or value['production']['cmake']!=prod['cmake']:raise ValueError('Production profile drift')
    if value['dev-fast']['configuration']!='Release' or value['dev-fast']['cmake']['DESKTOP_APP_DISABLE_AUTOUPDATE']!='ON':raise ValueError('Dev must be optimized/updater-disabled')
    return value

def dev_flags(value):
    flags=[x for x in shlex.split(value) if not x.startswith('-flto') and x!='-ffat-lto-objects' and x not in ('-g','-g0','-g1','-g2','-g3')]
    return shlex.join(flags+['-g1','-fno-lto'])

def directory(source,profile):
    source=Path(source).resolve();path=source/load()[profile]['directory']
    for p in (path,*path.parents):
        if p==source:break
        if p.is_symlink():raise ValueError('Build path must not traverse a symlink')
    if not path.resolve().is_relative_to(source/'out'):raise ValueError('Build path escapes out')
    return path

def check_dev_configuration(out):
    out=Path(out);cache=(out/'CMakeCache.txt').read_text()
    for key,value in {'CMAKE_BUILD_TYPE':'Release','DESKTOP_APP_DISABLE_AUTOUPDATE':'ON'}.items():
        if not re.search(r'^'+key+r':[^=]+='+value+'$',cache,re.M):raise ValueError('Required dev configuration missing: '+key)
    graph=(out/'build.ninja').read_text();all_flags=re.findall(r'^  (?:FLAGS|LINK_FLAGS|LINK_LIBRARIES) = (.*)$',graph,re.M)
    if any(re.search(r'(?<!\S)-flto(?:[=\s]|$)|(?<!\S)-ffat-lto-objects',x) for x in all_flags):raise ValueError('Effective dev build still contains LTO')
    edge=re.search(r'^build Jerkgram:.*\n((?:[ \t].*\n|\n)*)',graph,re.M)
    if not edge:raise ValueError('Expected dev Jerkgram target missing')
    flags=edge[1]
    for token in ('-O3','-DNDEBUG','-fno-lto','-fno-use-linker-plugin','-fuse-ld=lld','libQt6Core.a','libQt6Gui.a','libQt6Widgets.a'):
        if token not in flags:raise ValueError('Dev contract missing: '+token)
    return True

def production_resources(memory,swap,free_disk):
    if memory<30*2**30 or memory+swap<44*2**30 or free_disk<80*2**30:
        raise ValueError('Production runner has not met measured memory/swap/disk prerequisites; use a proven larger runner')
    return True

def image_id():
    lock=json.loads((ROOT/'toolchains/lock.json').read_text());wanted=lock['image_id']
    got=subprocess.check_output(['docker','image','inspect','--format={{.Id}}',wanted],text=True).strip()
    if got!=wanted:raise ValueError('Pinned image missing; restore toolchain first')
    return wanted

def verify_source(source,edits=()):
    pin=json.loads((ROOT/'PINNED_UPSTREAM').read_text())['commit']
    if identity.verify(source,pin,ROOT,allow_edits=edits)!='materialized':raise ValueError('Managed materialized source required')

def command(source,operation,jobs=2):
    source=Path(source).resolve();out=directory(source,'dev-fast');image=image_id()
    return ['docker','run','--rm','--name','jerkgram-dev-fast','--user',str(os.getuid()),'--volume',str(source)+':/usr/src/tdesktop:ro','--volume',str(out)+':/usr/src/tdesktop/out/dev-fast','--volume',str(ROOT)+':/opt/jerkgram-builder:ro','--env','PYTHONDONTWRITEBYTECODE=1','--entrypoint','python3',image,'/opt/jerkgram-builder/scripts/container_profile.py',operation,'--jobs',str(jobs)]

def receipt(source,image):
    return {'schema':1,'profile':'dev-fast','configuration':'Release','lto':False,'image_id':image,'profiles_sha256':sha(ROOT/'BUILD_PROFILES.json'),'overlay_sha256':sha(ROOT/'D1_CONFIG.json'),'credential_policy':'reuse configured API inside CMake; never included in logs'}

def configure(source,evidence):
    source=Path(source).resolve();verify_source(source);out=directory(source,'dev-fast');out.mkdir(parents=True,exist_ok=True,mode=0o700)
    cache=source/'out/CMakeCache.txt';before=sha(cache);evidence=Path(evidence);evidence.mkdir(parents=True,exist_ok=True)
    with (evidence/'configure.log').open('w') as log:subprocess.run(command(source,'configure'),stdout=log,stderr=subprocess.STDOUT,check=True)
    check_dev_configuration(out)
    if sha(cache)!=before:raise ValueError('Production cache changed')
    result=receipt(source,image_id());(out/'jerkgram-profile.json').write_text(json.dumps(result,indent=2)+'\n');(evidence/'config-verified.json').write_text(json.dumps(result,indent=2)+'\n');return result

def ninja_snapshot(out):
    path=Path(out)/'.ninja_log'
    return collections.Counter(path.read_text().splitlines()) if path.exists() else collections.Counter()

def ninja_records(out,before):
    path=Path(out)/'.ninja_log'
    if not path.exists():return []
    seen=before.copy();records=[]
    for line in path.read_text().splitlines():
        if seen[line]:seen[line]-=1;continue
        a=line.split('\t')
        if len(a)==5 and a[0].isdigit():records.append({'start_ms':int(a[0]),'end_ms':int(a[1]),'output':a[3]})
    return records

def build(source,evidence,jobs=2,edits=()):
    requested=time.time()
    if not 1<=jobs<=4:raise ValueError('Use 1–4 compile jobs')
    source=Path(source).resolve();verify_source(source,edits);out=directory(source,'dev-fast');check_dev_configuration(out)
    if json.loads((out/'jerkgram-profile.json').read_text())!=receipt(source,image_id()):raise ValueError('Profile changed; explicitly configure before building')
    evidence=Path(evidence).resolve();evidence.mkdir(parents=True,exist_ok=True)
    if (evidence/'build.json').exists():raise ValueError('Use a new evidence directory; old evidence is preserved')
    production={str(p):sha(p) for p in (source/'out/CMakeCache.txt',source/'out/Release/Jerkgram') if p.exists()}
    allocated_before=int(subprocess.check_output(['du','-s','-B1',str(out)],text=True).split()[0])
    checkpoint=ninja_snapshot(out);disk=shutil.disk_usage(source);summary={};stop=threading.Event();thread=threading.Thread(target=release.monitor,args=(stop,evidence/'memory.jsonl',summary),daemon=True);thread.start();start=time.time()
    result={'status':'failed','profile':'dev-fast','lto':False,'compile_jobs':jobs,'started':requested,'preflight_seconds':start-requested,'declared_edits':{p:sha(source/p) for p in edits},'image_id':image_id()}
    try:
        with (evidence/'compile.log').open('w') as f:
            p=subprocess.run(command(source,'build',jobs),stdout=f,stderr=subprocess.STDOUT)
        result['exit_code']=p.returncode
        if p.returncode:raise ValueError('Dev build failed; see redacted compile.log')
        if summary.get('peak_lto_processes',0):raise ValueError('Unexpected LTO process during dev build')
        verify_source(source,edits)
        if any(sha(Path(k))!=v for k,v in production.items()):raise ValueError('Production cache/binary changed')
        binary=out/'Jerkgram';result.update(status='compiled',binary=str(binary),binary_bytes=binary.stat().st_size,binary_sha256=sha(binary),production_preserved=True)
    finally:
        stop.set();thread.join();records=ninja_records(out,checkpoint);compiles=[x for x in records if x['output'].endswith('.o')];links=[x for x in records if x['output']=='Jerkgram']
        text=(evidence/'compile.log').read_text(errors='replace');operations=max([int(x) for x in re.findall(r'\[(\d+)/\d+\]',text)]+[0])
        result.update(duration_seconds=time.time()-requested,ninja_wall_seconds=time.time()-start,finished=time.time(),resources=summary,build_tree_delta_bytes=int(subprocess.check_output(['du','-s','-B1',str(out)],text=True).split()[0])-allocated_before,disk_used_delta_bytes=disk.free-shutil.disk_usage(source).free,operations=operations,outputs_updated=len(records),recompiled=len(compiles),compile_span_seconds=(max(x['end_ms'] for x in compiles)-min(x['start_ms'] for x in compiles))/1000 if compiles else 0,link_seconds=sum((x['end_ms']-x['start_ms'])/1000 for x in links),records=records)
        (evidence/'build.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('operation',choices=('validate','configure','build'));p.add_argument('--source');p.add_argument('--profile',choices=('dev-fast','production'),default='dev-fast');p.add_argument('--evidence');p.add_argument('--jobs',type=int,default=2);p.add_argument('--edit-path',action='append',default=[]);p.add_argument('--execute-production',action='store_true');a=p.parse_args()
    if a.operation=='validate':print(json.dumps(load(),indent=2));return
    if not a.source or not a.evidence:p.error('--source and --evidence are required')
    if a.profile=='production':
        if a.edit_path or not a.execute_production:raise ValueError('Production requires explicit execution and exact verified source')
        if a.operation!='build':raise ValueError('Production configure/build remains the existing explicit Release adapter')
        memory={x.split(':')[0]:int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith(('MemTotal:','SwapTotal:'))}
        production_resources(memory['MemTotal'],memory['SwapTotal'],shutil.disk_usage(a.source).free)
        image=image_id();release.run(a.source,a.evidence,image=image,jobs=a.jobs);return
    result=configure(a.source,a.evidence) if a.operation=='configure' else build(a.source,a.evidence,a.jobs,a.edit_path)
    print(json.dumps({k:v for k,v in result.items() if k!='records'},indent=2))
if __name__=='__main__':main()
