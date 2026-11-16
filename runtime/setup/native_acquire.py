#!/usr/bin/python3 -I
"""Fixed per-action Polkit package authorization; no broker/executor dependency."""
import argparse
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import pwd
import re
import resource
import subprocess
import sys

# Fixed owned installed namespace; no cwd, environment or module argument hook.
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
if Path(__file__).resolve().parents[1].name=='toddy':
    from toddy.setup.platform import installed_toddy
    from toddy.setup.pending import SetupError,_encode
    from toddy.setup.releases import NativeCatalog
    from toddy.setup.acquisition_journal import Journal,operation_id,TERMINAL
    from toddy.setup.native_backend import NativeBackend,command
else:
    from runtime.setup.platform import installed_toddy
    from runtime.setup.pending import SetupError,_encode
    from runtime.setup.releases import NativeCatalog
    from runtime.setup.acquisition_journal import Journal,operation_id,TERMINAL
    from runtime.setup.native_backend import NativeBackend,command


class Parser(argparse.ArgumentParser):
    def error(self,_message):
        raise SetupError('acquisition_arguments')


def caller():
    if os.getuid()!=0 or os.geteuid()!=0:
        raise SetupError('acquisition_authentication_required')
    raw=os.environ.get('PKEXEC_UID','')
    if not re.fullmatch('[1-9][0-9]{0,9}',raw) or not 1000<=int(raw)<2**31:
        raise SetupError('acquisition_caller_required')
    uid=int(raw);account=pwd.getpwuid(uid)
    if account.pw_name in ('root','lfs','toddy','toddy-live','live','builder'):
        raise SetupError('acquisition_installed_owner_required')
    return uid


def active(uid):
    installed_toddy()
    if 'toddy.live' in Path('/proc/cmdline').read_text().split() or Path('/run/toddy/live-session').exists():
        raise SetupError('acquisition_installed_owner_required')
    code,data=command(['/usr/bin/loginctl','show-user',str(uid),'-p','Display','--value'])
    session=data.decode('ascii',errors='strict').strip()
    if code or not re.fullmatch('[A-Za-z0-9_-]{1,128}',session):
        raise SetupError('acquisition_active_owner_required')
    code,data=command(['/usr/bin/loginctl','show-session',session,'-p','User','-p','Active','-p','Remote','-p','LockedHint'])
    values=dict(line.split('=',1) for line in data.decode('ascii',errors='strict').splitlines())
    if code or values!={'User':str(uid),'Active':'yes','Remote':'no','LockedHint':'no'}:
        raise SetupError('acquisition_active_owner_required')


