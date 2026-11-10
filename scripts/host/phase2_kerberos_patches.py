#!/usr/bin/env python3
"""Pin the three required patches from the exact frozen MIT Kerberos book page."""
from pathlib import Path
import hashlib,json,re,subprocess

ROOT=Path(__file__).resolve().parents[2]

def main():
 path=ROOT/'config/phase2/sources.lock.json';lock=json.loads(path.read_text())
 parent=next(r for r in lock['components'] if r['name']=='mitkrb')
 assert parent['version']=='1.22.2' and parent['reference']=='BLFS13.1-systemd postlfs/mitkrb.html'
 page=ROOT/'.local/books/blfs/postlfs/mitkrb.html';data=page.read_bytes()
 assert hashlib.sha256(data).hexdigest()==parent['book_page_sha256']
 urls=set(re.findall(r'href\s*=\s*"(https://www\.linuxfromscratch\.org/patches/blfs/13\.1/mitkrb-1\.22\.2-[^"]+\.patch)"',data.decode()))
 selected={'mitkrb-upstream-fix':'mitkrb-1.22.2-upstream_fix-1.patch','mitkrb-security-fix':'mitkrb-1.22.2-security_fix-1.patch','mitkrb-openssl4-fixes':'mitkrb-1.22.2-openssl_4_fixes-1.patch'}
 assert {url.rsplit('/',1)[1] for url in urls}==set(selected.values())
 rows=[]
 for name,filename in selected.items():
  url=next(url for url in urls if url.endswith('/'+filename));target=ROOT/'.local/sources'/filename
  assert not target.is_symlink()
  if not target.exists():
   part=target.with_name(filename+'.part');assert not part.exists(),'Inspect partial source download first'
   subprocess.run(['curl','--fail','--silent','--show-error','--location','--connect-timeout','15','--max-time','90','--output',str(part),url],check=True)
   part.rename(target)
  body=target.read_bytes();assert 0<len(body)<1024*1024 and b'--- ' in body and b'+++ ' in body
  row={'name':name,'version':'1.22.2','filename':filename,'url':url,'sha256':hashlib.sha256(body).hexdigest(),'reference':parent['reference'],'book_page_sha256':parent['book_page_sha256'],'integrity':'Exact required patch URL from frozen book, authenticated official HTTPS bytes; SHA256 pinned before guest use. The book provides no separate patch MD5.','status':'source_verified'}
  prior=[r for r in lock['components'] if r['name']==name]
  if prior:assert prior==[row],'Never replace a frozen patch'
  else:lock['components'].append(row)
  rows.append(row)
 path.write_text(json.dumps(lock,indent=2)+'\n');print(json.dumps(rows,indent=2))

if __name__=='__main__':main()
