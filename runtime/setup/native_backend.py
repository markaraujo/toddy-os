"""Fixed signed APT/dpkg acquisition backend, independent of the absent agent."""
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path
import pwd
import re
import stat
import subprocess
import tarfile

from .pending import SetupError,_encode
from .releases import PACKAGES, POSTCONDITIONS, SOURCES, DIRECTORY, signature, sha

ENV = {'PATH':'/usr/bin:/usr/sbin','HOME':'/root','LC_ALL':'C','DEBIAN_FRONTEND':'noninteractive'}


def command(argv, *, timeout=30):
    # Retain bounded bytes and drain the rest. A package writer has no timeout
    # or kill path; read-only/private-download commands may time out safely.
    import selectors
    import time
    child=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,env=ENV)
    limit=4*1024**2;data=bytearray();overflow=False;expired=False
    deadline=None if timeout is None else time.monotonic()+timeout
    selector=selectors.DefaultSelector();selector.register(child.stdout,selectors.EVENT_READ)
    try:
        while selector.get_map():
            if deadline is not None and time.monotonic()>=deadline and not expired:
                expired=True;child.kill()  # Never used for an installed-package writer.
            for key,_ in selector.select(0.1):
                piece=os.read(key.fileobj.fileno(),65536)
                if not piece:selector.unregister(key.fileobj);continue
                capacity=limit-len(data)
                if len(piece)>capacity:overflow=True
                data.extend(piece[:capacity])
        code=child.wait()
    finally:
        selector.close();child.stdout.close()
    if expired:raise SetupError('native_command_timeout')
    if overflow:raise SetupError('native_output_bound')
    return code,bytes(data)


def simulation(data, expected):
    found = {}
    for line in data.decode('utf-8',errors='strict').splitlines():
        if line.startswith('Remv '):
            raise SetupError('native_plan_changed')
        if line.startswith('Inst '):
            match = re.fullmatch(r'Inst ([a-z0-9][a-z0-9+.-]*) \(([^\s()]+) [^\n]*\)',line)
            if not match or match[1] in found or expected.get(match[1]) != match[2]:
                raise SetupError('native_plan_changed')
            found[match[1]] = match[2]
        if line.startswith('Conf '):
            match = re.fullmatch(r'Conf ([a-z0-9][a-z0-9+.-]*) \(([^\s()]+) [^\n]*\)',line)
            if not match or expected.get(match[1])!=match[2]:
                raise SetupError('native_plan_changed')
    if found != expected:
        raise SetupError('native_plan_changed')


