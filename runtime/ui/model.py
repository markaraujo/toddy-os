"""Agent-independent state/copy for the native Toddy setup surface."""
import json
import os
from pathlib import Path
import uuid

from runtime.setup.pending import Catalog, PendingStore, SetupError


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
