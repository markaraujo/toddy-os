#!/usr/bin/env python3
"""Freeze the exact optional dictionary from the already frozen Cracklib book page."""
from pathlib import Path
import hashlib,json,lzma,os,subprocess,tarfile
ROOT=Path(__file__).resolve().parents[2]
page=ROOT/'.local/books/blfs/postlfs/cracklib.html'
assert hashlib.sha256(page.read_bytes()).hexdigest()=='8fb50f6aa8421fffdaaf1ed995430144766feb73565d8625667688a8c93a91d9'
url='https://github.com/cracklib/cracklib/releases/download/v2.10.3/cracklib-words-2.10.3.xz'
md5='f27804022dbf2682a7f7c353317f9a53'
assert url in page.read_text() and md5 in page.read_text()
filename='cracklib-words-2.10.3.xz';p=ROOT/'.local/sources'/filename
if not p.exists():
 s=os.statvfs(ROOT);assert s.f_bavail*s.f_frsize>=100*1024**3+8*1024**2
 part=p.with_suffix('.xz.part');assert not part.exists(),'Inspect partial acquisition first; no replay'
 subprocess.run(['curl','--fail','--silent','--show-error','--location','--connect-timeout','15','--max-time','180','--output',str(part),url],check=True)
 part.rename(p)
assert p.is_file() and not p.is_symlink();raw=p.read_bytes();assert hashlib.md5(raw,usedforsecurity=False).hexdigest()==md5
size=lines=0;h=hashlib.sha256()
with lzma.open(p,'rb') as f:
 while block:=f.read(1024*1024):
  size+=len(block);assert size<=128*1024**2;lines+=block.count(b'\n');h.update(block)
with tarfile.open(ROOT/'.local/sources/cracklib-2.10.3.tar.xz') as t:
 license_data=t.extractfile('cracklib-2.10.3/README-WORDS').read();assert b'public\ndomain word lists' in license_data
row={'name':'cracklib-words','version':'2.10.3','filename':filename,'url':url,'sha256':hashlib.sha256(raw).hexdigest(),'reference':'BLFS13.1-systemd postlfs/cracklib.html recommended dictionary','book_page_sha256':hashlib.sha256(page.read_bytes()).hexdigest(),'book_md5':md5,'source_kind':'xz-compressed word-list data, not a tar archive','expanded_bytes':size,'expanded_sha256':h.hexdigest(),'lines':lines,'license_provenance':'Cracklib2.10.3 README-WORDS: upstream distribution built solely from prior cracklib/crack lists and/or public-domain lists; retain exact README-WORDS with source notices, no license claim for other word lists.','license_provenance_sha256':hashlib.sha256(license_data).hexdigest(),'integrity':'Official HTTPS release matched exact frozen book MD5; compressed/expanded SHA256 frozen before guest use, no detached-signature claim','status':'source_verified'}
lock=ROOT/'config/phase2/sources.lock.json';r=json.loads(lock.read_text());prior=[x for x in r['components'] if x['name']==row['name']]
if prior:assert len(prior)==1 and prior[0]==row
else:r['components'].append(row);lock.write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(row,indent=2))
