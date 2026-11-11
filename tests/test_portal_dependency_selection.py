"""Backend choice must preserve actual core portal dependencies."""
from pathlib import Path
import importlib.util,tempfile,unittest
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('desktop_graph',Path(__file__).resolve().parents[1]/'scripts/host/phase2_dependency_graph.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class PortalDependencySelectionTests(unittest.TestCase):
 def test_backend_alternative_keeps_required_core_dependencies(self):
  links=['../postlfs/fuse.html','gdk-pixbuf.html','../general/json-glib.html','../multimedia/pipewire.html','../general/dbus.html','../gnome/xdg-desktop-portal-gnome.html','xdg-desktop-portal-wlr.html']
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'x').mkdir()
   (root/'x/xdg-desktop-portal.html').write_text('<html xmlns="http://www.w3.org/1999/xhtml"><body><h1>Portal</h1><h3>Required</h3><p class="required">'+''.join('<a class="xref" href="'+p+'">dependency</a>' for p in links)+'</p></body></html>')
   with patch.object(module,'BOOK',root):edges=module.node('x/xdg-desktop-portal.html')['edges']
  states={r['reference']:r['selected'] for r in edges}
  self.assertTrue(states['postlfs/fuse.html'])
  self.assertTrue(states['x/gdk-pixbuf.html'])
  self.assertTrue(states['general/json-glib.html'])
  self.assertTrue(states['multimedia/pipewire.html'])
  self.assertTrue(states['general/dbus.html'])
  self.assertTrue(states['gnome/xdg-desktop-portal-gnome.html'])
  self.assertFalse(states['x/xdg-desktop-portal-wlr.html'])
