"""Strict structured operations; only an independent current owner grant authorizes.

No user/profile supplied callback, environment or executable search path. Explicit
root_command is unrestricted administration and cannot promise reversible effects.
"""
import hashlib
import os
from pathlib import Path
import re
import selectors
import signal
import stat
import subprocess
import sys
import time
from store import PolicyError


def exact(value,fields):
    return isinstance(value,dict) and set(value)==set(fields)


def validate(kind,args):
    if kind=='config_replace':
        if not exact(args,['path','text','expected_sha256']):raise PolicyError('invalid_operation')
        path=args['path'];text=args['text'];expected=args['expected_sha256']
        if not isinstance(path,str) or not path.startswith('/etc/') or '\x00' in path or len(path)>4096 or \
           any(part in ('.','..','') for part in path.split('/')[1:]) or \
           not isinstance(text,str) or '\x00' in text or len(text.encode('utf-8',errors='strict'))>16384 or \
           (expected is not None and (not isinstance(expected,str) or not re.fullmatch(r'[a-f0-9]{64}',expected))):
            raise PolicyError('invalid_operation')
    elif kind=='root_command':
        if not exact(args,['argv','timeout_seconds','acknowledge_unrestricted_root']):raise PolicyError('invalid_operation')
        argv=args['argv']
        if args['acknowledge_unrestricted_root'] is not True or not isinstance(argv,list) or not 1<=len(argv)<=64 or \
           any(not isinstance(arg,str) or '\x00' in arg or len(arg.encode())>4096 for arg in argv) or \
           not argv[0].startswith('/') or sum(len(arg.encode()) for arg in argv)>16384 or \
           type(args['timeout_seconds']) is not int or not 1<=args['timeout_seconds']<=120:
            raise PolicyError('invalid_operation')
    elif kind=='package_transaction':
        from native_backends import validate_package
        validate_package(args)
    else:raise PolicyError('operation_unavailable')
    return args


def _parent(path):
    """Open each real directory without following symlinks, retaining final FD."""
    fd=os.open('/',os.O_RDONLY|os.O_DIRECTORY|os.O_CLOEXEC)
    try:
        for name in Path(path).parts[1:-1]:
            child=os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=fd)
            os.close(fd);fd=child
        return fd
    except BaseException:os.close(fd);raise


def _file_hash(directory,name):
    try:fd=os.open(name,os.O_RDONLY|os.O_NONBLOCK|os.O_NOCTTY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=directory)
    except FileNotFoundError:return None,None
    with os.fdopen(fd,'rb') as file:
        info=os.fstat(file.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1 or info.st_size>1024*1024 or info.st_mode&0o7000:
            raise PolicyError('unsafe_configuration_file')
        if os.listxattr(file.fileno()):raise PolicyError('configuration_metadata_unsupported')
        return hashlib.file_digest(file,'sha256').hexdigest(),info


def config_replace(args,canceled=lambda:False):
    path=Path(args['path']);directory=_parent(path)
    temporary=None
    try:
        before,info=_file_hash(directory,path.name)
        if before!=args['expected_sha256']:raise PolicyError('configuration_changed')
        # Exclusive unpredictable same-directory staging, never follow an existing link.
        import secrets
        temporary='.toddy-'+secrets.token_hex(16)
        fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600,dir_fd=directory)
        try:
            if info:
                os.fchown(fd,info.st_uid,info.st_gid);os.fchmod(fd,stat.S_IMODE(info.st_mode))
            with os.fdopen(fd,'wb',closefd=False) as output:
                output.write(args['text'].encode());output.flush();os.fsync(fd)
        finally:os.close(fd)
        # Check again at commit. Arbitrary external root writers remain outside
        # executor locking; unrestricted root can defeat any local protection.
        current,_=_file_hash(directory,path.name)
        if current!=before:raise PolicyError('configuration_changed')
        if canceled():raise PolicyError('operation_canceled_before_commit')
        os.replace(temporary,path.name,src_dir_fd=directory,dst_dir_fd=directory)
        temporary=None;os.fsync(directory)
        after,_=_file_hash(directory,path.name)
        expected=hashlib.sha256(args['text'].encode()).hexdigest()
        if after!=expected:raise PolicyError('configuration_postcondition_failed')
        return {'verified':True,'sha256':after,'previous_sha256':before}
    finally:
        if temporary:
            try:os.unlink(temporary,dir_fd=directory)
            except FileNotFoundError:pass
        os.close(directory)


def run_command(args,canceled=lambda:False,*,capture=False,drain_unbounded=False):
    deadline=time.monotonic()+args['timeout_seconds'] if args['timeout_seconds'] is not None else float('inf')
    process=subprocess.Popen([sys.executable,str(Path(__file__).with_name('command_child.py')),str(os.getpid()),*args['argv']],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,cwd='/',env={'PATH':'/usr/sbin:/usr/bin','LANG':'C.UTF-8','HOME':'/root'},
        start_new_session=True,umask=0o077,close_fds=True)
    digest=hashlib.sha256();count=0;chunks=[];captured=0
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout,selectors.EVENT_READ)
            while selector.get_map():
                if canceled():raise PolicyError('root_command_canceled')
                remaining=deadline-time.monotonic()
                if remaining<=0:raise PolicyError('root_command_deadline')
                for key,_ in selector.select(min(remaining,.1)):
                    chunk=os.read(key.fd,8192)
                    if not chunk:selector.unregister(key.fileobj);continue
                    count+=len(chunk)
                    if count>65536 and not drain_unbounded:raise PolicyError('root_command_output_limit')
                    digest.update(chunk)
                    if capture and captured<65536:
                        retained=chunk[:65536-captured];chunks.append(retained);captured+=len(retained)
            # Keep the exited leader unreaped until group cleanup, avoiding a
            # reused PID/group identity between wait and killpg.
            while True:
                exited=os.waitid(os.P_PID,process.pid,os.WEXITED|os.WNOWAIT|os.WNOHANG)
                if exited is not None:break
                if canceled():raise PolicyError('root_command_canceled')
                if time.monotonic()>=deadline:raise PolicyError('root_command_deadline')
                time.sleep(.01)
            code=exited.si_status if exited.si_code==os.CLD_EXITED else -exited.si_status
        # This verifies process termination only, not arbitrary shell side effects.
        result={'process_exit_verified':True,'exit':code,'output_bytes':count,'output_sha256':digest.hexdigest(),
                'unrestricted_root':True,'side_effects_verified':False,'output_truncated':bool(capture and count>65536)}
        if capture:result['_private_output']=b''.join(chunks)
        return result
    finally:
        try:os.killpg(process.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        process.wait();process.stdout.close()


def root_command(args,canceled=lambda:False):
    return run_command(args,canceled)


def apply(kind,args,canceled=lambda:False):
    if os.geteuid()!=0:raise PolicyError('root_executor_required')
    validate(kind,args)
    if canceled():raise PolicyError('operation_canceled_before_dispatch')
    if kind=='config_replace':return config_replace(args,canceled)
    if kind=='package_transaction':
        from native_backends import package_transaction
        return package_transaction(args,canceled)
    return root_command(args,canceled)
