"""Owned named-profile catalog; independent canonical stores and metadata locators.

Registry operations never switch a running core, dispatch/replay tasks, copy a
state database, query credentials or execute imported instructions. The service
captures each task's core/profile revision before dispatch and binds its locator.
"""
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import stat

try:
    from .profiles import ProfileStore,ProfileError,_schema,_identifier
    from .protocol import strict_json
    from .skill_documents import profile_path
except ImportError:
    from profiles import ProfileStore,ProfileError,_schema,_identifier
    from protocol import strict_json
    from skill_documents import profile_path

MAX_BUNDLE=8*1024*1024
FILES={'config.json','SOUL.md','IDENTITY.md','USER.md','AGENTS.md'}
PERSONA={'SOUL.md','IDENTITY.md','AGENTS.md'}
REVISION=re.compile(r'[0-9a-f]{64}\Z')
TASK=re.compile(r'[a-zA-Z0-9_-]{1,128}\Z')
EMPTY_USER=b'# Explicit preferences\n\n<!-- toddy-memory-v1 -->\n```json\n{}\n```\n'


class RegistryError(ProfileError):pass


def _encode(value):
    return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode('utf-8')


def _private(path,mode,*,directory=False):
    if not path.is_absolute() or path.resolve()!=path:
        raise RegistryError('unsafe_registry_path')
    info=path.lstat()
    if info.st_uid!=os.getuid() or stat.S_IMODE(info.st_mode)!=mode or \
            (directory and not stat.S_ISDIR(info.st_mode)) or \
            (not directory and (not stat.S_ISREG(info.st_mode) or info.st_nlink!=1)):
        raise RegistryError('unsafe_registry_custody')


