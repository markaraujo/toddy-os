"""Promote the qualified browser stage with owned, pinned runtime providers."""
from pathlib import Path
import hashlib,json,os,re,shutil,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from audit_native_elf import target_resolve
from stage_package import payload
from verify_stage import inspect_stage
from package_copyright import write_copyright
R=Path('/opt/toddy-build');T=Path('/mnt/lfs');L=Path('/var/log/toddy/phase2')
VERSION='153.7.0esr-1+toddy1'
WORK=T/'sources/phase2/work/firefox-security-1537-1'


def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def dependencies(stage):
    # Firefox's dependentlibs.list preloads its private runtime before libxul.
    private=stage/'usr/lib/firefox';bootstrap=[n.strip() for n in (private/'dependentlibs.list').read_text().splitlines() if n.strip()]
    assert bootstrap and all('/' not in n and (private/n).is_file() for n in bootstrap)
    needed=set();elf={}
    for p in stage.rglob('*'):
        if p.is_symlink() or not p.is_file():continue
        with p.open('rb') as f:magic=f.read(4)
        if magic!=b'\x7fELF':continue
        dynamic=subprocess.check_output(['readelf','-d',str(p)],text=True)
        entries=re.findall(r'\((NEEDED|RPATH|RUNPATH)\).*\[(.*?)\]',dynamic)
        # This qualified source emits no runtime search override.
        assert not any(k in ('RPATH','RUNPATH') for k,v in entries),(p,entries)
        names=[v for k,v in entries if k=='NEEDED'];assert all('/' not in n for n in names)
        needed.update(names);elf[str(p.relative_to(stage))]=names
    owners={};providers={};private_needed=[]
    for name in sorted(needed):
        if (private/name).is_file():private_needed.append(name);continue
        resolved=None
        for prefix in ['/usr/lib/','/lib/','/lib64/']:
            p,virtual=target_resolve(T,prefix+name)
            if p.is_file():resolved=(p,virtual);break
        assert resolved,('Native provider absent',name)
        p,virtual=resolved
        output=subprocess.check_output(['chroot',str(T),'dpkg-query','-S',virtual],text=True).splitlines()
        candidates={line.split(': ',1)[0].split(':',1)[0] for line in output}
        assert len(candidates)==1,(name,candidates)
        owner=candidates.pop();version=subprocess.check_output(['chroot',str(T),'dpkg-query','-W','-f=${Version}',owner],text=True)
        record=Path('/var/log/toddy/packages')/(owner+'_'+version+'_amd64.json')
        if not record.exists():record=record.with_name(owner+'_'+version+'_all.json')
        r=json.loads(record.read_text());assert r['installed'] and digest(p)==r['payload'][virtual]['sha256']
        owners[owner]=version;providers[name]={'path':virtual,'owner':owner,'version':version,'sha256':digest(p)}
    # Runtime-loaded audio, public trust and default readable fonts are explicit.
    for owner in ['pulseaudio','p11-kit','ca-certificates','adwaita-fonts']:
        version=subprocess.check_output(['chroot',str(T),'dpkg-query','-W','-f=${Version}',owner],text=True)
        assert subprocess.check_output(['chroot',str(T),'dpkg-query','-W','-f=${Status}',owner],text=True)=='install ok installed'
        owners[owner]=version
    return ', '.join(n+' (= '+v+')' for n,v in sorted(owners.items())),{'elf':elf,'providers':providers,'private_needed':private_needed,'bootstrap_preloads':bootstrap,'runtime_packages':owners}


def main():
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    proof=json.loads((L/'firefox-security-stage-controller-1.json').read_text());assert proof['exit']==0
    result=json.loads((WORK/'firefox-stage-result.json').read_text());assert result['state']=='staged'
    source=WORK/'stage';assert inspect_stage(source)['manifest_sha256']==proof['stage_manifest_sha256']
    receipt=L/'firefox-package-install-1.json';stage=T/'sources/stage/phase2-firefox-security-1'
    assert not receipt.exists() and not stage.exists()
    assert subprocess.run(['chroot',str(T),'dpkg-query','-W','-f=${Status}','firefox'],capture_output=True).returncode==1
    assert not any(os.path.lexists(T/n) for n in ['usr/lib/firefox','usr/bin/firefox','usr/share/applications/firefox.desktop'])
    depends,audit=dependencies(source)
    stage.mkdir();subprocess.run(['mount','--bind',str(source),str(stage)],check=True)
    write_copyright(stage,'firefox',['firefox-153.7.0esr.source.tar.xz'])
    size=sum(p.stat().st_size for p in stage.rglob('*') if p.is_file() and not p.is_symlink())
    assert shutil.disk_usage(T).free>=16*1024**3+size+64*1024**2
    data={'state':'installing','version':VERSION,'depends':depends,'dependency_audit':audit,'stage_before_packaging':inspect_stage(stage)['manifest_sha256'],
          'scope':'Owned source-built browser installation/ABI dependency provenance only; actual normal-user runtime/sandbox/GUI gates pending'}
    def save():receipt.write_text(json.dumps(data,indent=2)+'\n')
    save()
    subprocess.run([sys.executable,str(R/'scripts/build/stage_package.py'),'firefox',VERSION,str(stage),'--source','firefox-153.7.0esr.source.tar.xz',
        '--recipe','scripts/build/phase2/firefox-install.sh','--depends',depends,'--install'],cwd=R,check=True)
    record=json.loads(Path('/var/log/toddy/packages','firefox_'+VERSION+'_amd64.json').read_text());assert record['installed']
    assert payload(stage)==record['payload']
    data.update(state='complete',archive_sha256=record['archive_sha256'],payload_entries=len(record['payload']),stage_bytes=size);save();print(json.dumps(data))


if __name__=='__main__':main()
