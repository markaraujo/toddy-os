"""Rebuild only the DDS loader after an exact MIME spelling patch, never core."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def digest(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def stage_hashes(root):
    return {str(p.relative_to(root)):digest(p) for p in root.rglob('*') if p.is_file() and not p.is_symlink()}


def main():
    assert os.getuid()==101
    namespace={};exec(compile(sys.argv[1],'glycin-mime-compat','exec'),namespace)
    work=Path('/build');out=work/'dds-compat';out.mkdir()
    source=out/'project';shutil.copytree('/src/project',source,symlinks=True)
    main=source/'glycin-loaders/glycin-image-rs/src/main.rs'
    original=main.read_bytes();updated=namespace['add_dds_decoder_alias'](original);main.write_bytes(updated)
    changed=[]
    for p in source.rglob('*'):
        other=Path('/src/project')/p.relative_to(source)
        if p.is_file() and not p.is_symlink() and digest(p)!=digest(other):changed.append(str(p.relative_to(source)))
    assert changed==['glycin-loaders/glycin-image-rs/src/main.rs']
    (out/'source-before.rs').write_bytes(original);(out/'source-after.rs').write_bytes(updated)
    stage=Path('/stage');before=stage_hashes(stage);config='usr/share/glycin-loaders/2+/conf.d/glycin-image-rs.conf'
    loader='usr/libexec/glycin-loaders/2+/glycin-image-rs'
    shutil.copy2(stage/loader,out/'original-loader');shutil.copy2(stage/config,out/'original.conf')
    lock=digest(source/'Cargo.lock')
    env=dict(os.environ,PATH='/build/tools:/usr/bin:/usr/sbin',CARGO_HOME='/build/compile/cargo-home',
             CARGO_NET_OFFLINE='true',CARGO_BUILD_JOBS='2',RUSTFLAGS='-Cdebuginfo=0',CARGO_INCREMENTAL='0',
             LOCALEDIR='/usr/share/locale',GIT_DESCRIBE='')
    args=['cargo','build','--package','glycin-image-rs','--target-dir','/build/compile/cargo-target',
          '--profile','release','--manifest-path',str(source/'Cargo.toml')]
    with (out/'compile.log').open('xb') as log:r=subprocess.run(args,env=env,stdout=log,stderr=subprocess.STDOUT)
    (out/'compile.exit').write_text(str(r.returncode)+'\n');assert r.returncode==0
    assert digest(source/'Cargo.lock')==lock==digest(Path('/src/project/Cargo.lock'))
    shutil.copy2(work/'compile/cargo-target/release/glycin-image-rs',stage/loader)
    (stage/config).write_bytes(namespace['add_dds_canonical_alias']((stage/config).read_bytes()))
    after=stage_hashes(stage);assert set(before)==set(after)
    assert sorted(k for k in before if before[k]!=after[k])==sorted([config,loader])
    receipt={'scope':'One additional DDS MIME spelling at existing decoder dispatch and canonical configuration; native retest pending',
             'source_before_sha256':hashlib.sha256(original).hexdigest(),'source_after_sha256':hashlib.sha256(updated).hexdigest(),
             'source_changed_files':changed,'cargo_lock_sha256':lock,'native_compile_exit':0,
             'stage_before':before,'stage_after':after,'changed_stage_files':[config,loader],
             'preserved_original_loader':str(out/'original-loader'),'package_promotable':False,
             'compatibility_recipe_sha256':hashlib.sha256(sys.argv[1].encode()).hexdigest()}
    (out/'results.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))


if __name__=='__main__':main()