class NativeBackend:
    def __init__(self, catalog, *, run=command, cache=Path('/var/cache/toddy/setup-acquisition'),before_write=None):
        self.catalog,self.run,self.cache = catalog,run,cache
        self.before_write=before_write

    def query(self, names):
        result = {}
        for name in names:
            if name not in PACKAGES:
                raise SetupError('native_package_id')
            code,data = self.run(['/usr/bin/dpkg-query','--show','--showformat=${db:Status-Status}\t${Version}\n',name])
            if code == 1:
                result[name] = None; continue
            if code or len(data)>4096:
                raise SetupError('native_inventory')
            fields=data.decode('ascii',errors='strict').strip().split('\t')
            if len(fields)!=2 or fields[0]!='installed' or not re.fullmatch('[0-9][A-Za-z0-9.+:~_-]{0,95}',fields[1]):
                raise SetupError('native_inventory')
            result[name] = fields[1]
        return result

    def audit(self):
        code,data=self.run(['/usr/bin/dpkg','--audit'])
        if code or data.strip():
            raise SetupError('native_recovery_required')

    def postconditions(self, release):
        if any(package['name']=='llama-cpp' for package in release['packages']):
            from .runtime_compat import compatible,validate_installed
            from .releases import private_metadata
            from .pending import _strict
            compatible();validate_installed(_strict(private_metadata(Path('/usr/share/doc/llama-cpp/cpu-profile.json'))))
        for virtual,digest in release['postconditions'].items():
            if virtual not in POSTCONDITIONS:
                raise SetupError('native_postcondition')
            path=Path(virtual)
            info=path.lstat()
            if not stat.S_ISREG(info.st_mode) or info.st_uid!=0 or stat.S_IMODE(info.st_mode)&0o022:
                raise SetupError('native_postcondition')
            with path.open('rb') as stream:
                if hashlib.file_digest(stream,'sha256').hexdigest()!=digest:
                    raise SetupError('native_postcondition')
            code,data=self.run(['/usr/bin/dpkg-query','--search',virtual])
            if code or data.decode('ascii',errors='strict').strip()!=POSTCONDITIONS[virtual]+': '+virtual:
                raise SetupError('native_postcondition')
        self.audit()

    def options(self, directory):
        return ['-o','Dir::Etc::sourcelist='+str(SOURCES),'-o','Dir::Etc::sourceparts=-',
            '-o','Dir::Cache::pkgcache=','-o','Dir::Cache::srcpkgcache=',
            '-o','Dir::Etc::preferences=-','-o','Dir::Etc::preferencesparts=-',
            '-o','Dir::State::lists='+str(directory/'lists'),'-o','Dir::Cache::archives='+str(directory/'archives'),
            '-o','APT::Get::AllowUnauthenticated=false','-o','Acquire::AllowInsecureRepositories=false',
            '-o','Acquire::AllowDowngradeToInsecureRepositories=false','-o','APT::Sandbox::User=_apt',
            '-o','Dpkg::Use-Pty=0','-o','Dpkg::Options::=--force-confold','-o','Dpkg::Options::=--force-confdef']

    def prepare_cache(self, identity):
        from .acquisition_journal import operation_id
        operation_id(identity)
        user=pwd.getpwnam('_apt')
        if user.pw_uid==0:
            raise SetupError('native_sandbox_unavailable')
        for parent in reversed((self.cache,*self.cache.parents)):
            if not parent.exists() and not parent.is_symlink():parent.mkdir(mode=0o755)
            info=parent.lstat()
            if not stat.S_ISDIR(info.st_mode) or info.st_uid!=0 or stat.S_IMODE(info.st_mode)&0o022:
                raise SetupError('native_cache_custody')
        directory=self.cache/identity
        directory.mkdir(mode=0o755)
        for name in ('lists','archives'):
            base=directory/name;base.mkdir(mode=0o755)
            partial=base/'partial';partial.mkdir(mode=0o700);os.chown(partial,user.pw_uid,user.pw_gid)
        return directory

    def downloaded(self,directory,packages):
        expected={p['name']:p for p in packages};found=set()
        verified=directory/'verified-archives';verified.mkdir(mode=0o700)
        (verified/'partial').mkdir(mode=0o700)
        for archive in (directory/'archives').glob('*.deb'):
            info=archive.lstat()
            if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1 or info.st_uid not in (0,pwd.getpwnam('_apt').pw_uid):
                raise SetupError('native_archive_custody')
            code,data=self.run(['/usr/bin/dpkg-deb','--field',str(archive),'Package','Version','Architecture'])
            fields={}
            for line in data.decode('ascii',errors='strict').splitlines():
                key,value=line.split(': ',1)
                if key in fields:raise SetupError('native_archive_changed')
                fields[key]=value
            row=expected.get(fields.get('Package'))
            if code or row is None or row['name'] in found or fields!={'Package':row['name'],'Version':row['version'],'Architecture':row['architecture']} or info.st_size!=row['bytes']:
                raise SetupError('native_archive_changed')
            # Copy into a new root-only inode and verify the actual copy. A
            # downloader-owned open FD cannot mutate these bytes after review.
            frozen=verified/archive.name
            descriptor=os.open(archive,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
            with os.fdopen(descriptor,'rb') as source, frozen.open('xb') as output:
                remaining=row['bytes']
                while remaining:
                    piece=source.read(min(1024**2,remaining))
                    if not piece:raise SetupError('native_archive_changed')
                    output.write(piece);remaining-=len(piece)
                if source.read(1):raise SetupError('native_archive_changed')
                output.flush();os.fsync(output.fileno())
            frozen.chmod(0o400)
            with frozen.open('rb') as stream:
                if frozen.stat().st_size!=row['bytes'] or hashlib.file_digest(stream,'sha256').hexdigest()!=row['sha256']:
                    raise SetupError('native_archive_changed')
            archive=frozen
            code,control=self.run(['/usr/bin/dpkg-deb','--ctrl-tarfile',str(archive)])
            if code:raise SetupError('native_archive_changed')
            with tarfile.open(fileobj=io.BytesIO(control)) as bundle:
                members=bundle.getmembers()
                if any(member.name.removeprefix('./') not in ('','.', 'control','md5sums','conffiles') or not (member.isfile() or member.isdir()) for member in members):
                    raise SetupError('native_activation_script_refused')
            self.payload_policy(archive,row)
            found.add(row['name'])
        if found!=set(expected):
            raise SetupError('native_archive_missing')
        return verified

    @staticmethod
    def payload_policy(archive,row):
        # Streaming read-only inspection, never unpack or run package content.
        from pathlib import PurePosixPath
        child=subprocess.Popen(['/usr/bin/dpkg-deb','--fsys-tarfile',str(archive)],
            stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,stdin=subprocess.DEVNULL,env=ENV)
        total=0
        try:
            with tarfile.open(fileobj=child.stdout,mode='r|') as bundle:
                for member in bundle:
                    path=PurePosixPath(member.name.removeprefix('./'))
                    if path.is_absolute() or '..' in path.parts or member.isdev() or member.isfifo() or member.mode&0o6000 or any('xattr' in key for key in member.pax_headers):
                        raise SetupError('native_payload_policy')
                    value=path.as_posix()
                    if value.lower().endswith('.gguf'):raise SetupError('native_model_payload_refused')
                    if any(part.endswith(('.wants','.requires')) for part in path.parts) or value.startswith((
                        'etc/xdg/autostart/','usr/share/autostart/','etc/cron','etc/init.d/',
                        'usr/lib/systemd/system-preset/','usr/lib/systemd/user-preset/')):
                        raise SetupError('native_activation_payload_refused')
                    if member.isfile():total+=member.size
                    if total>row['installed_bytes']:
                        raise SetupError('native_payload_size')
            if child.wait(timeout=30):raise SetupError('native_payload_policy')
        except BaseException:
            child.kill();child.wait();raise  # Read-only archive inspector only.
        finally:
            child.stdout.close()


    def acquire(self, journal, uid, identity, release, review):
        from .platform import installed_toddy
        installed_toddy()
        local=any(package['name']=='llama-cpp' for package in release['packages'])
        if local:
            from .runtime_compat import compatible,RUNTIME_PROFILE
            if _encode(release.get('runtime_profile'))!=_encode(RUNTIME_PROFILE):raise SetupError('native_runtime_profile_changed')
            compatible()
        self.audit()
        code,architecture=self.run(['/usr/bin/dpkg','--print-architecture'])
        if code or architecture.strip()!=b'amd64':raise SetupError('native_architecture')
        wanted={p['name']:p['version'] for p in release['packages']}
        before=self.query(wanted)
        if any(value is not None and value!=wanted[name] for name,value in before.items()):
            raise SetupError('native_existing_version_conflict')
        if all(before[name]==version for name,version in wanted.items()):
            self.postconditions(release);return journal.state(uid,identity,'installed')
        missing={name:version for name,version in wanted.items() if before[name] is None}
        if journal.get(uid,identity)['cancellation_requested']:
            return journal.state(uid,identity,'canceled')
        import shutil
        if shutil.disk_usage('/').free<2*review['download_bytes']+2*review['installed_bytes']+512*1024**2:
            raise SetupError('native_space')
        directory=self.prepare_cache(identity);options=self.options(directory)
        journal.state(uid,identity,'downloading')
        code,_=self.run(['/usr/bin/apt-get',*options,'update','-o','APT::Update::Error-Mode=any'],timeout=120)
        if code:return journal.state(uid,identity,'deferred',code='offline_or_repository_unavailable')
        indexes=list((directory/'lists').glob('*InRelease'))
        repo=self.catalog.value['repository']
        if len(indexes)!=1 or indexes[0].stat().st_size!=repo['inrelease_bytes'] or sha(indexes[0].read_bytes())!=repo['inrelease_sha256']:
            raise SetupError('native_repository_changed')
        # APT verifies repository signatures; independently require our pinned signer.
        if self.catalog.verify(self.catalog.directory/'archive-keyring.gpg',None,indexes[0])!=self.catalog.fingerprint:
            raise SetupError('native_repository_signature')
        # Snapshot authenticated lists into root-owned immutable inputs before
        # planning/install. APT's downloader can only write its partial cache.
        import shutil
        frozen_lists=directory/'verified-lists';frozen_lists.mkdir(mode=0o755)
        for item in (directory/'lists').iterdir():
            if item.name in ('partial','auxfiles','lock'):continue
            info=item.lstat()
            if not stat.S_ISREG(info.st_mode):raise SetupError('native_repository_changed')
            shutil.copyfile(item,frozen_lists/item.name);(frozen_lists/item.name).chmod(0o444)
        options=[value.replace(str(directory/'lists'),str(frozen_lists)) for value in options]
        packages=[name+'='+version for name,version in wanted.items()]
        common=['--assume-yes','--no-install-recommends','--no-remove']
        code,data=self.run(['/usr/bin/apt-get',*options,*common,'--simulate','install',*packages])
        if code:raise SetupError('native_plan_changed')
        simulation(data,missing)
        code,data=self.run(['/usr/bin/apt-get',*options,*common,'--download-only','install',*packages],timeout=300)
        if code:return journal.state(uid,identity,'deferred',code='offline_or_repository_unavailable')
        if b'unsandboxed as root' in data or b'No sandbox user' in data:
            raise SetupError('native_sandbox_unavailable')
        frozen=self.downloaded(directory,[p for p in release['packages'] if p['name'] in missing])
        options=[value.replace(str(directory/'archives'),str(frozen)) for value in options]
        if journal.get(uid,identity)['cancellation_requested']:
            return journal.state(uid,identity,'canceled')
        self.audit()
        if self.query(wanted)!=before:raise SetupError('native_inventory_changed')
        self.catalog.ensure_current()
        if self.before_write is None:raise SetupError('acquisition_owner_recheck_required')
        self.before_write()
        if local:compatible()
        if journal.get(uid,identity)['cancellation_requested']:
            return journal.state(uid,identity,'canceled')
        # Persist uncertainty BEFORE launching the native package writer. Healthy
        # APT/dpkg has no kill timeout; even cancel/disconnect waits for boundary.
        journal.state(uid,identity,'installing')
        if journal.get(uid,identity)['cancellation_requested']:
            return journal.state(uid,identity,'canceled',code='canceled_before_native_writer')
        code,data=self.run(['/usr/bin/apt-get',*options,*common,'--no-download','install',*packages],timeout=None)
        if code:raise SetupError('native_write_requires_reconciliation')
        if self.query(wanted)!=wanted:raise SetupError('native_postcondition')
        self.postconditions(release)
        return journal.state(uid,identity,'installed')
