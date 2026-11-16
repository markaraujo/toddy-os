#!/usr/bin/env python3
"""Fixed image input preparation from real signed archives, never image acceptance."""
import hashlib,json,os,re,stat,subprocess,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path[:0]=[str(HERE),str(ROOT)]
import offline_payload as p
from image_media import inherited_media_lease
from runtime.installer.native_finalizer import account_files,cache_command
from runtime.installer.installed_boot import module_namespace,InstalledBoot,RELEASE
from runtime.installer.composition import secured,validate_policy
TARGET=Path('/mnt/lfs');STAGE=TARGET/'sources/stage'
PROJECTION=STAGE/'toddy-image-projection-2'
EXPORT=STAGE/'toddy-package-export-2'
MVP_EXPORT=STAGE/'toddy-package-export-3'

def signed_export(kind):
    if kind not in ('base','live','mvp-base','mvp-live'):raise ValueError('Fixed image delivery profile required')
    return MVP_EXPORT if kind.startswith('mvp-') else EXPORT
RECORDS=Path('/var/log/toddy/packages');ARCHIVES=Path('/var/cache/toddy/packages')
OUTPUT={'base':STAGE/'toddy-installer-native-inputs','live':STAGE/'toddy-live-native-inputs',
        'mvp-base':STAGE/'toddy-mvp-installer-native-inputs','mvp-live':STAGE/'toddy-mvp-live-native-inputs'}
MVP_CLASS='phase2-mvp-preinstalled-v1'
EPOCH=1794787200
DENIED={'lfs','tester','builder','toddy','toddy-live','toddy-build','toddybuild'}

def selection(kind):
    if kind not in OUTPUT:raise ValueError('Fixed base/live input profile required')
    mvp=kind.startswith('mvp-');base_kind=kind.removeprefix('mvp-')
    directory=STAGE/'toddy-mvp-image-projection-1' if mvp else PROJECTION
    profile=directory/('profile.json' if base_kind=='base' else 'live-profile.json')
    policy=p.strict(secured(profile).read_bytes())
    if mvp:
        if p.delivery_policy(policy)[0]!=MVP_CLASS:raise ValueError('MVP profile delivery class required')
    elif policy.get('delivery_class')==MVP_CLASS:raise ValueError('MVP cannot enter standard image inputs')
    projection=directory/('projection.json' if base_kind=='base' else 'live-projection.json')
    doc=p.strict(secured(projection).read_bytes())
    additions=p.strict(secured(directory/'additional-components.json').read_bytes()) if base_kind=='base' else []
    components=[*doc['components'],*additions]
    if len({row['name'] for row in components})!=len(components):raise ValueError('Image input duplicate component')
    return profile,projection,additions,components

def records_for(components):
    records=[];pins={}
    for row in components:
        stem=row['name']+'_'+row['version']+'_'+row['architecture']
        path=secured(RECORDS/(stem+'.json'));record=p.strict(path.read_bytes())
        if p.digest(path)!=row['component_record_sha256'] or record.get('installed') is not True or record.get('archive_sha256')!=row['archive_sha256']:
            raise ValueError('Image input native record differs')
        records.append(record);pins[stem+'.json']=p.digest(path)
    return records,pins

def cache_tool(path,entries):
    # Only executable paths already owned by the selected archive closure may
    # select the existing fixed native cache argv vocabulary.
    candidates=('/usr/bin/glib-compile-schemas','/usr/bin/gtk4-update-icon-cache','/usr/bin/gtk-update-icon-cache',
      '/usr/bin/update-mime-database','/usr/bin/gio-querymodules','/usr/bin/systemd-hwdb','/usr/bin/dconf',
      '/usr/sbin/depmod','/usr/bin/gdk-pixbuf-query-loaders','/usr/lib/gdk-pixbuf-2.0/gdk-pixbuf-query-loaders',
      '/usr/bin/gtk-query-immodules-3.0','/usr/bin/gtk-query-immodules-2.0')
    for tool in candidates:
        if not entries.get(tool,{}).get('sha256'):continue
        try:cache_command(path,tool)
        except ValueError:continue
        return {'path':tool,'sha256':entries[tool]['sha256']}
    raise ValueError('Selected owned native cache tool unavailable: '+path)

