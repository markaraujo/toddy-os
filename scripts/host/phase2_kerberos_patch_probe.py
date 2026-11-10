#!/usr/bin/env python3
"""Verify required Kerberos patches on a disposable host source copy, never install."""
from pathlib import Path
import hashlib,json,shutil,subprocess,tarfile,tempfile

ROOT=Path(__file__).resolve().parents[2]
NAMES=['mitkrb-upstream-fix','mitkrb-security-fix','mitkrb-openssl4-fixes']

def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def manifest(base):
 return {str(p.relative_to(base)):digest(p) for p in base.rglob('*') if p.is_file() and not p.is_symlink()}

def main():
 rows=json.loads((ROOT/'config/phase2/sources.lock.json').read_text())['components']
 source=next(r for r in rows if r['name']=='mitkrb');assert source['version']=='1.22.2'
 archive=ROOT/'.local/sources'/source['filename'];assert digest(archive)==source['sha256']
 output=ROOT/'docs/evidence/B02-mitkrb-patch-preflight.json';assert not output.exists(),'Reuse the verified exact-input evidence'
 with tarfile.open(archive) as t:
  expanded=sum(m.size for m in t if m.isfile())
  assert shutil.disk_usage(ROOT).free>=100*1024**3+expanded+16*1024**2
  with tempfile.TemporaryDirectory(prefix='mitkrb-patches-',dir=ROOT/'.local/phase2') as directory:
   t.extractall(directory,filter='data');base=Path(directory)/'krb5-1.22.2';assert base.is_dir()
   initial=manifest(base);proofs=[]
   for name in NAMES:
    row=next(r for r in rows if r['name']==name);p=ROOT/'.local/sources'/row['filename'];assert digest(p)==row['sha256']
    before=manifest(base)
    r=subprocess.run(['patch','--batch','--forward','--fuzz=0','-Np1','-i',str(p)],cwd=base,text=True,capture_output=True)
    assert r.returncode==0,(name,r.stdout,r.stderr)
    after=manifest(base);changed=[key for key in sorted(before.keys()|after.keys()) if before.get(key)!=after.get(key)];assert changed
    proofs.append({'patch':row,'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'changed_files':[{'path':k,'before_sha256':before.get(k),'after_sha256':after.get(k)} for k in changed]})
   final=manifest(base)
 output.write_text(json.dumps({'scope':'Disposable host source application only, all3 exact frozen required patches in book order/fuzz0. No guest preparation/compiler/tests/runtime/package/security acceptance.','source':source,'expanded_regular_bytes':expanded,'initial_regular_files':len(initial),'final_regular_files':len(final),'patches':proofs,'original_archive_unchanged':digest(archive)==source['sha256']},indent=2)+'\n')
 print(output.relative_to(ROOT))

if __name__=='__main__':main()
