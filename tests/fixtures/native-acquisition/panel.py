#!/usr/bin/python3
"""Actual GTK panel construction/offline review; no Polkit/package/native proof."""
import argparse
from pathlib import Path
import sys
import tempfile
import time
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
import gi
gi.require_version('Gtk','4.0');gi.require_version('Adw','1')
from gi.repository import Gtk,Adw,GLib
from runtime.ui.model import SetupModel
from runtime.ui.acquisition import panel
from runtime.ui.onboarding import panel as onboarding_panel

parser=argparse.ArgumentParser();parser.add_argument('--locale',choices=['en','pt-BR'],default='en');args=parser.parse_args()
Gtk.init();Adw.init()
with tempfile.TemporaryDirectory() as temporary:
    model=SetupModel(ROOT,Path(temporary)/'setup',args.locale)
    class Window:pass
    owner=Window();owner.model=model
    page=Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    controller=panel(owner,page)
    onboarding=onboarding_panel(owner,page)
    assert onboarding.status=='idle'
    window=Adw.Window(title='Toddy source acquisition panel test',default_width=440,default_height=600)
    window.set_content(page);window.present()
    # Deterministic unavailable source fixture; never inspect user's keyring or
    # invoke owner authentication. Actual production client is wired by panel.
    controller.client.platform_check=lambda: (_ for _ in ()).throw(__import__('runtime.setup.pending',fromlist=['SetupError']).SetupError('native_os_unsupported'))
    controller.inspect('agent-local')
    deadline=time.monotonic()+3
    while controller.busy and time.monotonic()<deadline:
        GLib.MainContext.default().iteration(True)
    assert controller.status=='unavailable' and controller.close()
    assert window.get_width()>=360
    assert onboarding.close();onboarding.clear_password()
    window.close();model.close()
print('actual GTK panel/offline unavailable source fixture passed; no native acquisition acceptance')
