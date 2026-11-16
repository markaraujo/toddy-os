"""Stage/import checks for offline assistant payload; no archive/guest installation."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('assistant_package',ROOT/'scripts/build/phase2/assistant_package.py')
package=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(package)


class AssistantPackageTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name)
        self.stage=self.base/'stage'
        self.manifest=package.stage(ROOT,self.stage)

    def test_stage_is_deterministic_and_excludes_agent_credentials_and_maintainer_scripts(self):
        other=self.base/'second'
        other_manifest=package.stage(ROOT,other)
        self.assertEqual(self.manifest,other_manifest)
        paths={str(path.relative_to(self.stage)) for path in self.stage.rglob('*') if path.is_file()}
        self.assertEqual(paths,{str(path.relative_to(other)) for path in other.rglob('*') if path.is_file()})
        for name in paths:
            self.assertEqual((self.stage/name).read_bytes(),(other/name).read_bytes())
            self.assertEqual((self.stage/name).stat().st_mtime_ns,0)
        for name in ['broker','worker','executor','engine','voice','integrations']:
            self.assertFalse((self.stage/'usr/lib/toddy'/name).exists())
        self.assertFalse((self.stage/'DEBIAN').exists())
        self.assertFalse((self.stage/'usr/lib/toddy/runtime').exists())
        self.assertFalse(list(self.stage.rglob('*.sqlite')))
        self.assertFalse(list(self.stage.rglob('pending.json')))
        self.assertEqual(self.manifest['maintainer_scripts'],[])
        self.assertFalse(self.manifest['native_archive_built'])
        self.assertFalse(self.manifest['installed'])
        self.assertIsNone(self.manifest['active_global_shortcut'])

    def test_exact_launcher_desktop_namespace_legal_and_asset_custody(self):
        launcher=(self.stage/'usr/bin/toddy').read_text()
        self.assertTrue(launcher.startswith('#!/usr/bin/python3 -I\n'))
        self.assertIn("sys.path.insert(0, '/usr/lib')",launcher)
        self.assertIn("runpy.run_module('toddy.ui.app'",launcher)
        self.assertNotIn('PYTHONPATH',launcher.splitlines()[-1])
        self.assertEqual((self.stage/'usr/bin/toddy').stat().st_mode&0o777,0o755)
        desktop=(self.stage/'usr/share/applications/io.github.markaraujo.Toddy.desktop').read_text()
        self.assertIn('Exec=/usr/bin/toddy\n',desktop)
        self.assertIn('Icon=io.github.markaraujo.Toddy\n',desktop)
        self.assertNotIn('@TODDY_EXECUTABLE@',desktop)
        self.assertNotIn('pkexec',desktop)
        self.assertFalse((self.stage/'usr/share/pixmaps').exists())
        asset=self.manifest['original_asset_references'][0]
        self.assertEqual(asset['payload_owner'],'toddy-branding')
        self.assertFalse(asset['copied_by_this_package'])
        self.assertEqual(asset['sha256'],hashlib.sha256((ROOT/asset['source']).read_bytes()).hexdigest())
        for path,row in self.manifest['payload'].items():
            actual=self.stage/path.lstrip('/')
            self.assertEqual(row['sha256'],hashlib.sha256(actual.read_bytes()).hexdigest())
            self.assertEqual(int(row['mode'],8),actual.stat().st_mode&0o777)
        self.assertEqual((self.stage/'usr/share/doc/toddy-assistant/copyright').read_bytes(),(ROOT/'LICENSE').read_bytes())
        self.assertEqual(self.manifest['source_inputs']['runtime/ui/app.py']['sha256'],
                         hashlib.sha256((ROOT/'runtime/ui/app.py').read_bytes()).hexdigest())
        self.assertNotIn(str(ROOT),json.dumps(self.manifest))
        self.assertNotIn(str(self.stage),json.dumps(self.manifest))

    def test_existing_or_symlinked_destination_is_never_replayed(self):
        before=(self.stage/'usr/bin/toddy').read_bytes()
        with self.assertRaisesRegex(package.StageError,'fresh_canonical_stage_required'):
            package.stage(ROOT,self.stage)
        link=self.base/'link'
        link.symlink_to(self.stage,target_is_directory=True)
        with self.assertRaisesRegex(package.StageError,'fresh_canonical_stage_required'):
            package.stage(ROOT,link)
        self.assertEqual((self.stage/'usr/bin/toddy').read_bytes(),before)

    def test_changed_approved_icon_and_symlinked_source_are_refused_before_staging(self):
        repository=self.base/'source-copy'
        repository.mkdir()
        for relative in self.manifest['source_inputs']:
            target=repository/relative
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes((ROOT/relative).read_bytes())
        icon=repository/'assets/brand/toddy-os-system-icon.png'
        original=icon.read_bytes()
        icon.write_bytes(original+b'changed')
        first=self.base/'bad-icon-stage'
        with self.assertRaisesRegex(package.StageError,'approved_icon_integrity'):
            package.stage(repository,first)
        self.assertFalse(first.exists())
        icon.write_bytes(original)
        source=repository/'runtime/ui/app.py'
        source.unlink()
        source.symlink_to(ROOT/'runtime/ui/app.py')
        second=self.base/'bad-source-stage'
        with self.assertRaisesRegex(package.StageError,'symlink_source_refused'):
            package.stage(repository,second)
        self.assertFalse(second.exists())

    def test_actual_staged_modules_import_in_isolated_installed_namespace_without_agent(self):
        malicious=self.base/'malicious'
        malicious.mkdir()
        (malicious/'toddy.py').write_text("raise RuntimeError('untrusted cwd import')")
        code='''
import sys
from pathlib import Path
sys.dont_write_bytecode=True
root=Path(sys.argv[1])
sys.path.insert(0,str(root/'usr/lib'))
from toddy.ui.model import SetupModel
from toddy.ui.task_state import TaskText
from toddy.connections.secret_store import ProtectedStore
import toddy.ui.model as model
assert Path(model.__file__).is_relative_to(root/'usr/lib/toddy')
setup=SetupModel(root/'usr/share/toddy',Path(sys.argv[2]),'pt-BR')
setup.defer()
assert setup.manifest['ai_choice']=='later'
assert setup.manifest['invitation_dismissed']
assert all(not row['can_install'] for row in setup.software())
assert not any(key.startswith(('toddy.broker','toddy.engine','toddy.executor')) for key in sys.modules)
assert 'gi.repository.Secret' not in sys.modules
setup.close()
print('ACTUAL_STAGED_OFFLINE_IMPORT_AND_DEFERRED_PASS')
'''
        result=subprocess.run([sys.executable,'-I','-c',code,str(self.stage),str(self.base/'user-state')],
            cwd=malicious,env=dict(os.environ,PYTHONPATH=str(malicious)),capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn('ACTUAL_STAGED_OFFLINE_IMPORT_AND_DEFERRED_PASS',result.stdout)
        self.assertFalse(list(self.stage.rglob('__pycache__')))

    def test_actual_staged_gtk_widgets_open_deferred_without_agent(self):
        if importlib.util.find_spec('gi') is None or shutil.which('dbus-run-session') is None or \
                not (os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')):
            self.skipTest('optional host GTK/display absent; installed guest qualification remains required')
        code='''
import sys
from pathlib import Path
sys.dont_write_bytecode=True
root=Path(sys.argv[1])
sys.path.insert(0,str(root/'usr/lib'))
from toddy.ui.model import SetupModel
from toddy.ui.app import ToddyApplication,SetupWindow
from gi.repository import Gtk,Adw,GLib
Gtk.init();Adw.init()
model=SetupModel(root/'usr/share/toddy',Path(sys.argv[2]),'pt-BR')
app=ToddyApplication(model);app.register(None)
window=SetupWindow(app,model)
while GLib.MainContext.default().pending():GLib.MainContext.default().iteration(False)
assert not window.entry.get_sensitive()
assert not window.send_button.get_sensitive()
assert not window.run_button.get_sensitive()
assert not window.profile_validate.get_sensitive()
window._defer()
assert model.manifest['ai_choice']=='later' and model.manifest['invitation_dismissed']
assert not any(key.startswith(('toddy.broker','toddy.engine','toddy.executor')) for key in sys.modules)
assert 'gi.repository.Secret' not in sys.modules
window._close();window.destroy();model.close()
print('ACTUAL_STAGED_GTK_OFFLINE_DEFERRED_PASS')
'''
        result=subprocess.run(['dbus-run-session','--config-file',str(ROOT/'tests/fixtures/setup-client/bus.conf'),
            '--',sys.executable,'-I','-c',code,str(self.stage),str(self.base/'gtk-user-state')],
            cwd=self.base,capture_output=True,text=True,timeout=15,
            env=dict(os.environ,GTK_USE_PORTAL='0',GIO_USE_VFS='local',GTK_A11Y='none'))
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn('ACTUAL_STAGED_GTK_OFFLINE_DEFERRED_PASS',result.stdout)
        self.assertFalse(list(self.stage.rglob('__pycache__')))


if __name__=='__main__':unittest.main()
