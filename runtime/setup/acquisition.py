"""Installed-user review/client cursor; no dependency on an optional agent."""
import os
import re
import uuid

from .pending import SetupError,_encode,_strict,_digest
from .releases import NativeCatalog
from .native_backend import command,NativeBackend
from .acquisition_journal import STATES,TERMINAL

HELPER = '/usr/lib/toddy/setup/native_acquire.py'


def owner_command(argv,*,timeout=None,progress=None):
    """One Polkit child, bounded NDJSON progress; no periodic authentication."""
    import selectors
    import subprocess
    from .native_backend import ENV
    child=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,env=ENV)
    selector=selectors.DefaultSelector();selector.register(child.stdout,selectors.EVENT_READ)
    buffer=bytearray();result=None;invalid=False
    try:
        while selector.get_map():
            for key,_ in selector.select(0.1):
                piece=os.read(key.fileobj.fileno(),65536)
                if not piece:selector.unregister(key.fileobj);continue
                buffer.extend(piece)
                if len(buffer)>65536:invalid=True;buffer.clear();continue
                while b'\n' in buffer:
                    line,_,rest=buffer.partition(b'\n');buffer=bytearray(rest)
                    try:
                        value=_strict(bytes(line))
                        if not isinstance(value,dict) or type(value.get('version')) is not int or value['version']!=1:raise SetupError('acquisition_reply_unknown')
                        if value.get('kind')=='progress':
                            if result is not None or value.get('operation_id')!=argv[3] or value.get('phase') not in STATES:raise SetupError('acquisition_reply_unknown')
                            if progress:
                                try:progress(value)
                                except Exception:pass
                        elif value.get('kind')=='result' and result is None:result=bytes(line)
                        else:raise SetupError('acquisition_reply_unknown')
                    except (SetupError,ValueError,TypeError):invalid=True
        code=child.wait()
    finally:selector.close();child.stdout.close()
    if invalid or buffer or result is None:
        if code in (126,127) and result is None and not invalid and not buffer:return code,b''
        raise SetupError('acquisition_reply_unknown')
    return code,result


class Cursor:
    """Private operation locator, separate from the unchanged installer wishes."""
    def __init__(self,store):
        self.store=store

    def load(self):
        try:descriptor=os.open('acquisition.json',os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC|os.O_NONBLOCK,dir_fd=self.store.dirfd)
        except FileNotFoundError:return None,None
        try:
            self.store._private_regular(descriptor)
            data=os.read(descriptor,65537)
            value=_strict(data)
            if not isinstance(value,dict) or set(value)!={'version','operation_id','review_sha256','terms_sha256','state'} or type(value['version']) is not int or value['version']!=1 or \
                    not isinstance(value['operation_id'],str) or not re.fullmatch('[a-f0-9]{32}',value['operation_id']) or any(not isinstance(value[key],str) or not re.fullmatch('[a-f0-9]{64}',value[key]) for key in ('review_sha256','terms_sha256')) or \
                    value['state'] not in STATES|{'authorizing','outcome_unknown','authorization_canceled'}:
                raise SetupError('acquisition_cursor')
            return value,_digest(data)
        finally:os.close(descriptor)

    def save(self,value,expected_revision):
        with self.store._locked():
            _,revision=self.load()
            if revision!=expected_revision:raise SetupError('stale_revision')
            data=_encode(value)
            name='.acquisition-'+uuid.uuid4().hex
            descriptor=os.open(name,os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_WRONLY|os.O_CLOEXEC,0o600,dir_fd=self.store.dirfd)
            try:
                with os.fdopen(descriptor,'wb',closefd=False) as stream:
                    stream.write(data);stream.flush();os.fsync(descriptor)
                os.replace(name,'acquisition.json',src_dir_fd=self.store.dirfd,dst_dir_fd=self.store.dirfd)
                os.fsync(self.store.dirfd)
            finally:
                os.close(descriptor)
                try:os.unlink(name,dir_fd=self.store.dirfd)
                except FileNotFoundError:pass
        return _digest(data)


