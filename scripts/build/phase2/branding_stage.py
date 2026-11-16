"""Stage exact approved native branding and separate live-only installer scenes.

No image editing, source modification, package installation, host settings change
or guest acceptance. Native transaction/ownership/cache promotion stays explicit.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import struct


class BrandingError(ValueError):
    pass


def sha(data):
    return hashlib.sha256(data).hexdigest()


def source(repository, relative):
    if not isinstance(relative, str) or PurePosixPath(relative).is_absolute() or any(part in ('', '.', '..') for part in relative.split('/')):
        raise BrandingError('branding_source_path')
    path = repository
    for part in relative.split('/'):
        path /= part
        if path.is_symlink():
            raise BrandingError('branding_source_symlink')
    if not path.is_file() or path.stat().st_size > 16 * 1024 * 1024:
        raise BrandingError('branding_source_file')
    return path.read_bytes()


def png(data):
    if data[:8] != b'\x89PNG\r\n\x1a\n' or data[12:16] != b'IHDR' or len(data) < 33:
        raise BrandingError('branding_png')
    return struct.unpack('>II', data[16:24])


def verified_asset(repository, relative, assets):
    data = source(repository, relative)
    row = assets.get(relative)
    if not row or sha(data) != row['sha256'] or png(data) != (row['width'], row['height']):
        raise BrandingError('branding_asset_integrity')
    return data


def _stage_root(destination):
    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
        raise BrandingError('branding_output_exists')
    for parent in destination.parents:
        if parent.is_symlink():
            raise BrandingError('branding_output_symlink')
    destination.mkdir(parents=True, mode=0o755)
    return destination


def _write(root, absolute, data):
    if not absolute.startswith('/usr/share/') or '..' in PurePosixPath(absolute).parts:
        raise BrandingError('branding_destination')
    path = root / absolute.lstrip('/')
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
    if path.exists() or path.is_symlink():
        raise BrandingError('branding_duplicate_destination')
    path.write_bytes(data)
    path.chmod(0o644)


def _assets(repository):
    return {'assets/brand/' + row['file']: row for row in json.loads(source(repository, 'assets/brand/assets.json'))}


def render_desktop_defaults(keyfile):
    """Update the canonical B02 package input, never an installed/user conffile.

    Existing dconf defaults outrank GSettings schema defaults. The owning
    toddy-desktop-defaults recipe can use this renderer and rebuild its existing
    controlled native dconf database. No duplicate file ownership is introduced.
    An edited/unknown baseline is refused rather than reset silently.
    """
    if not isinstance(keyfile, str) or len(keyfile.encode()) > 65536:
        raise BrandingError('branding_defaults_input')
    expected = {'picture-uri': "''", 'picture-uri-dark': "''", 'picture-options': "'none'"}
    replacements = {
        'picture-uri': "'file:///usr/share/backgrounds/toddy-os/toddy-os-wallpaper-light-logo.png'",
        'picture-uri-dark': "'file:///usr/share/backgrounds/toddy-os/toddy-os-wallpaper-dark-logo.png'",
        'picture-options': "'zoom'"}
    active = False
    seen = set()
    output = []
    sections = 0
    for line in keyfile.splitlines(keepends=True):
        stripped = line.strip()
        if stripped.startswith('['):
            active = stripped == '[org/gnome/desktop/background]'
            sections += int(active)
        key, separator, value = stripped.partition('=')
        if active and separator and key in expected:
            if key in seen or value != expected[key]:
                raise BrandingError('branding_defaults_baseline_changed')
            seen.add(key)
            line = key + '=' + replacements[key] + ('\n' if line.endswith('\n') else '')
        output.append(line)
    if sections != 1 or seen != set(expected):
        raise BrandingError('branding_defaults_background_keys')
    return ''.join(output)


def _notices(root, repository, package):
    prefix = '/usr/share/doc/' + package + '/'
    for src, leaf in [('LICENSE', 'copyright'), ('LICENSE', 'copyright-code'), ('LICENSES/CC-BY-4.0.txt', 'CC-BY-4.0.txt'),
                      ('assets/brand/assets.json', 'asset-provenance.json')]:
        _write(root, prefix + leaf, source(repository, src))


def _receipt(root, package, **extra):
    files = {}
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            raise BrandingError('branding_stage_symlink')
        if path.is_dir():
            path.chmod(0o755)
        else:
            files['/' + str(path.relative_to(root))] = sha(path.read_bytes())
    return dict(package=package, architecture='all', files=files,
                ownership='root:root-required-at-native-promotion', native_acceptance='pending', **extra)


def stage_desktop(destination, repository, *, validate_schemas=None):
    repository = Path(repository).resolve()
    specification = json.loads(source(repository, 'assets/brand/gnome/package-map.json'))
    assets = _assets(repository)
    # Check all protected masters even if only the transparent identity is used.
    for relative, asset in assets.items():
        if asset['role'] == 'protected-original':
            verified_asset(repository, relative, assets)
    pending = specification['pending_exports'][0]
    if pending['source'] != 'assets/brand/toddy-os-system-icon.png' or pending['icon_name'] != 'io.github.markaraujo.Toddy':
        raise BrandingError('branding_icon_identity')
    prepared = []
    excluded = {path for values in specification['excluded_runtime_assets'].values() for path in values}
    for row in specification['payload']:
        if row['source'] in excluded:
            raise BrandingError('branding_excluded_runtime_asset')
        data = verified_asset(repository, row['source'], assets) if row['kind'] == 'wallpaper' else source(repository, row['source'])
        prepared.append((row['destination'], data))
    # Prefer approved existing exports when their separate map is present. The
    # current repository has pending sizes only; never fabricate resized assets.
    exports = specification.get('icon_exports', [])
    if exports:
        for row in exports:
            if set(row) != {'source', 'sha256', 'size'} or row['size'] not in pending['sizes']:
                raise BrandingError('branding_icon_export')
            data = source(repository, row['source'])
            if sha(data) != row['sha256'] or png(data) != (row['size'], row['size']):
                raise BrandingError('branding_icon_export_integrity')
            prepared.append(('/usr/share/icons/hicolor/{0}x{0}/apps/io.github.markaraujo.Toddy.png'.format(row['size']), data))
        icon_mode = 'existing-approved-exports'
    else:
        prepared.append(('/usr/share/pixmaps/io.github.markaraujo.Toddy.png', verified_asset(repository, pending['source'], assets)))
        icon_mode = 'protected-master-pixmaps-fallback'
    schema_receipt = None
    if validate_schemas is not None:
        for row in specification['templates']:
            data = source(repository, row['source'])
            schema_receipt = validate_schemas(data)
            if not isinstance(schema_receipt, dict) or schema_receipt.get('verified') is not True or not isinstance(schema_receipt.get('schema_sha256'), str) or not re.fullmatch('[a-f0-9]{64}', schema_receipt['schema_sha256']):
                raise BrandingError('branding_exact_guest_schema_required')
            prepared.append((row['destination'], data))
    root = _stage_root(destination)
    try:
        for path, data in prepared:
            _write(root, path, data)
        _notices(root, repository, specification['package'])
        _write(root, '/usr/share/doc/toddy-branding/README', b'Approved source artwork copied without modification. User settings remain authoritative. No login preference reset, dconf lock, global GTK/GDM patch, or absent-executable launcher. Native icon/readability, defaults/cache promotion and removal checks remain required.\n')
        return _receipt(root, specification['package'], icon_mode=icon_mode,
            small_icon_readability='native-32-48-64-review-pending', schema_validation=schema_receipt,
            native_schema_cache_rebuild_required=schema_receipt is not None)
    except BaseException:
        shutil.rmtree(root)
        raise


def stage_installer(destination, repository, *, qml_enabled=False):
    repository = Path(repository).resolve()
    assets = _assets(repository)
    manifest = json.loads(source(repository, 'assets/brand/installer/scenes.json'))
    if type(qml_enabled) is not bool or manifest.get('schema_version') != 1 or len(manifest['scenes']) != 4:
        raise BrandingError('branding_installer_schema')
    scenes, prepared = [], []
    seen_ids = set()
    for scene in manifest['scenes']:
        if not isinstance(scene.get('id'), str) or not re.fullmatch('[a-z][a-z0-9-]{0,63}', scene['id']) or scene['id'] in seen_ids:
            raise BrandingError('branding_scene_id')
        seen_ids.add(scene['id'])
        if scene['kind'] not in ('native-guest-capture', 'design-preview'):
            raise BrandingError('branding_scene_kind')
        data = source(repository, scene['source'])
        if sha(data) != scene['sha256']:
            raise BrandingError('branding_scene_integrity')
        evidence = source(repository, scene['evidence'])
        if scene['kind'] == 'native-guest-capture':
            if not scene['source'].startswith('docs/evidence/B02-') or scene['sha256'].encode() not in evidence:
                raise BrandingError('branding_native_capture_evidence')
        elif assets.get(scene['source'], {}).get('role') != 'design-preview':
            raise BrandingError('branding_concept_provenance')
        if set(scene['notice']) != {'en', 'pt_BR'} or any(not str(v).strip() for v in scene['notice'].values()):
            raise BrandingError('branding_scene_notice_required')
        if scene['kind'] == 'design-preview' and scene['notice']['en'] != 'Design preview — not a running build.':
            raise BrandingError('branding_concept_label_required')
        image = scene['id'] + '.png'
        prepared.append((image, data))
        scenes.append(dict(scene, image=image, dimensions=list(png(data))))
    prefix = '/usr/share/calamares/branding/toddy/'
    root = _stage_root(destination)
    try:
        for image, data in prepared:
            _write(root, prefix + image, data)
        for relative, name in [('assets/brand/toddy-os-system-icon.png', 'mascot.png'),
                                ('assets/brand/toddy-os-boot-background.png', 'boot-background.png')]:
            _write(root, prefix + name, verified_asset(repository, relative, assets))
        _write(root, prefix + 'scenes.json', (json.dumps(dict(manifest, scenes=scenes), ensure_ascii=False, indent=2) + '\n').encode())
        if qml_enabled:
            qml = source(repository, 'assets/brand/installer/show.qml.in').decode().replace('@SCENES@', json.dumps(scenes, ensure_ascii=True))
            _write(root, prefix + 'show.qml', qml.encode())
            slideshow = 'slideshow: "show.qml"\nslideshowAPI: 2\n'
        else:
            # Actual B02 capture, one static image: no QtQml dependency or timer
            # conveying false progress. Concepts require the visible-label view.
            slideshow = 'slideshow: ["desktop.png"]\n'
        descriptor = '''---
componentName: toddy
welcomeStyleCalamares: false
welcomeExpandingLogo: false
windowExpanding: normal
windowPlacement: center
sidebar: widget
navigation: widget
strings:
    productName: "Toddy OS"
    shortProductName: "Toddy"
    version: "Experimental owner preview"
    shortVersion: "Experimental"
    versionedName: "Toddy OS experimental owner preview"
    shortVersionedName: "Toddy OS experimental"
    bootloaderEntryName: "Toddy OS"
    productUrl: ""
    supportUrl: ""
    knownIssuesUrl: ""
    releaseNotesUrl: ""
    donateUrl: ""
images:
    productIcon: "mascot.png"
    productLogo: "mascot.png"
    productWelcome: "mascot.png"
style:
    SidebarBackground: "#081426"
    SidebarText: "#F1F6FF"
    SidebarTextCurrent: "#F1F6FF"
    SidebarBackgroundCurrent: "#294D75"
uploadServer:
    type: "none"
'''
        _write(root, prefix + 'branding.desc', (descriptor + slideshow).encode())
        _notices(root, repository, 'calamares-branding-toddy')
        for path in sorted((repository / 'assets/third-party/gnome').iterdir()):
            if path.is_file() and path.suffix != '.svg':
                _write(root, '/usr/share/doc/calamares-branding-toddy/gnome-notices/' + path.name, source(repository, str(path.relative_to(repository))))
        return _receipt(root, 'calamares-branding-toddy', live_only=True,
            slideshow='qml-source-runtime-qualification-pending' if qml_enabled else 'static-actual-B02-capture',
            concept_scenes_require_visible_notice=True, independent_real_progress=True)
    except BaseException:
        shutil.rmtree(root)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('component', choices=('desktop', 'installer'))
    parser.add_argument('repository', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    function = stage_desktop if args.component == 'desktop' else stage_installer
    print(json.dumps(function(args.destination, args.repository), sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
