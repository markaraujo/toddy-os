#!/usr/bin/env python3
"""Derive selected desktop dependency edges from the frozen local BLFS book.

Scoped package anchors avoid treating all Python modules/Xorg drivers as one
package. Required-for-GNOME/Wayland recommendations are selected explicitly;
other recommended/optional edges are recorded but never automatically installed.
"""
import hashlib
import html.entities
import json
from pathlib import Path
import posixpath
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
BOOK = ROOT/'.local/books/blfs'
NS = {'x': 'http://www.w3.org/1999/xhtml'}
ROOTS = ['x/gtk4.html', 'x/libadwaita.html', 'x/gdm.html', 'gnome/mutter.html',
         'gnome/gnome-shell.html', 'gnome/gnome-session.html',
         'gnome/gnome-control-center.html', 'gnome/gnome-settings-daemon.html',
         'gnome/gnome-keyring.html', 'gnome/libsecret.html', 'gnome/nautilus.html',
         'gnome/gnome-terminal.html', 'gnome/xdg-desktop-portal-gnome.html',
         'xsoft/firefox.html', 'basicnet/networkmanager.html',
         'multimedia/pipewire.html', 'multimedia/wireplumber.html', 'general/git.html',
         'x/mesa.html', 'x/x7driver.html#libinput', 'general/wayland.html',
         'general/wayland-protocols.html', 'postlfs/linux-pam.html',
         'postlfs/polkit.html', 'general/fontconfig.html',
         'gnome/gsettings-desktop-schemas.html', 'x/gtksourceview5.html',
         'general/enchant.html', 'general/icu.html']


def entity(match):
    if match[1] in {'amp', 'lt', 'gt', 'quot', 'apos'}:
        return match[0]
    return ''.join('&#'+str(ord(c))+';' for c in html.entities.html5[match[1]+';'])


def node(reference):
    filename, _, anchor = reference.partition('#')
    raw = (BOOK/filename).read_bytes()
    document = ET.fromstring(re.sub(r'&([A-Za-z][A-Za-z0-9]*);', entity, raw.decode()))
    parents = {child: parent for parent in document.iter() for child in parent}
    scope = document
    if anchor:
        found = next((e for e in document.iter() if e.get('id') == anchor), None)
        assert found is not None, reference+' missing anchor'
        while found in parents:
            found = parents[found]
            if found.tag.endswith('}div') and found.get('class') == 'sect2':
                scope = found
                break
    heading = scope.find('.//x:h2', NS) if scope is not document else document.find('.//x:h1', NS)
    title = ' '.join(''.join(heading.itertext()).split()) if heading is not None else reference
    edges = []
    for paragraph in scope.iter():
        kind = paragraph.get('class')
        if kind not in {'required', 'recommended', 'optional'}:
            continue
        siblings = list(parents[paragraph])
        index = siblings.index(paragraph)
        label = ' '.join(''.join(siblings[index-1].itertext()).split()) if index else ''
        selected = kind == 'required' or (kind == 'recommended' and 'Required' in label)
        for link in paragraph.findall('.//x:a', NS):
            if link.get('class') != 'xref':
                continue
            href = link.get('href', '')
            if '.html' not in href or '://' in href:
                continue
            target = posixpath.normpath(posixpath.join(posixpath.dirname(filename), href))
            if target == reference:
                continue
            assert not target.startswith('../'), target
            chosen, rationale = selected, label
            if reference == 'x/libnotify.html' and label == 'Required (runtime)':
                chosen = False
                rationale = 'GNOME Shell supplies the notification service; alternate desktop daemons unselected'
            if reference == 'x/xdg-desktop-portal.html' and kind == 'required' and '/xdg-desktop-portal-' in target:
                chosen = target == 'gnome/xdg-desktop-portal-gnome.html'
                rationale = 'Select the GNOME backend from the book alternatives; other backends need a consumer reason'
            edges.append({'reference': target, 'title': link.get('title', ''.join(link.itertext())),
                          'kind': kind, 'selected': chosen, 'reason': rationale})
    if reference == 'x/libnotify.html':
        edges.append({'reference':'gnome/gnome-shell.html','title':'gnome-shell50.4 notification service',
                      'kind':'runtime-capability','selected':True,'reason':'Integrated notification provider in selected GNOME session'})
    return {'title': title, 'book_page_sha256': hashlib.sha256(raw).hexdigest(), 'edges': edges}


if __name__ == '__main__':
    pending, nodes = list(ROOTS), {}
    while pending:
        reference = pending.pop(0)
        if reference in nodes:
            continue
        nodes[reference] = node(reference)
        pending.extend(e['reference'] for e in nodes[reference]['edges'] if e['selected'])
    lock = json.loads((ROOT/'config/phase2/sources.lock.json').read_text())['components']
    for name, version, refs in [
        ('gnome-text-editor','50.1',['x/gtk4.html','x/libadwaita.html','x/gtksourceview5.html','general/glib2.html','upstream/libspelling-0.4.11']),
        ('libspelling','0.4.11',['x/gtk4.html','x/gtksourceview5.html','general/glib2.html','general/enchant.html','general/icu.html'])]:
        source = next(r for r in lock if r['name']==name and r['version']==version)
        key = 'upstream/'+name+'-'+version
        nodes[key] = {'title':name+'-'+version,'source_sha256':source['sha256'],
                      'reference':'Actual pinned source meson.build and lib/enchant/meson.build; optional profiling disabled',
                      'edges':[{'reference':ref,'kind':'source-required','selected':True,'reason':'Native editor/spelling source consumer'} for ref in refs]}
    report = {'scope': 'B01 selected required/capability graph, not native build qualification or an all-optional-package mandate',
              'reference': 'BLFS13.1-systemd', 'roots': ROOTS+['upstream/gnome-text-editor-50.1'], 'nodes': nodes,
              'implementation_rules': [
                  'Reuse accepted native foundation versions; source-pin any missing dependency before extraction.',
                  'Aggregated Xorg library/protocol/font pages are capabilities; resolve only actual consumer-required packages, not the entire page.',
                  'DConf0.49.0 is selected; DConf-Editor49.0 is not a default application.',
                  'GNOME Text Editor50.1 requires GTK/adwaita, GtkSourceView>=5.15 and pinned libspelling0.4.11; libspelling Enchant/ICU backend and source notices stay explicit.',
                  'Calamares uses the separately verified minimal Qt/Svg/LinguistTools/CoreAddons/YAML closure, not the KDE aggregate.',
                  'Other recommendations are unselected unless their owning consumer feature is explicitly required and recorded.',
                  'PipeWire supplies the selected audio server; PulseAudio reference edges represent client API capability, not a second mandatory daemon.',
                  'New source/license/ELF/feature ownership checks are required as each package is qualified.']}
    assert not any(ref.startswith(('lxqt/', 'kde/')) for ref in nodes), 'Alternate desktop leaked into GNOME closure'
    assert all(edge['reference'] in nodes for data in nodes.values() for edge in data['edges'] if edge['selected'])
    destination = ROOT/'config/phase2/desktop-dependencies.json'
    destination.write_text(json.dumps(report, indent=2)+'\n')
    print('Selected graph:', len(nodes), 'scoped nodes')