class AcquisitionClient:
    """Blocking worker-thread API; UI must serialize explicit owner actions.

    No automatic query (which would prompt Polkit), retry or backend activation.
    Losing an install reply retains the same operation for explicit reconciliation.
    """
    def __init__(self,store,*,catalog=NativeCatalog.load,run=owner_command,inventory=None,progress=None):
        self.cursor=Cursor(store);self.catalog=catalog;self.run=run;self.progress=progress
        self.inventory=inventory or (lambda names:NativeBackend(None).query(names))

    def review(self):
        try:
            current,_=self.cursor.load()
            if current and current['state'] not in TERMINAL|{'authorization_canceled'}:
                return {'version':1,'state':'reconciliation_required','can_install':False,'operation_id':current['operation_id']}
            catalog=self.catalog();review=catalog.review()
            observed=self.inventory([package['name'] for package in review['packages']])
            wanted={package['name']:package['version'] for package in review['packages']}
            if any(value is not None and value!=wanted[name] for name,value in observed.items()):
                return {'version':1,'state':'unavailable','can_install':False,'reason':'native_existing_version_conflict'}
            present=observed==wanted
            return {**review,'state':'packages_present' if present else 'review_required','can_install':not present,
                'observed_packages':observed,'terms_text':catalog.terms(),
                'backend_ready':False,'remote_consent':False,'model_installed':False}
        except (SetupError,OSError,ValueError):
            return {'version':1,'state':'unavailable','can_install':False,'reason':'no_verified_native_release'}

    def install(self,review,*,accepted_terms=False):
        if accepted_terms is not True or review.get('state')!='review_required' or review.get('can_install') is not True or \
                review.get('release_id')!='agent-backend' or any(not isinstance(review.get(key),str) or not re.fullmatch('[a-f0-9]{64}',review[key]) for key in ('review_sha256','terms_sha256')):
            raise SetupError('acquisition_review_required')
        previous,revision=self.cursor.load()
        if previous and previous['state'] not in TERMINAL|{'authorization_canceled'}:
            raise SetupError('acquisition_reconciliation_required')
        current={'version':1,'operation_id':uuid.uuid4().hex,'review_sha256':review['review_sha256'],
            'terms_sha256':review['terms_sha256'],'state':'authorizing'}
        revision=self.cursor.save(current,revision)
        return self._invoke('install',current,revision)

    def action(self,action):
        if action not in ('status','cancel','reconcile'):raise SetupError('acquisition_action')
        current,revision=self.cursor.load()
        if current is None:raise SetupError('acquisition_unknown')
        return self._invoke(action,current,revision)

    def _invoke(self,action,current,revision):
        argv=['/usr/bin/pkexec',HELPER,action,current['operation_id']]
        if action=='install':argv+=['agent-backend',current['review_sha256'],current['terms_sha256']]
        current={**current,'state':'outcome_unknown'}
        response=None
        try:
            code,data=self.run(argv,timeout=None,progress=self.progress)
            if code in (126,127) and not data.strip():
                if action=='install':current['state']='authorization_canceled'
                response={'version':1,'ok':False,'code':'owner_authorization_canceled'}
            else:
                value=_strict(data)
                if isinstance(value,dict) and action=='install' and code==2 and value.get('accepted') is False and value.get('operation_id')==current['operation_id'] and value.get('review_sha256')==current['review_sha256']:
                    current['state']='failed';response=value
                    self.cursor.save(current,revision);return response
                if not isinstance(value,dict) or code not in (0,2) or type(value.get('ok')) is not bool or type(value.get('version')) is not int or value.get('version')!=1 or value.get('operation_id')!=current['operation_id'] or \
                        value.get('review_sha256')!=current['review_sha256'] or value.get('state') not in STATES:
                    raise SetupError('acquisition_reply_unknown')
                current['state']=value['state'];response=value
        except (SetupError,OSError,ValueError,TypeError):
            response={'version':1,'ok':False,'code':'acquisition_reply_unknown','operation_id':current['operation_id']}
        self.cursor.save(current,revision)
        return response
