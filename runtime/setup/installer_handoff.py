"""Fresh installed-user PendingStore handoff; no acquisition, secrets or grants."""
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys


def save(request,*,home,catalog_path):
    try:
        from .pending import Catalog,PendingStore,SetupError
    except ImportError:
        # Fixed installed isolated-script entry; no cwd/PYTHONPATH imports.
        sys.path.insert(0,'/usr/lib')
        from toddy.setup.pending import Catalog,PendingStore,SetupError
    if not isinstance(request,dict) or set(request)!={'operation_id','uid','gid','username','ai_choice','extras','catalog_sha256'} or \
            not re.fullmatch('[0-9a-f]{32}',request.get('operation_id','')) or \
            type(request['uid']) is not int or type(request['gid']) is not int or request['uid']!=os.getuid() or request['gid']!=os.getgid() or os.getuid()==0 or \
            not isinstance(request['username'],str) or not re.fullmatch('[a-z][a-z0-9_-]{0,31}',request['username']) or \
            request['username'] in ('root','lfs','tester','builder','toddy','toddy-live') or \
            request['ai_choice'] not in ('later','api','local') or not isinstance(request['extras'],list) or \
            len(request['extras'])!=len(set(request['extras'])) or set(request['extras'])-{'docker','opencode','vscode'}:
        raise SetupError('installer_pending_request')
    home=Path(home)
    if not home.is_absolute() or home.resolve()!=home or not home.is_dir() or home.stat().st_uid!=os.getuid():raise SetupError('installer_owner_home')
    data=Path(catalog_path).read_bytes();catalog=Catalog(data)
    if catalog.revision!=request['catalog_sha256']:raise SetupError('installer_pending_catalog_changed')
    directory=home
    for part in ('.local','state','toddy'):
        directory/=part
        try:directory.mkdir(mode=0o700)
        except FileExistsError:pass
        info=directory.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid!=os.getuid() or stat.S_IMODE(info.st_mode)!=0o700:raise SetupError('installer_pending_parent')
    with PendingStore(directory/'setup',catalog) as store:
        value={'schema_version':1,'installation_id':'install-'+request['operation_id'],'catalog_revision':catalog.revision,
               'ai_choice':request['ai_choice'],'choices':[{'id':name,'artifact_id':None,'state':'deferred','error_code':'unavailable'} for name in sorted(request['extras'])],
               'consent_receipts':[],'invitation_dismissed':False}
        revision=store.save(value,expected_revision=None)
        observed,digest=store.load()
        if observed!=value or revision!=digest:raise SetupError('installer_pending_readback')
    return {'verified':True,'uid':os.getuid(),'mode':0o600,
            'path':'/home/'+request['username']+'/.local/state/toddy/setup/pending.json',
            'catalog_sha256':catalog.revision,'manifest_sha256':revision}


def main():
    try:
        sys.path.insert(0,'/usr/lib')
        from toddy.shared.json import strict_json
        raw=sys.stdin.buffer.read(65537)
        if len(raw)>65536:raise ValueError('installer_pending_limit')
        request=strict_json(raw)
        home=Path('/home')/request['username']
        result=save(request,home=home,catalog_path='/usr/share/toddy/config/phase2/software-catalog.json')
        print(json.dumps(result,sort_keys=True,separators=(',',':')))
    except (ValueError,OSError,KeyError,TypeError):
        raise SystemExit('installer_pending_handoff_failed') from None

if __name__=='__main__':main()
