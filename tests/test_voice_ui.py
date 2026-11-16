"""Real GTK voice controls with a non-audio controller fixture; no native B09."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]


class VoiceWidgetTests(unittest.TestCase):
    def test_actual_en_pt_widgets_review_release_and_profile_scope(self):
        if importlib.util.find_spec('gi') is None or shutil.which('dbus-run-session') is None or not (os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')):
            self.skipTest('host GTK/display absent; native voice still unqualified')
        result=subprocess.run(['dbus-run-session','--config-file',str(ROOT/'tests/fixtures/setup-client/bus.conf'),
            '--',sys.executable,str(ROOT/'tests/fixtures/voice-ui/gtk.py')],capture_output=True,text=True,
            cwd=ROOT,timeout=15,env=dict(os.environ,GTK_USE_PORTAL='0',GIO_USE_VFS='local',GTK_A11Y='none'))
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        value=json.loads(result.stdout)
        self.assertTrue(value['press_release_stop_controls']);self.assertTrue(value['review_draft_without_submit'])
        self.assertTrue(value['profile_switch_clears_review'])


if __name__=='__main__':unittest.main()