@contextmanager
def dispatch_lock(journal):
    descriptor=os.open(journal.directory/'dispatch.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
    try:
        try:fcntl.flock(descriptor,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise SetupError('acquisition_busy') from None
        yield
    finally:os.close(descriptor)


@contextmanager
def package_idle():
    descriptors=[]
    try:
        for path in ('/var/lib/dpkg/lock-frontend','/var/lib/dpkg/lock'):
            descriptor=os.open(path,os.O_RDWR|os.O_NOFOLLOW|os.O_CLOEXEC)
            descriptors.append(descriptor)
            try:fcntl.lockf(descriptor,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:raise SetupError('native_package_busy') from None
        yield
    finally:
        for descriptor in descriptors:os.close(descriptor)


def reconcile(journal,uid,identity,backend):
    row=journal.get(uid,identity)
    if row is None:raise SetupError('acquisition_unknown')
    if row['state'] in TERMINAL:return row
    with dispatch_lock(journal),package_idle():
        if not row['write_intent_recorded']:
            return journal.state(uid,identity,'deferred',code='interrupted_before_package_write')
        expected={p['name']:p['version'] for p in row['review']['packages']}
        if backend.query(expected)==expected:
            backend.postconditions(row['review'])
            return journal.state(uid,identity,'installed')
        return journal.state(uid,identity,'needs_reconciliation',code='native_write_requires_reconciliation')


def install(journal,uid,identity,review_hash,terms_hash,release_id,*,catalog=None,backend=None):
    operation_id(identity)
    # Pure lookup before current catalog/availability/busy checks; never requeue.
    row=journal.get(uid,identity)
    if row is not None:
        if row['review_sha256']!=review_hash or row['review']['release_id']!=release_id or row['review']['terms_sha256']!=terms_hash:
            raise SetupError('acquisition_identity_conflict')
        return row
    active(uid)
    catalog=NativeCatalog.load() if catalog is None else catalog
    review=catalog.review(release_id)
    if review['review_sha256']!=review_hash or review['terms_sha256']!=terms_hash:
        raise SetupError('acquisition_review_changed')
    backend=NativeBackend(catalog,before_write=lambda:active(uid)) if backend is None else backend
    with dispatch_lock(journal):
        row,created=journal.accept(uid,identity,review)
        if not created:return row
        try:
            return backend.acquire(journal,uid,identity,catalog.releases[release_id],review)
        except BaseException as error:
            current=journal.get(uid,identity)
            if current['state'] not in TERMINAL:
                code=str(error) if isinstance(error,SetupError) and re.fullmatch('[a-z_]{1,64}',str(error)) else 'acquisition_step_unverified'
                journal.state(uid,identity,'needs_reconciliation' if current['write_intent_recorded'] else 'failed',code=code)
            raise


def main(argv=None):
    journal=None;args=None;output_open=True
    def progress(row):
        nonlocal output_open
        if not output_open:return
        try:
            frame={'version':1,'kind':'progress','operation_id':row['operation_id'],
                'review_sha256':row['review_sha256'],'phase':row['state'],
                'cancellation_requested':row['cancellation_requested']}
            sys.stdout.buffer.write(_encode(frame)+b'\n');sys.stdout.buffer.flush()
        except OSError:
            output_open=False
            if journal is not None:journal.cancel(uid,row['operation_id'])
    try:
        uid=caller();os.umask(0o077);resource.setrlimit(resource.RLIMIT_CORE,(0,0))
        parser=Parser(add_help=False,allow_abbrev=False)
        parser.add_argument('action',choices=['install','status','cancel','reconcile'])
        parser.add_argument('operation_id')
        parser.add_argument('release_id',nargs='?')
        parser.add_argument('review_sha256',nargs='?')
        parser.add_argument('terms_sha256',nargs='?')
        args=parser.parse_args(argv);operation_id(args.operation_id)
        if args.action=='install':
            if args.release_id!='agent-backend' or any(not isinstance(value,str) or not re.fullmatch('[a-f0-9]{64}',value) for value in (args.review_sha256,args.terms_sha256)):
                raise SetupError('acquisition_arguments')
        elif any(value is not None for value in (args.release_id,args.review_sha256,args.terms_sha256)):
            raise SetupError('acquisition_arguments')
        journal=Journal(observer=progress if args.action=='install' else None,create=args.action=='install',read_only=args.action=='status')
        if args.action=='install':
            row=install(journal,uid,args.operation_id,args.review_sha256,args.terms_sha256,args.release_id)
        elif args.action=='cancel':
            row=journal.cancel(uid,args.operation_id)
        elif args.action=='reconcile':
            row=reconcile(journal,uid,args.operation_id,NativeBackend(None))
        else:
            row=journal.get(uid,args.operation_id)
            if row is None:raise SetupError('acquisition_unknown')
        output={'version':1,'kind':'result','ok':True,**row};code=0
    except Exception as error:
        message=str(error) if isinstance(error,SetupError) and re.fullmatch('[a-z_]{1,64}',str(error)) else 'acquisition_unavailable'
        output={'version':1,'kind':'result','ok':False,'code':message};code=2
        if journal is not None and args is not None:
            try:
                known=journal.get(uid,args.operation_id)
                output.update(operation_id=args.operation_id,accepted=known is not None)
                if known is not None:output.update(known)
                elif args.action=='install':output['review_sha256']=args.review_sha256
            except Exception:pass
    finally:
        if journal is not None:journal.close()
    try:sys.stdout.buffer.write(_encode(output)+b'\n');sys.stdout.buffer.flush()
    except BrokenPipeError:pass # No replay/kill after an owner UI disconnect.
    return code


if __name__=='__main__':
    raise SystemExit(main())
