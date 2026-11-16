"""Bounded owner/FD/restore contracts on actual canonical SQLite, no provider."""
import fcntl
import json
import os
from pathlib import Path
import tempfile
import unittest

from runtime.broker.memory_api import MemoryAPI, MemoryAPIError, MemoryEngine, parse_projection
from runtime.broker.memory_control import MemoryControl, sealed_export, sealed_import, SEALS
from runtime.broker.profiles import ProfileStore, ProfileError

ROOT = Path(__file__).resolve().parents[1]


class ControlTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.owner = True
        schema = json.loads((ROOT / 'config/phase2/profile.schema.json').read_text())
        config = (ROOT / 'config/phase2/profile/config.json').read_bytes()
        self.profiles = ProfileStore(Path(self.tmp.name) / 'profile', 'toddy-default', schema,
            capabilities={'tools': {'system-info'}, 'skills': {'explain-system'}})
        self.original = self.profiles.apply({'config.json': config}, expected_revision=None)
        self.api = MemoryAPI(self.profiles, owner_allowed=lambda: self.owner)
        self.control = MemoryControl(self.api)

    def mutate(self, op, **fields):
        page = self.control.page()
        return self.control.mutate(page['profile_revision'], json.dumps({'version': 1,
            'memory_generation': page['memory_generation'], 'operation': op, **fields}))

    def test_actual_owner_edit_metadata_generation_cas_and_delete(self):
        first = self.control.page()
        result = self.mutate('put', id='language', text='Portuguese', expires=None)
        self.assertNotIn('records', result)
        self.assertNotIn('Portuguese', json.dumps(result))
        self.assertEqual(self.control.page()['records'][0]['text'], 'Portuguese')
        # Same USER bytes can keep the profile revision while generation changes.
        again = self.mutate('put', id='language', text='Portuguese', expires=None)
        self.assertEqual(again['profile_revision'], result['profile_revision'])
        with self.assertRaisesRegex(MemoryAPIError, 'stale_memory_generation'):
            self.control.mutate(result['profile_revision'], json.dumps({'version':1,
                'memory_generation':result['memory_generation'],'operation':'delete','id':'language'}))
        self.mutate('delete', id='language')
        self.assertEqual(self.control.page()['records'], [])
        self.owner = False
        with self.assertRaisesRegex(MemoryAPIError, 'authenticated_owner'):
            self.control.page()

    def test_sealed_backup_restore_cannot_resurrect_current_tombstone(self):
        self.mutate('put', id='language', text='Portuguese', expires=None)
        page = self.control.page()
        descriptor = self.control.export(page['profile_revision'], page['memory_generation'])
        self.addCleanup(os.close, descriptor)
        self.assertEqual(fcntl.fcntl(descriptor, fcntl.F_GET_SEALS) & SEALS, SEALS)
        with self.assertRaises(OSError): os.write(descriptor, b'changed')
        self.mutate('delete', id='language')
        current = self.control.page()
        self.control.restore(current['profile_revision'], current['memory_generation'], descriptor)
        self.assertEqual(self.control.page()['records'], [])
        raw = Path(self.tmp.name) / 'unsealed'; raw.write_bytes(sealed_import(descriptor)); raw.chmod(0o600)
        with raw.open('rb') as source, self.assertRaisesRegex(MemoryAPIError, 'transfer'):
            self.control.restore(current['profile_revision'], current['memory_generation'], source.fileno())

    def test_manual_notes_preserved_in_settings_but_only_explicit_review_converts(self):
        files = self.profiles.snapshot(); files['USER.md'] = b'An owner manual note, awaiting review.'
        old = self.profiles.apply(files, expected_revision=self.original)
        page = self.control.page()
        self.assertTrue(page['user_document_review_required']); self.assertNotIn('user_document', page)
        descriptor = self.control.export_document(old, page['memory_generation'])
        try: self.assertEqual(sealed_import(descriptor), files['USER.md'])
        finally: os.close(descriptor)
        config = json.loads(files['config.json']); config['display_name'] = 'Edited settings'
        files['config.json'] = json.dumps(config).encode()
        self.api.apply_profile(files, expected_revision=old)
        self.assertEqual(self.profiles.snapshot()['USER.md'], b'An owner manual note, awaiting review.')
        self.mutate('review-user-document', preferences={'note':'Owner explicitly selected preference'},
            reviewed_user_sha256=self.control.page()['user_document_sha256'])
        self.assertEqual(parse_projection(self.profiles.snapshot()['USER.md']), {'note':'Owner explicitly selected preference'})

    def test_profile_restore_keeps_current_memory_and_repairs_corrupt_config(self):
        self.mutate('put', id='language', text='Portuguese', expires=None)
        saved = self.profiles.current()
        self.mutate('delete', id='language')
        self.api.restore_profile(saved, expected_revision=self.profiles.current())
        self.assertEqual(self.control.page()['records'], [])
        self.assertEqual(parse_projection(self.profiles.snapshot()['USER.md']), {})
        files = self.profiles.snapshot(); config=json.loads(files['config.json']);config['display_name']='Corrupt candidate'
        files['config.json']=json.dumps(config).encode()
        broken = self.profiles.apply(files, expected_revision=self.profiles.current())
        with self.profiles._db() as db: db.execute("UPDATE profile_revisions SET bundle='{}' WHERE revision=?", (broken,))
        self.assertTrue(self.api.restore_profile(saved, expected_revision=broken)['restored'])
        self.assertEqual(parse_projection(self.profiles.snapshot()['USER.md']), {})

    def test_expiry_during_settings_apply_removes_stale_structured_projection(self):
        now=[1000.]; self.api.clock=lambda:now[0]
        self.api.put('expires', 'Expires soon', expected_revision=self.profiles.current(), expires=1001.)
        files=self.profiles.snapshot(); now[0]=1002.
        expected=self.profiles.current(); staged=self.profiles.validate(files)[0]
        with self.assertRaisesRegex(MemoryAPIError,'revalidate'):
            self.api.apply_profile(files, expected_revision=expected, validated_revision=staged)
        self.assertEqual(self.profiles.current(),expected)
        result=self.api.apply_profile(files, expected_revision=expected)
        self.assertEqual(parse_projection(self.profiles.snapshot()['USER.md']), {})
        self.assertGreater(result['memory_generation'], 1)

    def test_pages_are_bounded_and_documents_never_leak_into_metadata(self):
        self.mutate('put', id='one', text='a'*4096, expires=None)
        self.mutate('put', id='two', text='b'*4096, expires=None)
        page=self.control.page(limit=1)
        self.assertFalse(page['complete']); self.assertEqual(len(page['records']),1)
        tail=self.control.page(page['next_cursor'],1)
        self.assertTrue(tail['complete']); self.assertEqual(tail['records'][0]['id'],'two')
        self.assertLess(len(json.dumps(page).encode()),49152)
        with self.assertRaises(MemoryAPIError): self.control.page(limit=10000)
        with self.assertRaises(MemoryAPIError): self.control.mutate(self.profiles.current(), '{"version":1,"operation":"grant-root"}')


if __name__=='__main__': unittest.main()