def cache_bindings(records,pins):
    entries=p.inventory(records)['entries'];bindings={};evidence={}
    for path,row in sorted(entries.items()):
        if not row.get('sha256') or not p.generated_artifact(path):continue
        owners=[record for record in records if record.get('payload',{}).get(path.lstrip('/'),{}).get('sha256')==row['sha256'] or record.get('payload',{}).get(path,{}).get('sha256')==row['sha256']]
        if not owners:raise ValueError('Archived native generated output has no record: '+path)
        namespace=p.cache_namespace(path,entries);tool=cache_tool(path,entries)
        proof={'version':1,'scope':'archived-native-output-provenance-needs-selected-union-regeneration',
            'output':path,'output_sha256':row['sha256'],'tool':tool,'native_record_sha256':pins,
            'selected_namespace_sha256':hashlib.sha256(p.encoded(namespace)).hexdigest(),
            'regeneration_passed':False,'finalizer_passed':False}
        evidence[path]=proof
        bindings[path]={'output_sha256':row['sha256'],'tool':tool,
            'inputs':{name:item['sha256'] for name,item in namespace.items() if 'sha256' in item},
            'input_namespace_sha256':proof['selected_namespace_sha256'],
            'native_evidence_sha256':hashlib.sha256(p.encoded(proof)).hexdigest()}
    p.validate_generated(records,entries,bindings)
    return entries,bindings,evidence

def account_policy(passwd,group,entries):
    """Fresh locked service baseline only; never copy shadow or owner membership."""
    users=[];groups=[]
    for line in passwd.splitlines():
        row=line.split(':')
        if len(row)!=7 or not row[2].isdigit():raise ValueError('Malformed native account inventory')
        if row[0]=='root':continue
        if row[0] in DENIED or not (1<=int(row[2])<1000 or int(row[2])==65534):continue
        if row[6] not in ('/usr/bin/false','/bin/false','/usr/sbin/nologin'):continue
        users.append(row)
    for line in group.splitlines():
        row=line.split(':')
        if len(row)!=4 or not row[2].isdigit():raise ValueError('Malformed native group inventory')
        if row[0] in DENIED or row[0] in ('root','wheel') or not (1<=int(row[2])<1000 or int(row[2])==65534):continue
        groups.append([row[0],'x',row[2],''])
    account={'passwd':'root:x:0:0:root:/root:/bin/bash\n'+''.join(':'.join([row[0],'x',*row[2:]])+'\n' for row in sorted(users,key=lambda row:int(row[2]))),
        'group':'root:x:0:\nwheel:x:97:\n'+''.join(':'.join(row)+'\n' for row in sorted(groups,key=lambda row:int(row[2])))}
    account_files(account)
    paths=sorted(path for path,row in entries.items() if row.get('sha256') and (path.startswith('/etc/pam.d/') or path in ('/usr/lib/systemd/system/gdm.service','/usr/lib/systemd/system/NetworkManager.service','/usr/lib/systemd/system/systemd-logind.service','/usr/lib/systemd/system/dbus.service')))
    if '/etc/pam.d/gdm-password' not in paths or '/usr/lib/systemd/system/gdm.service' not in paths:raise ValueError('Selected GNOME PAM/service policy unavailable')
    policy={'accounts':account,'required_policy_paths':paths};validate_policy(policy,{'ownership':{'entries':entries}})
    return policy

def boot_profile(entries):
    _,namespace=module_namespace(entries)
    kernel=entries.get('/boot/vmlinuz-'+RELEASE,{}).get('sha256')
    if not kernel:raise ValueError('Selected owned kernel unavailable')
    return {'kernel_sha256':kernel,'module_namespace_sha256':namespace,
        'modules':['virtio_pci','virtio_blk','ext4'],'epoch':EPOCH}

