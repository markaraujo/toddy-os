#!/usr/bin/env python3
"""Read-only Qt6.11 raster Wayland custody inspection; never loads a plugin."""
import argparse
import json
from pathlib import Path
import re

VERSION = '6.11.2'
FILES = ['usr/lib/libQt6Core.so.' + VERSION, 'usr/lib/libQt6Gui.so.' + VERSION,
         'usr/lib/libQt6Widgets.so.' + VERSION, 'usr/lib/libQt6WaylandClient.so.' + VERSION,
         'usr/plugins/platforms/libqwayland.so',
         'usr/plugins/wayland-shell-integration/libxdg-shell.so']
PUBLIC = ('wayland', 'waylandscanner', 'xkbcommon')
PRIVATE = ('wayland_client', 'wayland_client_xdg_shell')


def inspect(root, *, stage=False):
    if root.is_symlink() or not root.is_dir():
        raise ValueError('Qt inspection requires a real root directory')
    root = root.resolve()
    missing = []
    evidence = {}
    def safe_file(relative):
        path = root / relative
        if not path.resolve().is_relative_to(root):
            raise ValueError('Qt file escapes inspected root')
        return path
    for relative in FILES:
        path = safe_file(relative)
        if not path.is_file():
            missing.append(relative); continue
        info = path.stat()
        if info.st_mode & 0o6022:
            raise ValueError('Unsafe Qt artifact mode')
        with path.open('rb') as stream:
            header = stream.read(20)
        # This checks architecture/custody only; not relocations or actual load.
        if len(header) != 20 or header[:6] != b'\x7fELF\x02\x01' or header[18:20] != b'\x3e\x00':
            raise ValueError('Expected x86_64 ELF Qt artifact')
        evidence[relative] = {'bytes': info.st_size}
    bases = [base for base in ('usr/include/QtGui', 'usr/include/qt6/QtGui')
             if safe_file(base + '/qtgui-config.h').is_file()]
    if len(bases) > 1:
        raise ValueError('Ambiguous Qt include roots')
    for filename, features in (('qtgui-config.h', PUBLIC),
                               (VERSION + '/QtGui/private/qtgui-config_p.h', PRIVATE)):
        relative = (bases[0] if bases else 'usr/include/QtGui') + '/' + filename
        path = safe_file(relative)
        data = path.read_text() if path.is_file() and path.stat().st_size <= 262144 else ''
        for feature in features:
            found = re.search(r'^\s*#\s*define\s+QT_FEATURE_' + feature + r'\s+1\s*$', data, re.M) is not None
            evidence['QT_FEATURE_' + feature] = found
            if not found:
                missing.append('QT_FEATURE_' + feature)
    manifest = None
    if stage:
        if __package__:
            from .verify_stage import inspect_stage
        else:
            from verify_stage import inspect_stage
        manifest = inspect_stage(root)['manifest_sha256']
    return {'version': 1, 'qt_version': VERSION, 'scope': 'static raster Wayland files/features; no GUI acceptance',
            'qtbase_rebuild_required': bool(missing), 'missing': missing, 'evidence': evidence,
            'stage_manifest_sha256': manifest, 'native_plugin_load': 'not-run', 'root_gui_launch': 'not-run'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('--stage', action='store_true')
    parser.add_argument('--require', action='store_true')
    args = parser.parse_args()
    result = inspect(args.root, stage=args.stage)
    print(json.dumps(result, indent=2))
    return 2 if args.require and result['qtbase_rebuild_required'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
