"""Ordinary user file/argv tools. No root, policy, secret store or plugin imports.

The broker selects declared tools from a pinned profile. Outputs are untrusted
data. A workspace scopes these file methods; arbitrary shell remains the user's
normal account authority, not a same-UID sandbox or a cross-profile secret wall.
"""
import hashlib
import os
from pathlib import Path
import selectors
import signal
import stat
import subprocess
import sys
import time


class ToolError(Exception):
    pass


class Tools:
    def __init__(self,workspace):
        if os.getuid()==0 or os.geteuid()==0:raise ToolError('unprivileged_tools_required')
        self.workspace=Path(workspace)
        if not self.workspace.is_absolute() or self.workspace.resolve()!=self.workspace:raise ToolError('invalid_workspace')
        self.directory=os.open(self.workspace,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
        info=os.fstat(self.directory)
        if info.st_uid!=os.getuid() or info.st_mode&0o022:
            os.close(self.directory);raise ToolError('unsafe_workspace')

    def close(self):
        if self.directory is not None:os.close(self.directory);self.directory=None

    def __enter__(self):return self
    def __exit__(self,*_):self.close()

    def _parent(self,path):
        if not isinstance(path,str) or len(path.encode())>4096 or '\x00' in path or path.startswith('/') or \
           any(part in ('','.','..') for part in path.split('/')):raise ToolError('invalid_relative_path')
        descriptor=os.dup(self.directory)
        try:
            for part in path.split('/')[:-1]:
                child=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=descriptor)
                os.close(descriptor);descriptor=child
            return descriptor,path.split('/')[-1]
        except BaseException:os.close(descriptor);raise

    def _read(self,parent,name):
        fd=os.open(name,os.O_RDONLY|os.O_NONBLOCK|os.O_NOCTTY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=parent)
        with os.fdopen(fd,'rb') as file:
            info=os.fstat(file.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1 or info.st_size>65536:raise ToolError('file_type_or_size_limit')
            data=file.read(65537)
            if len(data)>65536:raise ToolError('file_size_limit')
            return data,info

    def read(self,path):
        parent,name=self._parent(path)
        try:data,_=self._read(parent,name)
        finally:os.close(parent)
        try:text=data.decode('utf-8',errors='strict')
        except UnicodeError:raise ToolError('text_encoding_unsupported') from None
        return {'text':text,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}

    def write(self,path,text,expected_sha256):
        if not isinstance(text,str) or len(text.encode())>65536:raise ToolError('file_size_limit')
        if expected_sha256 is not None and (not isinstance(expected_sha256,str) or len(expected_sha256)!=64 or any(c not in '0123456789abcdef' for c in expected_sha256)):
            raise ToolError('invalid_expected_hash')
        parent,name=self._parent(path);temporary=None
        try:
            try:data,info=self._read(parent,name)
            except FileNotFoundError:data=None;info=None
            before=hashlib.sha256(data).hexdigest() if data is not None else None
            if before!=expected_sha256:raise ToolError('file_changed')
            if info and (info.st_uid!=os.getuid() or info.st_mode&0o7000):raise ToolError('file_metadata_unsupported')
            if info:
                fd=os.open(name,os.O_RDONLY|os.O_NONBLOCK|os.O_NOCTTY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=parent)
                try:
                    if os.listxattr(fd):raise ToolError('file_metadata_unsupported')
                finally:os.close(fd)
            import secrets
            temporary='.toddy-'+secrets.token_hex(16)
            fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600,dir_fd=parent)
            try:
                if info:os.fchmod(fd,stat.S_IMODE(info.st_mode))
                with os.fdopen(fd,'wb',closefd=False) as output:
                    output.write(text.encode());output.flush();os.fsync(fd)
            finally:os.close(fd)
            try:latest,_=self._read(parent,name);current=hashlib.sha256(latest).hexdigest()
            except FileNotFoundError:current=None
            if current!=before:raise ToolError('file_changed')
            os.replace(temporary,name,src_dir_fd=parent,dst_dir_fd=parent);temporary=None;os.fsync(parent)
            after,_=self._read(parent,name);digest=hashlib.sha256(after).hexdigest()
            if digest!=hashlib.sha256(text.encode()).hexdigest():raise ToolError('file_postcondition_failed')
            return {'verified':True,'sha256':digest,'bytes':len(after)}
        finally:
            if temporary:
                try:os.unlink(temporary,dir_fd=parent)
                except FileNotFoundError:pass
            os.close(parent)

    def shell(self,argv,*,timeout_seconds=30,canceled=lambda:False):
        if not isinstance(argv,list) or not 1<=len(argv)<=64 or any(not isinstance(arg,str) or '\x00' in arg or len(arg.encode())>4096 for arg in argv) or \
           not argv[0].startswith('/') or sum(len(arg.encode()) for arg in argv)>16384 or \
           type(timeout_seconds) is not int or not 1<=timeout_seconds<=120:raise ToolError('invalid_shell_arguments')
        if canceled():raise ToolError('canceled_before_dispatch')
        child=Path(__file__).with_name('child.py')
        process=subprocess.Popen([sys.executable,str(child),str(os.getpid()),*argv],stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,stderr=subprocess.STDOUT,cwd='/proc/self/fd/'+str(self.directory),
            env={'PATH':'/usr/bin:/usr/sbin','LANG':'C.UTF-8','HOME':str(self.workspace)},
            start_new_session=True,close_fds=True,umask=0o077)
        deadline=time.monotonic()+timeout_seconds;chunks=[];size=0
        try:
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout,selectors.EVENT_READ)
                while selector.get_map():
                    if canceled():raise ToolError('canceled_effects_unverified')
                    if time.monotonic()>=deadline:raise ToolError('shell_deadline')
                    for key,_ in selector.select(.05):
                        chunk=os.read(key.fd,8192)
                        if not chunk:selector.unregister(key.fileobj);continue
                        size+=len(chunk)
                        if size>65536:raise ToolError('shell_output_limit')
                        chunks.append(chunk)
                while True:
                    done=os.waitid(os.P_PID,process.pid,os.WEXITED|os.WNOWAIT|os.WNOHANG)
                    if done is not None:break
                    if canceled():raise ToolError('canceled_effects_unverified')
                    if time.monotonic()>=deadline:raise ToolError('shell_deadline')
                    time.sleep(.01)
                code=done.si_status if done.si_code==os.CLD_EXITED else -done.si_status
            return {'process_exit_verified':True,'exit':code,'output':b''.join(chunks).decode('utf-8',errors='replace'),
                    'side_effects_verified':False,'uid':os.getuid()}
        finally:
            try:os.killpg(process.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            process.wait();process.stdout.close()
