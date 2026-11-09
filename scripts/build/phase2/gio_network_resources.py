"""Update the tracked shared DConf/GIO cache for three qualified network modules."""
from pathlib import Path
import hashlib,json,subprocess
TARGET=Path('/mnt/lfs');LOG=Path('/var/log/toddy/phase2')
RECORD=Path('/var/log/toddy/packages/dconf_0.49.0-1+toddy1_amd64.json')
RECEIPT=LOG/'gio-network-resources-1.json';CACHE='/usr/lib/gio/modules/giomodule.cache'
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def entries(text):
    result={}
    for line in text.splitlines():
        if not line.strip():continue
        name,points=line.split(': ',1);assert name not in result
        result[name]=points
    return result
def prepare():
    assert not RECEIPT.exists(),'Inspect resource transaction before replay'
    old=json.loads(RECORD.read_text());cache=TARGET/CACHE.lstrip('/')
    tracked=old['generated_resources'][CACHE]
    assert old['installed'] and digest(cache)==tracked['sha256']
    assert entries(cache.read_text())=={'libdconfsettings.so':'gsettings-backend'}
    modules=cache.parent;assert sorted(p.name for p in modules.glob('*.so'))==['libdconfsettings.so']
    assert digest(modules/'libdconfsettings.so')==tracked['input_sha256']==old['payload']['/usr/lib/gio/modules/libdconfsettings.so']['sha256']
    stage=TARGET/'sources/phase2/work/glib-networking-1/stage/usr/lib/gio/modules/giomodule.cache'
    expected=entries(stage.read_text())
    assert expected=={'libgiognomeproxy.so':'gio-proxy-resolver','libgiolibproxy.so':'gio-proxy-resolver','libgiognutls.so':'gio-tls-backend'}
    RECEIPT.write_text(json.dumps({'state':'prepared','old_cache_text':cache.read_text(),'old_generated_resource':tracked,'old_archive_sha256':old['archive_sha256'],'new_network_entries':expected,'stage_cache_sha256':digest(stage),'recovery':'Inspect native package and resource receipts before replay. Retained old DConf resource metadata/cache text can be restored only with verified prior module inputs after reverting/removing the new owned network package. No rollback has been executed.'},indent=2)+'\n')
def finish():
    r=json.loads(RECEIPT.read_text());assert r['state']=='prepared'
    old=json.loads(RECORD.read_text());cache=TARGET/CACHE.lstrip('/')
    assert old['archive_sha256']==r['old_archive_sha256'] and digest(cache)==r['old_generated_resource']['sha256']
    package=json.loads(Path('/var/log/toddy/packages/glib-networking_2.80.1-1+toddy1_amd64.json').read_text());assert package['installed']
    modules=cache.parent;assert {p.name for p in modules.glob('*.so')}=={'libdconfsettings.so',*r['new_network_entries']}
    inputs={p.name:digest(p) for p in modules.glob('*.so')}
    assert inputs['libdconfsettings.so']==old['payload']['/usr/lib/gio/modules/libdconfsettings.so']['sha256']
    for name in r['new_network_entries']:assert inputs[name]==package['payload']['/usr/lib/gio/modules/'+name]['sha256']
    subprocess.run(['chroot',str(TARGET),'gio-querymodules','/usr/lib/gio/modules'],check=True)
    assert entries(cache.read_text())=={**entries(r['old_cache_text']),**r['new_network_entries']}
    updated={**r['old_generated_resource'],'sha256':digest(cache),'module_inputs_sha256':inputs,'scope':'Shared generated cache for unchanged DConf plus three qualified owned GLib networking modules. Archive payload unchanged; regenerate only when module inputs change.'}
    old['generated_resources'][CACHE]=updated
    part=RECORD.with_suffix('.part');assert not part.exists();part.write_text(json.dumps(old,indent=2)+'\n');part.replace(RECORD)
    r.update(state='complete',new_cache_sha256=digest(cache),module_inputs_sha256=inputs,dconf_archive_unchanged=True)
    RECEIPT.write_text(json.dumps(r,indent=2)+'\n')