class ProfileRegistry:
    def __init__(self,root,schema,defaults,*,capabilities=None,profile_limit=32,locator_limit=10000,
                 legacy_default_directory=None):
        self.root=Path(root)
        if not self.root.is_absolute() or self.root.resolve()!=self.root or \
                type(profile_limit) is not int or not 1<=profile_limit<=128 or \
                type(locator_limit) is not int or not 1<=locator_limit<=100000:
            raise RegistryError('unsafe_registry_configuration')
        self.root.mkdir(mode=0o700,exist_ok=True)
        _private(self.root,0o700,directory=True)
        self.legacy_default_directory=Path(legacy_default_directory) if legacy_default_directory is not None else None
        if self.legacy_default_directory is not None:
            _private(self.legacy_default_directory,0o700,directory=True)
        self.schema=schema
        self.defaults=dict(defaults)
        self.capabilities=capabilities or {'adapters':set(),'tools':{'system-info'},
            'skills':{'explain-system'},'extensions':set(),'workflows':set()}
        self.profile_limit=profile_limit
        self.locator_limit=locator_limit
        self.path=self.root/'catalog.sqlite'
        fd=os.open(self.path,os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
        os.close(fd)
        _private(self.path,0o600)
        with self._db() as db:
            tables={row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if tables:
                if not {'registry_schema','profiles','selected_profile','task_locators'}.issubset(tables):
                    raise RegistryError('registry_schema_incomplete')
                if [row[0] for row in db.execute('SELECT version FROM registry_schema')]!=[1]:
                    raise RegistryError('unsupported_registry_schema')
            else:
                # Initialize the complete catalog atomically. A crash cannot
                # publish an unversioned/half-created catalog as ready state.
                db.executescript('''BEGIN IMMEDIATE;
                    CREATE TABLE registry_schema(version INTEGER NOT NULL);
                    INSERT INTO registry_schema VALUES(1);
                    CREATE TABLE profiles(profile_id TEXT PRIMARY KEY,status TEXT NOT NULL,
                        initial_revision TEXT NOT NULL);
                    CREATE TABLE selected_profile(id INTEGER PRIMARY KEY CHECK(id=1),
                        profile_id TEXT,generation INTEGER NOT NULL);
                    INSERT INTO selected_profile VALUES(1,NULL,0);
                    CREATE TABLE task_locators(task_id TEXT PRIMARY KEY,
                        profile_id TEXT NOT NULL,revision TEXT NOT NULL);
                    COMMIT;''')

    @contextmanager
    def _db(self):
        _private(self.path,0o600)
        db=sqlite3.connect(self.path,isolation_level=None,timeout=2)
        db.row_factory=sqlite3.Row
        db.execute('PRAGMA synchronous=FULL')
        try:yield db
        finally:db.close()

    @contextmanager
    def _lock(self):
        path=self.root/'.registry.lock'
        fd=os.open(path,os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
        try:
            _private(path,0o600)
            try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:raise RegistryError('registry_busy') from None
            yield
        finally:os.close(fd)

    @contextmanager
    def _transaction(self):
        with self._db() as db:
            db.execute('BEGIN IMMEDIATE')
            try:
                yield db
                db.execute('COMMIT')
            except BaseException:
                db.execute('ROLLBACK')
                raise

    def _validate(self,profile_id,files):
        # Reuse the canonical byte validator, whose documented operation is pure
        # and accesses only schema/identity/capabilities; do not create a DB just
        # to discover invalid input. ProfileStore.apply repeats the same checks.
        validator=ProfileStore.__new__(ProfileStore)
        validator.profile_id=profile_id
        validator.schema=self.schema
        validator.capabilities=self.capabilities
        return validator.validate(files)

    def _portable(self,profile_id,files):
        _identifier(profile_id)
        if not isinstance(files,dict) or 'config.json' not in files or not 1<=len(files)<=128:
            raise RegistryError('unsupported_bundle_path')
        for name,data in files.items():
            try:limit,_=profile_path(name)
            except (ValueError,TypeError):raise RegistryError('unsupported_bundle_path') from None
            if type(data) is not bytes or len(data)>limit:
                raise RegistryError('profile_file_limit')
        try:config=strict_json(files['config.json'])
        except (ValueError,UnicodeError,RecursionError,OverflowError):
            raise RegistryError('invalid_profile_json') from None
        _schema(config,self.schema)  # Unknown grant/key fields are rejected before sanitizing.
        config['profile_id']=profile_id
        config['provider']={'mode':'deferred','adapter_id':None,'model_id':None,
                            'connection_ref':None,'allow_remote_fallback':False}
        config['budgets']['remote_spending_enabled']=False
        config['memory']={'history_enabled':False,'retention_days':0}
        config['automation']={'enabled':False,'workflow_ids':[]}
        config['extensions']={'enabled':[]}
        config['tools']={'enabled':['system-info'] if 'system-info' in self.capabilities.get('tools',()) else []}
        # Data-only selected skill documents survive an explicit owner import;
        # tools/extensions/provider/automation authority is reset independently.
        clean={name:data for name,data in files.items() if name in PERSONA or name.startswith('skills/')}
        clean['config.json']=_encode(config)
        clean['USER.md']=EMPTY_USER
        self._validate(profile_id,clean)
        return clean

    def _directory(self,profile_id):
        _identifier(profile_id)
        if profile_id=='toddy-default' and self.legacy_default_directory is not None:
            return self.legacy_default_directory
        return self.root/profile_id

    def _new_store(self,profile_id):
        return ProfileStore(self._directory(profile_id),profile_id,self.schema,capabilities=self.capabilities)

    def _verified_existing(self,profile_id,expected=None,*,allow_recovery=False):
        directory=self._directory(profile_id)
        path=directory/'state.sqlite'
        try:
            _private(directory,0o700,directory=True)
            _private(path,0o600)
            # Read-only postcondition first. A missing/partial DB must not be
            # created, migrated or have an uncertain apply replayed on resume.
            db=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True,timeout=2)
            try:row=db.execute('SELECT profile_id,revision FROM profile_current WHERE id=1').fetchone()
            finally:db.close()
            if row is None or row[0]!=profile_id or not isinstance(row[1],str) or not REVISION.fullmatch(row[1]) or \
                    (expected is not None and row[1]!=expected):
                raise RegistryError('profile_postcondition_unverified')
        except (OSError,sqlite3.Error):
            raise RegistryError('profile_postcondition_unverified') from None
        store=self._new_store(profile_id)
        if not allow_recovery:
            store.snapshot(row[1])
        return store

    def _publish(self,profile_id,expected):
        self._verified_existing(profile_id,expected)
        with self._transaction() as db:
            changed=db.execute("UPDATE profiles SET status='ready' WHERE profile_id=? AND status='preparing' AND initial_revision=?",
                               (profile_id,expected)).rowcount
            if changed!=1:raise RegistryError('profile_publication_conflict')

    def create(self,profile_id,files=None):
        """Create without selecting; invalid input changes neither active profile nor DB."""
        clean=self._portable(profile_id,self.defaults if files is None else files)
        revision,_,_=self._validate(profile_id,clean)
        with self._lock():
            directory=self._directory(profile_id)
            if directory.exists() or directory.is_symlink():raise RegistryError('profile_directory_exists')
            with self._transaction() as db:
                if db.execute('SELECT 1 FROM profiles WHERE profile_id=?',(profile_id,)).fetchone():
                    raise RegistryError('profile_exists')
                if db.execute('SELECT count(*) FROM profiles').fetchone()[0]>=self.profile_limit:
                    raise RegistryError('profile_limit')
                db.execute("INSERT INTO profiles VALUES(?,'preparing',?)",(profile_id,revision))
            store=self._new_store(profile_id)
            actual=store.apply(clean,expected_revision=None)
            if actual!=revision:raise RegistryError('profile_postcondition_unverified')
            self._publish(profile_id,revision)
        return {'profile_id':profile_id,'profile_revision':revision,'selected':False}

    def adopt_existing(self,profile_id,*,allow_recovery=False):
        """Explicit legacy-store registration after actual custody/postcondition checks.

        This preserves existing revisions/tasks/preferences/routing. It is not
        clone/import, never selects a profile and cannot publish a preparing row.
        """
        _identifier(profile_id)
        with self._lock():
            store=self._verified_existing(profile_id,allow_recovery=allow_recovery)
            revision=store.current()
            with self._transaction() as db:
                row=db.execute('SELECT status FROM profiles WHERE profile_id=?',(profile_id,)).fetchone()
                if row is not None and row['status']!='ready':
                    raise RegistryError('profile_publication_conflict')
                if row is None:
                    if db.execute('SELECT count(*) FROM profiles').fetchone()[0]>=self.profile_limit:
                        raise RegistryError('profile_limit')
                    db.execute("INSERT INTO profiles VALUES(?,'ready',?)",(profile_id,revision))
        return {'profile_id':profile_id,'profile_revision':revision,'selected':False,'adopted':True}

    def reconcile_prepared(self,profile_id):
        """Publish only actual verified postconditions; never repeat create/apply."""
        _identifier(profile_id)
        with self._lock():
            with self._db() as db:
                row=db.execute('SELECT status,initial_revision FROM profiles WHERE profile_id=?',(profile_id,)).fetchone()
            if row is None:raise RegistryError('unknown_profile')
            if row['status']=='ready':return {'profile_id':profile_id,'status':'ready'}
            try:self._publish(profile_id,row['initial_revision'])
            except (ProfileError,OSError,sqlite3.Error):
                return {'profile_id':profile_id,'status':'held','reason':'profile_postcondition_unverified'}
        return {'profile_id':profile_id,'status':'ready'}

    def store(self,profile_id,*,allow_recovery=False):
        _identifier(profile_id)
        with self._db() as db:
            row=db.execute("SELECT 1 FROM profiles WHERE profile_id=? AND status='ready'",(profile_id,)).fetchone()
        if row is None:raise RegistryError('unknown_or_unready_profile')
        return self._verified_existing(profile_id,allow_recovery=allow_recovery)

    def active(self):
        with self._db() as db:
            row=db.execute('SELECT profile_id,generation FROM selected_profile WHERE id=1').fetchone()
        return {'profile_id':row['profile_id'],'generation':row['generation']}

    def select(self,profile_id,*,expected_generation):
        if type(expected_generation) is not int or not 0<=expected_generation<2**53-1:
            raise RegistryError('invalid_registry_generation')
        with self._lock():
            self.store(profile_id)
            with self._transaction() as db:
                row=db.execute('SELECT profile_id,generation FROM selected_profile WHERE id=1').fetchone()
                if row['generation']!=expected_generation:raise RegistryError('stale_registry_generation')
                generation=expected_generation+(row['profile_id']!=profile_id)
                db.execute('UPDATE selected_profile SET profile_id=?,generation=? WHERE id=1',(profile_id,generation))
        return {'profile_id':profile_id,'generation':generation}

    def list_profiles(self):
        selected=self.active()
        with self._db() as db:
            ids=[row[0] for row in db.execute("SELECT profile_id FROM profiles WHERE status='ready' ORDER BY profile_id")]
        result=[]
        for profile_id in ids:
            try:
                store=self.store(profile_id)
                revision=store.current()
                config=strict_json(store.snapshot(revision)['config.json'])
                row={'profile_id':profile_id,'display_name':config['display_name'],
                     'profile_revision':revision,'status':'ready'}
            except (ProfileError,OSError,sqlite3.Error):
                row={'profile_id':profile_id,'display_name':profile_id,
                     'profile_revision':None,'status':'recovery_required'}
            row['selected']=profile_id==selected['profile_id']
            result.append(row)
        return {'version':1,'generation':selected['generation'],'profiles':result}

    def clone(self,source_id,target_id,*,expected_revision):
        source=self.store(source_id)
        if source.current()!=expected_revision:raise RegistryError('stale_profile_revision')
        files=source.snapshot(expected_revision)
        return self.create(target_id,files)

    def export_bundle(self,profile_id,*,revision=None):
        source=self.store(profile_id)
        clean=self._portable(profile_id,source.snapshot(revision))
        files={name:data.decode('utf-8') for name,data in sorted(clean.items())}
        value={'bundle_version':1,'scope':'profile-without-memory-or-authority',
               'routing':'deferred-rebind-required','files':files,
               'sha256':{name:hashlib.sha256(data).hexdigest() for name,data in sorted(clean.items())}}
        data=_encode(value)
        if len(data)>MAX_BUNDLE:raise RegistryError('bundle_size')
        return data

    def decode_bundle(self,profile_id,data):
        if type(data) is not bytes or not 0<len(data)<=MAX_BUNDLE:raise RegistryError('bundle_size')
        try:value=strict_json(data)
        except (ValueError,UnicodeError,RecursionError,OverflowError):raise RegistryError('bundle_json') from None
        if not isinstance(value,dict) or set(value)!={'bundle_version','scope','routing','files','sha256'} or \
                type(value['bundle_version']) is not int or value['bundle_version']!=1 or \
                value['scope']!='profile-without-memory-or-authority' or value['routing']!='deferred-rebind-required' or \
                not isinstance(value['files'],dict) or not isinstance(value['sha256'],dict) or \
                not 0<len(value['files'])<=128 or set(value['files'])!=set(value['sha256']):
            raise RegistryError('bundle_schema')
        files={}
        for name,text in value['files'].items():
            if not isinstance(text,str):raise RegistryError('bundle_file')
            actual=text.encode('utf-8')
            if hashlib.sha256(actual).hexdigest()!=value['sha256'][name]:raise RegistryError('bundle_integrity')
            files[name]=actual
        return self._portable(profile_id,files)

    def import_bundle(self,profile_id,data):
        return self.create(profile_id,self.decode_bundle(profile_id,data))

    @staticmethod
    def read_fd(descriptor):
        if type(descriptor) is not int or not 0<=descriptor<=2**31-1:raise RegistryError('bundle_fd')
        try:
            before=os.fstat(descriptor)
            if not stat.S_ISREG(before.st_mode) or before.st_uid!=os.getuid() or not 0<before.st_size<=MAX_BUNDLE:
                raise RegistryError('bundle_fd')
            data=os.pread(descriptor,MAX_BUNDLE+1,0)
            after=os.fstat(descriptor)
            identity=lambda info:(info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns,info.st_ctime_ns)
            if identity(before)!=identity(after) or len(data)!=before.st_size:raise RegistryError('bundle_fd_changed')
        except OSError:raise RegistryError('bundle_fd') from None
        return data

    def import_fd(self,profile_id,descriptor):
        return self.import_bundle(profile_id,self.read_fd(descriptor))

    def export_fd(self,profile_id,*,revision=None):
        data=self.export_bundle(profile_id,revision=revision)
        descriptor=os.memfd_create('toddy-profile-export',os.MFD_CLOEXEC|os.MFD_ALLOW_SEALING)
        try:
            os.fchmod(descriptor,0o600)
            view=memoryview(data)
            while view:view=view[os.write(descriptor,view):]
            fcntl.fcntl(descriptor,fcntl.F_ADD_SEALS,
                fcntl.F_SEAL_SEAL|fcntl.F_SEAL_WRITE|fcntl.F_SEAL_GROW|fcntl.F_SEAL_SHRINK)
            return os.open('/proc/self/fd/'+str(descriptor),os.O_RDONLY|os.O_CLOEXEC)
        finally:os.close(descriptor)

    def bind_task(self,task_id,profile_id):
        if not isinstance(task_id,str) or not TASK.fullmatch(task_id):raise RegistryError('invalid_task_id')
        store=self.store(profile_id,allow_recovery=True)
        revision,_=store.task_snapshot(task_id)
        with self._lock(),self._transaction() as db:
            old=db.execute('SELECT profile_id,revision FROM task_locators WHERE task_id=?',(task_id,)).fetchone()
            if old:
                if (old['profile_id'],old['revision'])!=(profile_id,revision):raise RegistryError('task_locator_conflict')
            else:
                if db.execute('SELECT count(*) FROM task_locators').fetchone()[0]>=self.locator_limit:
                    raise RegistryError('task_locator_limit')
                db.execute('INSERT INTO task_locators VALUES(?,?,?)',(task_id,profile_id,revision))
        return {'task_id':task_id,'profile_id':profile_id,'profile_revision':revision}

    def locate_task(self,task_id):
        if not isinstance(task_id,str) or not TASK.fullmatch(task_id):raise RegistryError('invalid_task_id')
        with self._db() as db:
            row=db.execute('SELECT profile_id,revision FROM task_locators WHERE task_id=?',(task_id,)).fetchone()
        if row is None:raise RegistryError('unknown_task_locator')
        actual,_=self.store(row['profile_id'],allow_recovery=True).task_snapshot(task_id)
        if actual!=row['revision']:raise RegistryError('task_locator_corrupt')
        return {'task_id':task_id,'profile_id':row['profile_id'],'profile_revision':actual}
