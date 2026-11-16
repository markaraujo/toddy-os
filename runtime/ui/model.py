"""Agent-independent state/copy for the native Toddy setup surface."""
import json
import fcntl
import stat
import tempfile
import os
from pathlib import Path
import uuid

from ..setup.pending import Catalog, PendingStore, SetupError


class SetupModel:
    def __init__(self, data_root, state_directory, locale='en'):
        self.root = Path(data_root)
        self.locale = 'pt-BR' if locale.replace('_', '-').lower().startswith('pt') else 'en'
        self.catalog = Catalog((self.root / 'config/phase2/software-catalog.json').read_bytes())
        copy = json.loads((self.root / 'ui/phase2/messages.json').read_text(encoding='utf-8'))
        self.messages = {row['id']: row['text'] for row in copy['messages']}
        self.store = PendingStore(state_directory, self.catalog)
        try:
            self.manifest, self.revision = self.store.load()
            if self.manifest is None:
                # A local setup identity is not proof of a tested installation.
                self.store.create('user-' + uuid.uuid4().hex)
                self.reload()
        except Exception:
            self.store.close()
            raise

    def close(self):
        self.store.close()

    def text(self, key):
        return self.messages[key][self.locale]

    def reload(self):
        self.manifest, self.revision = self.store.load()
        if self.manifest is None:
            raise SetupError('manifest_missing')

    def choose_backend(self, mode):
        if mode not in ('later', 'api', 'local'):
            raise SetupError('invalid_backend_choice')
        self.manifest['ai_choice'] = mode
        self.revision = self.store.save(self.manifest, expected_revision=self.revision)

    def defer(self):
        self.choose_backend('later')
        self.revision = self.store.dismiss(expected_revision=self.revision)
        self.reload()

    def software(self):
        """All catalog candidates are informational and unselectable in this slice."""
        deferred = {item['id'] for item in self.manifest['choices']}
        rows = []
        for candidate in self.catalog.candidates.values():
            if candidate['default'] == 'required':
                continue
            rows.append({'id': candidate['id'], 'name': candidate['name'],
                         'description': candidate['description'][self.locale],
                         'pending': candidate['id'] in deferred,
                         'can_install': False, 'status': self.text('software.unavailable')})
        return rows


def state_directory():
    """Resolve the user's state home without accepting relative XDG overrides."""
    base = Path(os.environ.get('XDG_STATE_HOME') or Path.home() / '.local/state')
    if not base.is_absolute():
        raise SetupError('state_directory')
    # Create only the ordinary user-state parents. PendingStore validates the
    # private final directory and refuses symlink components before writing state.
    parent = base / 'toddy'
    for component in (parent, *parent.parents):
        if component.is_symlink():
            raise SetupError('state_directory')
    parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    return parent / 'setup'


def open_profile_import(path):
    """Explicit native file selection only; return a bounded readonly regular FD."""
    path=Path(path)
    if not path.is_absolute():raise ValueError('profile_import_path')
    descriptor=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
    try:
        info=os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or not 0<info.st_size<=8*1024*1024:
            raise ValueError('profile_import_file')
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def save_profile_export(descriptor,path):
    """Publish an explicit private export atomically without overwriting a file."""
    path=Path(path)
    info=os.fstat(descriptor)
    if not path.is_absolute() or not stat.S_ISREG(info.st_mode) or not 0<info.st_size<=8*1024*1024:
        raise ValueError('profile_export_file')
    required=fcntl.F_SEAL_WRITE|fcntl.F_SEAL_GROW|fcntl.F_SEAL_SHRINK
    if fcntl.fcntl(descriptor,fcntl.F_GET_SEALS)&required!=required:
        raise ValueError('profile_export_unsealed')
    data=os.pread(descriptor,8*1024*1024+1,0)
    if len(data)!=info.st_size:raise ValueError('profile_export_bound')
    fd,temporary=tempfile.mkstemp(prefix='.toddy-profile-',dir=path.parent)
    temporary=Path(temporary)
    try:
        os.fchmod(fd,0o600)
        with os.fdopen(fd,'wb',closefd=False) as stream:
            stream.write(data);stream.flush();os.fsync(fd)
        # link is atomic and refuses an existing destination, including a symlink.
        os.link(temporary,path,follow_symlinks=False)
        temporary.unlink()
        directory=os.open(path.parent,os.O_DIRECTORY|os.O_CLOEXEC)
        try:os.fsync(directory)
        finally:os.close(directory)
    finally:
        os.close(fd)
        temporary.unlink(missing_ok=True)
