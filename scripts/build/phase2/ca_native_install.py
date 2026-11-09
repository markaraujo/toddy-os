#!/usr/bin/env python3
"""Promote qualified factory CA data; preserve OpenSSL and legacy consumers."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys
from package_copyright import write_copyright
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from stage_package import payload

ROOT=Path('/opt/toddy-build');TARGET=Path('/mnt/lfs');LOG=Path('/var/log/toddy/phase2')
OLD='2026.11.05-1+toddy1';NEW='2026.11.09-1+toddy1'
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def verify(record):
    for name,row in record['payload'].items():
        p=TARGET/name.lstrip('/');st=p.lstat()
        assert (st.st_mode,st.st_uid,st.st_gid)==(row['mode'],row['uid'],row['gid']),name
        if 'sha256' in row:assert digest(p)==row['sha256'],name
        elif 'symlink' in row:assert os.readlink(p)==row['symlink'],name
        else:assert row['directory'] and p.is_dir(),name
def main():
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    receipt=LOG/'ca-native-transaction-1.json';stage=TARGET/'sources/stage/phase2-ca-native-1'
    assert not stage.exists() and not receipt.exists(),'Inspect uncertain state; no replay'
    for suffix,base in [('.deb','/var/cache/toddy/packages'),('.json','/var/log/toddy/packages')]:
        assert not Path(base,'ca-certificates_'+NEW+'_amd64'+suffix).exists()
    acceptance=json.loads((LOG/'ca-data-acceptance-1.json').read_text())
    assert acceptance['state']=='private-stage-data-qualified-not-installed' and acceptance['installed_root_changed_paths']==0
    work=Path(acceptance['work']);source=Path(acceptance['source'])
    assert digest(work/'data-results.json')==acceptance['private_data_result_sha256']
    result=json.loads((work/'data-results.json').read_text())
    assert result['generation_exit']==result['original_trust_store_exit']==result['ISRG_Root_X1_verification_exit']==0
    assert result['anchors']==172 and result['server_auth_certificates']==121 and not result['removed_server_auth_DER_sha256']
    for name,sha in result['generated_manifest'].items():assert digest(work/name)==sha,name
    assert digest(source/'nss-certdata.txt')==result['certdata_sha256']
    old=json.loads(Path('/var/log/toddy/packages','ca-certificates_'+OLD+'_amd64.json').read_text())
    archive=Path('/var/cache/toddy/packages','ca-certificates_'+OLD+'_amd64.deb')
    assert old['installed'] and digest(archive)==old['archive_sha256'];verify(old)
    assert subprocess.check_output(['chroot',str(TARGET),'dpkg-query','-W','-f=${Version}','ca-certificates'],text=True)==OLD
    assert not (TARGET/'etc/pki').exists() and not list((TARGET/'etc/ssl/private').iterdir())
    # An exact pin would need a reviewed control-only transaction first.
    depends=subprocess.check_output(['chroot',str(TARGET),'dpkg-query','-W','-f=${Depends}','ca-certificates'],text=True)
    reverse=subprocess.check_output(['chroot',str(TARGET),'dpkg-query','-W','-f=${Package} ${Depends}\n'],text=True)
    assert 'ca-certificates (= ' not in reverse
    openssl=json.loads(Path('/var/log/toddy/packages/openssl_4.0.3-1+toddy1_amd64.json').read_text());verify(openssl)
    data={'state':'preparing','scope':'Factory CA data only; no OpenSSL binary/configuration or NSS module change. Local trust update hook/recovery and remote TLS remain pending.',
          'old_version':OLD,'new_version':NEW,'old_archive_sha256':old['archive_sha256'],
          'candidate_result_sha256':digest(work/'data-results.json'),'anchors':172,'server_auth_certificates':121,
          'added_server_auth_DER_sha256':result['added_server_auth_DER_sha256'],
          'rollback':'Inspect transaction, dpkg and payload before action. Retained old ca-certificates archive restores previous bundle and removes only new package-owned data; verify original package and all OpenSSL payload. Never replay uncertain install.'}
    def save():receipt.write_text(json.dumps(data,indent=2)+'\n')
    save();stage.mkdir();subprocess.run(['dpkg-deb','-x',str(archive),str(stage)],check=True)
    assert payload(stage)==old['payload']
    # Copy only qualified factory trust, never owner configurations/private keys,
    # optional generated NSS databases or Java artifacts without consumers.
    pki=stage/'etc/pki';pki.mkdir()
    shutil.copytree(work/'candidate-pki/anchors',pki/'anchors',symlinks=True)
    shutil.copyfile(work/'candidate-pki/anchors.md5sums',pki/'anchors.md5sums')
    shutil.copytree(work/'candidate-pki/tls/certs',pki/'tls/certs',symlinks=True)
    certs=stage/'etc/ssl/certs'
    for f in (work/'candidate-ssl/certs').iterdir():
        target=certs/f.name
        if target.exists() or target.is_symlink():target.unlink()
        if f.is_symlink():
            link=os.readlink(f)
            assert not link.startswith('/') and '/' not in link and link not in ['.','..'],link
            target.symlink_to(link)
        else:
            assert f.is_file();shutil.copyfile(f,target)
    # Keep existing curl/OpenSSL compatibility names, with identical ownership
    # and directory modes. The candidate trust tool seals its own output0555.
    legacy=certs/'ca-bundle.crt'
    if legacy.exists() or legacy.is_symlink():legacy.unlink()
    legacy.symlink_to('ca-certificates.crt')
    shutil.copyfile(source/'nss-certdata.txt',stage/'etc/ssl/certdata.txt')
    for f in stage.rglob('*'):
        if f.is_symlink():continue
        f.chmod(0o755 if f.is_dir() else 0o644)
    archives=[r['filename'] for r in old['sources']]+['nss-3.126.tar.gz','make-ca-1.16.1.tar.gz']
    write_copyright(stage,'ca-certificates',archives)
    updated=payload(stage)
    for name,row in old['payload'].items():
        if name=='/etc/ssl/certs/ca-certificates.crt' or name.startswith('/usr/share/doc/ca-certificates/'):continue
        assert updated[name]==row,name
    for name,row in openssl['payload'].items():
        if name in updated:assert updated[name]==row,'OpenSSL shared path changed '+name
    data['state']='installing';save()
    subprocess.run([sys.executable,str(ROOT/'scripts/build/stage_package.py'),'ca-certificates',NEW,str(stage),
                    *[arg for a in archives for arg in ['--source',a]],'--recipe','scripts/build/phase2/ca-native-install.sh',
                    '--depends',depends,'--install'],cwd=ROOT,check=True)
    new=json.loads(Path('/var/log/toddy/packages','ca-certificates_'+NEW+'_amd64.json').read_text())
    assert new['installed'];verify(new);verify(openssl)
    data.update(state='complete',archive_sha256=new['archive_sha256'],payload_entries=len(new['payload']),openssl_payload_entries_unchanged=len(openssl['payload']))
    save()
if __name__=='__main__':main()
