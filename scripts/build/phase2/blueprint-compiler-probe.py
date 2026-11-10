"""Real CLI UTF8 GTK XML generation/refusal/recovery, no widget creation."""
import json,os,subprocess,sys,xml.etree.ElementTree as ET
command=[sys.argv[1]]
r=subprocess.run(command+['--version'],capture_output=True,text=True,check=True);assert r.stdout.strip()=='0.22.2'
valid='using Gtk 4.0;\nGtk.Box { orientation: vertical; Gtk.Label { label: "Olá Toddy"; } }\n'
bad='using Gtk 4.0;\nGtk.Box { this-property-does-not-exist: true; }\n'
for cycle in range(2):
 r=subprocess.run(command+['compile','-'],input=valid,capture_output=True,text=True);assert r.returncode==0,r.stderr
 tree=ET.fromstring(r.stdout);assert tree.tag=='interface'
 objects=tree.findall('.//object');assert [x.get('class') for x in objects]==['GtkBox','GtkLabel']
 assert tree.find(".//property[@name='label']").text=='Olá Toddy'
 r=subprocess.run(command+['compile','-'],input=bad,capture_output=True,text=True);assert r.returncode==1 and not r.stdout and 'error' in r.stderr.lower()
 r=subprocess.run(command+['compile','-'],input=valid,capture_output=True,text=True);assert r.returncode==0;ET.fromstring(r.stdout)
print(json.dumps({'UTF8_Gtk_XML_cycles':2,'invalid_property_refusals':2,'recovery_cycles':2,'widgets_or_display_tested':False}))
