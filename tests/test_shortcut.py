"""Real Gio.Settings in a child memory backend; never touches host dconf."""
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]

class ShortcutTests(unittest.TestCase):
 def test_real_gsettings_isolated_conflicts_and_preservation(self):
  code='''
from runtime.ui.shortcut import *
s=Shortcut()
assert not s.current()
other='/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/existing/'
f=s.settings(CUSTOM,other)
f.set_string('name','Existing');f.set_string('command','/usr/bin/true');f.set_string('binding','<Control><Alt>z')
s.media.set_strv('custom-keybindings',[other])
def refused(binding,expected):
 try:s.register(binding)
 except ShortcutError as error:assert str(error)==expected,(binding,error)
 else:raise AssertionError('accepted')
refused('<Alt>F4','conflict')
refused('<Control><Alt>z','conflict')
refused('t','invalid')
assert s.media.get_strv('custom-keybindings')==[other]
assert s.register('<Super><Shift>t')==canonical('<Shift><Super>t')
assert s.current()==canonical('<Super><Shift>t')
assert s.media.get_strv('custom-keybindings')==[other,PATH]
s.register('<Super><Control>t')
s.remove()
assert s.media.get_strv('custom-keybindings')==[other]
assert f.get_string('command')=='/usr/bin/true' and f.get_string('binding')=='<Control><Alt>z'
s.own.set_string('command','/usr/bin/false')
refused('<Super><Shift>t','occupied')
assert s.own.get_string('command')=='/usr/bin/false'
print('isolated-real-GioSettings-passed')
'''
  env={**os.environ,'GSETTINGS_BACKEND':'memory','PYTHONPATH':str(ROOT)}
  p=subprocess.run([sys.executable,'-c',code],cwd=ROOT,env=env,text=True,capture_output=True,timeout=15)
  self.assertEqual(p.returncode,0,p.stdout+p.stderr)
  self.assertIn('isolated-real-GioSettings-passed',p.stdout)

if __name__=='__main__':unittest.main()
