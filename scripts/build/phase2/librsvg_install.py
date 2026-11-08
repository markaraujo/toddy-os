"""Owned native SVG renderer and same-owner generated Pixbuf cache transaction."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

from package_copyright import write_copyright
from verify_stage import inspect_stage
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from stage_package import payload

ROOT=Path('/opt/toddy-build')
TARGET=Path('/mnt/lfs')


def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def main():
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    logs=Path('/var/log/toddy/phase2');work=TARGET/'sources/phase2/work/librsvg-1'
    source=TARGET/'sources/phase2/inputs/librsvg-2.62.3'
    assert sha(source/'toddy-build.py')=='9ec8e7b892b30388015234f6c054a9605614ee3240846bfd84e69d73ac1c6a97'
    assert (source/'toddy-probe.c').read_bytes()==(ROOT/'scripts/build/phase2/librsvg-probe.c').read_bytes()
    assert (source/'toddy-crates.json').read_bytes()==(ROOT/'config/phase2/rust-crates.lock.json').read_bytes()
    contract=json.loads((source/'toddy-crates.json').read_text());parent=next(p for p in contract['parents'] if p['name']=='librsvg')
    assert sha(source/'project/Cargo.lock')==parent['cargo_lock_sha256'] and len(parent['packages'])==352
    harness=sha(ROOT/'scripts/build/phase2/isolated.sh')
    for name,expected in [('librsvg-1',1),('librsvg-reference-diagnose-3',0),('librsvg-strike-oracle-5',0),('librsvg-finish-6',0)]:
        assert int((logs/(name+'.exit')).read_text())==expected
        r=json.loads((logs/(name+'.job.json')).read_text());assert r['harness_sha256']==harness
        if name in ['librsvg-strike-oracle-5','librsvg-finish-6']:
            filename='librsvg_strike_qualify.py' if name=='librsvg-strike-oracle-5' else 'librsvg_finish.py'
            assert r['command'][-3:]==['python3','-c',(ROOT/'scripts/build/phase2'/filename).read_text()]
    proof=json.loads((work/'test-results.json').read_text())
    assert proof['staged_consumer_exit']==0 and proof['unchanged_compiled_elf_files']==144
    assert all(r['native_exit']==0 for r in proof['checks'])
    assert proof['known_golden_failure']['upstream_passed'] is False
    oracle=proof['known_golden_failure']['pango_geometry_oracle']
    assert oracle==json.loads((work/'strike-oracle-5/metrics.json').read_text())
    assert oracle['changed_pixels']==12 and oracle['outside_decoration_changes']==0 and oracle['pango_version']=='1.58.2'
    manifest=json.loads((work/'reference-diagnose-3/binaries-before.json').read_text())
    assert len(manifest)==144
    for relative,digest in manifest.items():assert sha(work/'compile'/relative)==digest
    for name in ['configure','build']:assert (work/(name+'.exit')).read_text().strip()=='0'
    assert (work/'upstream-tests.exit').read_text().strip()=='1'
    stage=work/'stage';verified=inspect_stage(stage)
    assert (stage/'usr/lib/librsvg-2.so.2').is_file() and (stage/'usr/lib/girepository-1.0/Rsvg-2.0.typelib').is_file()
    destination=TARGET/'sources/stage/phase2-librsvg';cache_stage=TARGET/'sources/stage/phase2-gdk-pixbuf-svg-cache'
    assert not destination.exists() and not cache_stage.exists(),'Reconcile prior transaction; no install replay'
    old=json.loads(Path('/var/log/toddy/packages/gdk-pixbuf_2.44.7-1+toddy1_amd64.json').read_text())
    old_stage=TARGET/'sources/stage/phase2-gdk-pixbuf'
    old_payload={p:r for p,r in payload(old_stage).items() if p!='/DEBIAN' and not p.startswith('/DEBIAN/')}
    assert old['installed'] and old_payload==old['payload']
    assert sha(Path('/var/cache/toddy/packages/gdk-pixbuf_2.44.7-1+toddy1_amd64.deb'))==old['archive_sha256']
    cache_relative='usr/lib/gdk-pixbuf-2.0/2.10.0/loaders.cache'
    assert sha(TARGET/cache_relative)==old['payload']['/'+cache_relative]['sha256']
    shutil.copytree(stage,destination,symlinks=True);assert inspect_stage(destination)==verified
    (logs/'librsvg-stage.json').write_text(json.dumps(verified,indent=2)+'\n')
    archives=['librsvg-2.62.3.tar.xz','librsvg-2.62.3-vendor.tar.gz','rustc-1.97.1-src.tar.xz']
    write_copyright(destination,'librsvg',archives)
    dependencies='glibc (>= 2.44-1), gcc (>= 16.2.0-1), glib (>= 2.88.3-1+toddy1), cairo (>= 1.18.4-1+toddy1), pango (= 1.58.2-1+toddy1), gdk-pixbuf (>= 2.44.7-1+toddy1), libxml2 (= 2.15.3-1+toddy1)'
    def package(name,version,stage,archives,depends):
        subprocess.run([sys.executable,str(ROOT/'scripts/build/stage_package.py'),name,version,str(stage),
            *[arg for name in archives for arg in ['--source',name]],'--recipe','scripts/build/phase2/librsvg-install.sh','--depends',depends,'--install'],cwd=ROOT,check=True)
    package('librsvg','2.62.3-1+toddy1',destination,archives,dependencies)
    # Upstream suppresses cache writes under DESTDIR. Reuse the byte-verified
    # original image package, replacing only its own generated cache; no foreign
    # payload overwrite, compiler replay or unmanaged global postinstall script.
    shutil.copytree(old_stage,cache_stage,symlinks=True,ignore=shutil.ignore_patterns('DEBIAN'))
    assert payload(cache_stage)==old['payload']
    generated=subprocess.check_output(['chroot',str(TARGET),'/usr/bin/gdk-pixbuf-query-loaders'],
                                     env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8'})
    text=generated.decode();module='/usr/lib/gdk-pixbuf-2.0/2.10.0/loaders/libpixbufloader_svg.so'
    assert text.count('"'+module+'"')==1 and '"svg"' in text
    assert all(part not in text for part in ['/build/','/src/','/stage/','/mnt/lfs/'])
    (cache_stage/cache_relative).write_bytes(generated)
    revised=payload(cache_stage)
    changed=[p for p in old['payload'] if old['payload'][p]!=revised[p]]
    assert changed==['/'+cache_relative] and set(revised)==set(old['payload'])
    receipt={'scope':'Same-owner generated cache replacement only; unchanged native Gdk library/builtin loader/legal payload reused',
             'old_package_version':old['version'],'old_archive_sha256':old['archive_sha256'],
             'old_cache_sha256':old['payload']['/'+cache_relative]['sha256'],'new_cache_sha256':sha(cache_stage/cache_relative),
             'changed_paths':changed,'external_modules':[module],'unchanged_other_payload_entries':len(revised)-1,'complete':False}
    receipt_path=logs/'librsvg-gdk-cache-transaction.json';receipt_path.write_text(json.dumps(receipt,indent=2)+'\n')
    package('gdk-pixbuf','2.44.7-1+toddy2',cache_stage,['gdk-pixbuf-2.44.7.tar.xz'],
        'glibc (>= 2.44-1), glib (>= 2.88.3-1+toddy1), libpng (>= 1.6.58-1+toddy1), libjpeg-turbo (= 3.2.0-1+toddy1), gobject-introspection (>= 1.86.0-1+toddy1)')
    assert sha(TARGET/cache_relative)==receipt['new_cache_sha256']
    receipt['complete']=True;receipt_path.write_text(json.dumps(receipt,indent=2)+'\n')


if __name__=='__main__':main()
