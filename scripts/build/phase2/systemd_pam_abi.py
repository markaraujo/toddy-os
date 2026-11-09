"""Compare the existing same-version private dynamic symbol surface before update."""
import hashlib,json,subprocess
from pathlib import Path
TARGET=Path('/mnt/lfs');WORK=TARGET/'sources/phase2/work/systemd-pam-1'
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def exported(path):
    text=subprocess.check_output(['chroot',str(TARGET),'readelf','--wide','--dyn-syms','/'+str(path.relative_to(TARGET))],text=True)
    result={}
    for line in text.splitlines():
        bits=line.split()
        if len(bits)<8 or not bits[0].rstrip(':').isdigit():continue
        _,value,size,kind,binding,visibility,index,name=bits[:8]
        if index=='UND' or binding not in ['GLOBAL','WEAK'] or visibility not in ['DEFAULT','PROTECTED']:continue
        item={'type':kind,'binding':binding,'visibility':visibility}
        if kind in ['OBJECT','TLS']:item['size']=int(size)
        assert name not in result,name
        result[name]=item
    assert result;return result

def compare():
    rows=[]
    for name in ['libsystemd-core-261.so','libsystemd-shared-261.so']:
        old=TARGET/'usr/lib/systemd'/name;new=WORK/'stage/usr/lib/systemd'/name
        baseline=exported(old);candidate=exported(new)
        missing=sorted(set(baseline)-set(candidate));changed={n:{'old':baseline[n],'new':candidate[n]} for n in baseline.keys()&candidate.keys() if baseline[n]!=candidate[n]}
        rows.append({'path':'/usr/lib/systemd/'+name,'installed_sha256':digest(old),'staged_sha256':digest(new),'existing_dynamic_exports':len(baseline),'candidate_dynamic_exports':len(candidate),'missing':missing,'changed_type_binding_visibility_or_object_size':changed,'added':sorted(set(candidate)-set(baseline))})
    return {'scope':'Same-version private ELF exported symbol/type/binding/visibility/object-size comparison only; no claim of complete semantic ABI or boot/session validation','libraries':rows,'accepted_existing_export_surface':all(not r['missing'] and not r['changed_type_binding_visibility_or_object_size'] for r in rows)}
if __name__=='__main__':
    result=compare();print(json.dumps(result,indent=2));assert result['accepted_existing_export_surface']
