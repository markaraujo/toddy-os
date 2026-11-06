#!/usr/bin/python3
"""Test-only live downloader: verify frozen GLVS inputs before Vim sees bytes."""
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
from urllib.parse import parse_qs,urlsplit

NATIVE='/usr/bin/curl'
ROOT=Path(__file__).resolve().parents[1]


def classify(url, manifest, head):
    parsed=urlsplit(url)
    if parsed.scheme!='https' or parsed.netloc!='www.vim.org' or parsed.fragment:
        raise ValueError('Unexpected Vim source origin')
    query=parse_qs(parsed.query,strict_parsing=True)
    if parsed.path=='/scripts/script.php' and list(query)==['script_id'] and len(query['script_id'])==1:
        for row in manifest['components']:
            if query['script_id'][0]==str(row['script_id']):return 'metadata',row
    if parsed.path=='/scripts/download_script.php' and list(query)==['src_id'] and len(query['src_id'])==1:
        for row in manifest['components']:
            if query['src_id'][0]==str(row['source_id']):return 'plugin',row
        if head and query['src_id']==['1']:return 'historical-head-only',None
    raise ValueError('Unfrozen Vim script/version requested')


def validate(data, kind, row):
    if kind=='plugin':
        if len(data)!=row['size'] or hashlib.sha256(data).hexdigest()!=row['sha256']:
            raise ValueError('Vim plugin source hash/size mismatch')
    else:
        text=data.decode('utf-8')
        marker='Click on the package to download'
        if marker not in text:raise ValueError('Missing live Vim download table')
        match=re.search(r'^\s*<td class.*src_id=(\d+)">([^<]+)<.*$',text.split(marker,1)[1],re.M)
        if not match or match.groups()!=(str(row['source_id']),row['upstream_filename']):
            raise ValueError('Live Vim download metadata changed from frozen version')
        if re.search(r'(^|[ \t])(?:vi|vim|ex):',text,re.M):
            raise ValueError('Unexpected editor modeline in downloaded metadata')
    return hashlib.sha256(data).hexdigest()


def main(args):
    urls=[a for a in args if a.startswith(('http://','https://'))
          and 'vim.org' in urlsplit(a).netloc and urlsplit(a).path.startswith('/scripts/')]
    if not urls:
        return subprocess.call([NATIVE,*args])
    if os.geteuid()==0:raise ValueError('Vim download guard is for unprivileged tests only')
    manifest=json.loads((ROOT/'manifest.json').read_text())
    if len(urls)!=1:raise ValueError('Ambiguous Vim download request')
    url=urls[0];head='-I' in args
    kind,row=classify(url,manifest,head)
    if head:
        if args!=['-s','-I','-w','%{http_code}','-o','/dev/null',url]:
            raise ValueError('Unexpected Vim HEAD invocation')
        return subprocess.call([NATIVE,'--max-time','60',*args])
    if len(args)!=4 or args[:2]!=['-s','-o'] or args[-1]!=url:
        raise ValueError('Unexpected Vim download invocation')
    output=Path(args[2])
    if output.is_symlink():raise ValueError('Symlink download output refused')
    resolved=output.resolve()
    if not (resolved.is_relative_to('/tmp') or resolved.is_relative_to('/sources/vim-9.2.1201')):
        raise ValueError('Download output outside disposable test paths')
    if output.exists():
        info=output.stat()
        if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.geteuid():
            raise ValueError('Download output is not a tester-owned regular file')
        output.unlink()
    temporary=None
    try:
        fd,name=tempfile.mkstemp(prefix='.toddy-verified-',dir=output.parent)
        os.close(fd);temporary=Path(name)
        result=subprocess.run([NATIVE,'--fail','--max-time','60','--max-filesize','1048576','-s','-o',name,url])
        if result.returncode:return result.returncode
        data=temporary.read_bytes();sha=validate(data,kind,row)
        # Log only public source facts; never arbitrary curl arguments/headers.
        log=Path(os.environ['TODDY_VIM_DOWNLOAD_LOG'])
        descriptor=os.open(log,os.O_WRONLY|os.O_APPEND|os.O_NOFOLLOW)
        try:
            info=os.fstat(descriptor)
            if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.geteuid() or info.st_nlink!=1:
                raise ValueError('Unsafe Vim download event log')
            record={'kind':kind,'script_id':row['script_id'],'source_id':row['source_id'],
                    'url':url,'sha256':sha,'uid':os.geteuid(),'verified':True}
            os.write(descriptor,(json.dumps(record)+'\n').encode())
        finally:os.close(descriptor)
        os.replace(temporary,output);temporary=None
        return 0
    finally:
        if temporary is not None:temporary.unlink(missing_ok=True)

if __name__=='__main__':
    try:raise SystemExit(main(sys.argv[1:]))
    except (ValueError,OSError,KeyError) as error:
        print('Verified Vim downloader refused input: '+str(error),file=sys.stderr)
        raise SystemExit(1)