def write(path,value):
    with path.open('xb') as stream:
        os.fchmod(stream.fileno(),0o600);stream.write(p.encoded(value));stream.flush();os.fsync(stream.fileno())

def prepare(kind):
    profile,projection,additions,components=selection(kind)
    records,pins=records_for(components);entries,bindings,evidence=cache_bindings(records,pins)
    policy=account_policy(secured(TARGET/'etc/passwd').read_text(),secured(TARGET/'etc/group').read_text(),entries)
    boot=boot_profile(entries);InstalledBoot(Path('/'),{'ownership':{'entries':entries}},boot,None)
    trustpins=p.strict(secured(ROOT/'config/phase2/archive-public-trust.json').read_bytes())
    export=signed_export(kind)
    trust=p.ReleaseTrust(keyring=secured(ROOT/'config/phase2/archive-public-key.gpg'),expected_key_sha256=trustpins['public_keyring_sha256'],
        release=secured(export/'Release'),signature=secured(export/'Release.gpg'),packages=secured(export/'Packages'),index_path='Packages')
    # Verify actual signature/package identity before creating an input namespace.
    trust.verify([dict(row,archive=row['name']+'_'+row['version']+'_'+row['architecture']+'.deb',archive_bytes=secured(ARCHIVES/(row['name']+'_'+row['version']+'_'+row['architecture']+'.deb'),limit=8*1024**3).stat().st_size) for row in components])
    output=OUTPUT[kind]
    if os.path.lexists(output):raise ValueError('Image input namespace exists; preserve and reconcile, no replay')
    output.mkdir(mode=0o700)
    write(output/'input-intent.json',{'version':1,'state':'native-image-input-preparation-intended','kind':kind,'producer_sha256':p.digest(Path(__file__))})
    write(output/'generated-bindings.json',bindings);write(output/'archived-cache-evidence.json',evidence)
    write(output/'policy.json',policy);write(output/'boot-profile.json',boot)
    manifest=p.prepare(profile_path=profile,projection_path=projection,records_directory=RECORDS,archive_directory=ARCHIVES,
        catalog_path=ROOT/'config/phase2/software-catalog.json',destination=output/'payload',trust=trust,generated_bindings=bindings,
        additional_components=additions,required_additions=p.MANDATORY_ADDITIONS if kind.removeprefix('mvp-')=='base' else ())
    write(output/'input-prepared.json',{'version':1,'state':'signed-native-image-inputs-prepared-needs-resource-regeneration',
        'payload_manifest_sha256':p.digest(output/'payload/manifest.json'),'kind':kind,'native_record_sha256':pins,
        'regeneration_passed':False,'finalizer_passed':False,'boot_verified':False})
    return {'kind':kind,'input_directory':str(output),'payload_bytes':manifest['bytes'],'storage':manifest['storage'],'next':'image_native.sh '+kind}

def main():
    if len(sys.argv)!=3 or sys.argv[1] not in ('requirements','prepare') or sys.argv[2] not in OUTPUT or os.geteuid()!=0 or Path(__file__).resolve()!=Path('/opt/toddy-build/scripts/build/phase2/image_inputs.py'):
        raise ValueError('Fixed root coordinator image inputs command required')
    os.umask(0o077);subprocess.run(['/bin/bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    inherited_media_lease();kind=sys.argv[2]
    if sys.argv[1]=='requirements':
        _,_,_,components=selection(kind);records,pins=records_for(components);entries,bindings,evidence=cache_bindings(records,pins)
        result={'kind':kind,'packages':len(components),'owned_entries':len(entries),'generated_bindings':bindings,'archived_cache_evidence':evidence,'selected_union_regeneration_passed':False}
    else:result=prepare(kind)
    print(json.dumps(result,sort_keys=True))

if __name__=='__main__':main()
