"""Verify and prepare an offline own-package closure without copying a builder root.

This source component never installs on the host. Native root installation is an
explicit separate call with a qualified runner/finalizer and whole-image audit.
Accepted H10/H11 inventory/metadata/attribution algorithms remain unchanged.
"""
from contextlib import contextmanager
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import tarfile
import tempfile

HERE = Path(__file__).resolve().parent
RESERVE_BYTES = 16 * 1024**3
NAME = re.compile(r'[a-z0-9][a-z0-9+.-]+\Z')
HASH = re.compile('[0-9a-f]{64}\\Z')
VERSION = re.compile(r'[0-9][0-9A-Za-z.+:~_-]*\Z')
CHECKS = {'native-dpkg-database', 'fresh-system-accounts', 'pam-service-policy',
          'generated-caches', 'ownership-xattrs', 'private-state-and-keys',
          'runtime-linkage', 'whole-image-attribution', 'foundation-recovery'}
MANDATORY_ADDITIONS = {'toddy-assistant', 'toddy-branding'}
ACQUIRED = {'toddy-agent', 'toddy-executor', 'toddy-voice', 'toddy-integrations', 'nodejs', 'llama-cpp'}
RECOVERY_PATHS = ('/boot/vmlinuz-7.1.8-toddy', '/boot/vmlinuz-7.1.8-toddy-pre-fuse', '/etc/toddy/grub.cfg')
MODULE_INPUTS = {'modules.order', 'modules.builtin', 'modules.builtin.modinfo', 'modules.builtin.ranges'}


class PayloadError(ValueError):
    pass


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False) + '\n').encode()


def strict(data):
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise PayloadError('payload_duplicate_json')
            out[key] = value
        return out
    try:
        return json.loads(data.decode('utf-8', errors='strict'), object_pairs_hook=pairs,
            parse_constant=lambda _: (_ for _ in ()).throw(PayloadError('payload_nonfinite_json')))
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise PayloadError('payload_json') from exc


def canonical(value, *, absolute=True):
    if not isinstance(value, str) or '\0' in value or '\n' in value:
        raise PayloadError('payload_path')
    path = PurePosixPath(value)
    if path.is_absolute() != absolute or path.as_posix() != value or '..' in path.parts or value in ('', '/', '.') or value.startswith('//'):
        raise PayloadError('payload_path')
    return value


def regular(path):
    path = Path(path)
    if path.resolve() != path or not path.is_file() or path.is_symlink() or path.stat().st_nlink != 1:
        raise PayloadError('payload_input_not_private_regular')
    return path


def deb822(text):
    fields = {}
    key = None
    for line in text.splitlines():
        if not line:
            continue
        if line[0] in ' \t':
            if key is None:
                raise PayloadError('payload_control_continuation')
            fields[key] += '\n' + line[1:]
            continue
        key, separator, value = line.partition(':')
        if not separator or not re.fullmatch('[A-Za-z][A-Za-z0-9-]*', key) or key in fields:
            raise PayloadError('payload_control_fields')
        fields[key] = value.strip()
    return fields


class ReleaseTrust:
    """Offline detached Release signature + exact SHA256 Packages-index binding.

    Public-key hash/origin come from the reviewed release policy, never an
    automatically imported key or a package's self-declared identity.
    """
    def __init__(self, *, keyring, expected_key_sha256, release, signature, packages,
                 index_path, origin='Toddy OS', gpgv='/usr/bin/gpgv'):
        self.keyring, self.release, self.signature, self.packages = map(regular, (keyring, release, signature, packages))
        self.key_hash = expected_key_sha256
        self.index_path = canonical(index_path, absolute=False)
        self.origin = origin
        self.gpgv = gpgv

    def verify(self, archives):
        if not HASH.fullmatch(self.key_hash) or digest(self.keyring) != self.key_hash:
            raise PayloadError('payload_repository_key_changed')
        public_key_only(self.keyring.read_bytes())
        result = subprocess.run([self.gpgv, '--keyring', str(self.keyring), str(self.signature), str(self.release)],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            env={'PATH': '/usr/bin:/bin', 'LC_ALL': 'C'}, timeout=30, check=False)
        if result.returncode:
            raise PayloadError('payload_repository_signature')
        release = deb822(self.release.read_text())
        if release.get('Origin') != self.origin or 'SHA256' not in release:
            raise PayloadError('payload_repository_origin')
        matches = []
        for line in release['SHA256'].splitlines():
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) != 3 or not HASH.fullmatch(parts[0]) or not parts[1].isdigit():
                raise PayloadError('payload_release_index')
            if parts[2] == self.index_path:
                matches.append(parts)
        if len(matches) != 1 or matches[0][0] != digest(self.packages) or int(matches[0][1]) != self.packages.stat().st_size:
            raise PayloadError('payload_repository_index_binding')
        index = {}
        for paragraph in self.packages.read_text().strip().split('\n\n'):
            row = deb822(paragraph)
            identity = (row.get('Package'), row.get('Version'), row.get('Architecture'))
            if identity in index:
                raise PayloadError('payload_duplicate_repository_package')
            index[identity] = row
        bindings = {}
        for component in archives:
            identity = tuple(component[k] for k in ('name', 'version', 'architecture'))
            row = index.get(identity)
            if not row or row.get('SHA256') != component['archive_sha256'] or not row.get('Size', '').isdigit() or int(row['Size']) != component['archive_bytes']:
                raise PayloadError('payload_signed_package_binding')
            canonical(row.get('Filename'), absolute=False)
            bindings[component['archive']] = component['archive_sha256']
        return {'verified': True, 'origin': self.origin, 'public_key_sha256': self.key_hash,
            'release_sha256': digest(self.release), 'signature_sha256': digest(self.signature),
            'packages_sha256': digest(self.packages), 'index_path': self.index_path, 'archives': bindings}

    def materials(self):
        return {'trusted-keyring.gpg': self.keyring.read_bytes(), 'Release': self.release.read_bytes(),
            'Release.gpg': self.signature.read_bytes(), 'Packages': self.packages.read_bytes()}


def public_key_only(data):
    """Reject secret OpenPGP packets before copying a reviewed binary keyring."""
    if not isinstance(data, bytes) or not 0 < len(data) <= 1024 * 1024:
        raise PayloadError('payload_public_keyring_required')
    offset = 0
    public_key = False
    while offset < len(data):
        header = data[offset]
        offset += 1
        if not header & 0x80:
            raise PayloadError('payload_public_keyring_required')
        if header & 0x40:
            tag = header & 63
            if offset >= len(data):
                raise PayloadError('payload_public_keyring_required')
            first = data[offset]
            offset += 1
            if first < 192:
                length = first
            elif first < 224 and offset < len(data):
                length = ((first - 192) << 8) + data[offset] + 192
                offset += 1
            elif first == 255 and offset + 4 <= len(data):
                length = int.from_bytes(data[offset:offset + 4], 'big')
                offset += 4
            else:
                raise PayloadError('payload_unqualified_public_key_packet')
        else:
            tag = (header >> 2) & 15
            width = (1, 2, 4, 0)[header & 3]
            if width == 0 or offset + width > len(data):
                raise PayloadError('payload_unqualified_public_key_packet')
            length = int.from_bytes(data[offset:offset + width], 'big')
            offset += width
        if tag not in (2, 6, 12, 13, 14, 17):
            raise PayloadError('payload_nonpublic_key_packet')
        public_key |= tag == 6
        offset += length
        if offset > len(data):
            raise PayloadError('payload_truncated_public_key_packet')
    if not public_key:
        raise PayloadError('payload_public_keyring_required')


@contextmanager
def tar_stream(archive, mode, *, dpkg_deb='/usr/bin/dpkg-deb'):
    process = subprocess.Popen([dpkg_deb, mode, str(archive)], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, close_fds=True)
    try:
        with tarfile.open(fileobj=process.stdout, mode='r|') as stream:
            yield stream
        if process.wait(timeout=30):
            raise PayloadError('payload_native_deb_reader')
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        process.stdout.close()


def archive_contents(archive, *, storage=None):
    control_files = {}
    with tar_stream(archive, '--ctrl-tarfile') as stream:
        for member in stream:
            relative = member.name.removeprefix('./').rstrip('/')
            if relative in ('', '.'):
                continue
            if relative not in ('control', 'conffiles', 'md5sums') or not member.isfile() or member.size > 8 * 1024 * 1024:
                raise PayloadError('payload_maintainer_scripts_triggers_or_control_unqualified')
            if relative in control_files:
                raise PayloadError('payload_duplicate_control')
            control_files[relative] = stream.extractfile(member).read()
    if 'control' not in control_files:
        raise PayloadError('payload_missing_control')
    control = deb822(control_files['control'].decode('utf-8', errors='strict'))
    payload, hardlinks, sizes, classes = {}, {}, {}, {}
    with tar_stream(archive, '--fsys-tarfile') as stream:
        for count, member in enumerate(stream):
            if count > 1000000:
                raise PayloadError('payload_archive_entry_limit')
            relative = member.name.removeprefix('./').rstrip('/')
            if relative in ('', '.'):
                continue
            path = canonical('/' + relative)
            if path in payload or path in hardlinks:
                raise PayloadError('payload_duplicate_archive_path')
            row = {'mode': member.mode, 'uid': member.uid, 'gid': member.gid}
            if member.isdir():
                row.update(mode=stat.S_IFDIR | member.mode, directory=True)
            elif member.issym():
                row.update(mode=stat.S_IFLNK | member.mode, symlink=member.linkname)
            elif member.isfile():
                if member.size > 16 * 1024**3:
                    raise PayloadError('payload_archive_file_limit')
                row.update(mode=stat.S_IFREG | member.mode,
                    sha256=hashlib.file_digest(stream.extractfile(member), 'sha256').hexdigest())
                sizes[path] = member.size
                classes[path] = path
            elif member.islnk():
                row['mode'] |= stat.S_IFREG
                hardlinks[path] = (canonical('/' + member.linkname.removeprefix('./')), row)
                continue
            else:
                raise PayloadError('payload_archive_special_node')
            payload[path] = row
    for _ in range(len(hardlinks) + 1):
        changed = False
        for path, (target, row) in list(hardlinks.items()):
            if target in payload and 'sha256' in payload[target]:
                payload[path] = dict(row, sha256=payload[target]['sha256'])
                sizes[path] = sizes[target]
                classes[path] = classes[target]
                del hardlinks[path]
                changed = True
        if not hardlinks or not changed:
            break
    if hardlinks:
        raise PayloadError('payload_hardlink_target')
    if storage is not None:
        storage.update(members={path:({'kind':'regular','bytes':sizes[path],'hardlink_class':classes[path]} if path in sizes else
            {'kind':'directory'} if row.get('directory') else {'kind':'symlink','bytes':len(os.fsencode(row['symlink']))})
            for path,row in payload.items()},control_bytes=sum(map(len,control_files.values())),
            control_files=len(control_files),list_bytes=3+sum(len(os.fsencode(path))+1 for path in payload),
            conffile_lines=len(control_files.get('conffiles',b'').splitlines()))
    return control, payload, sum(sizes.values())


def dependencies(text):
    if not isinstance(text, str) or '\n' in text or len(text) > 65536:
        raise PayloadError('payload_dependency_syntax')
    result = []
    for group in text.split(','):
        if not group.strip():
            continue
        terms = []
        for term in group.split('|'):
            match = re.fullmatch(r'\s*([a-z0-9][a-z0-9+.-]*)(?::(?:any|native|amd64))?(?:\s*\((<<|<=|=|>=|>>)\s*([0-9][0-9A-Za-z.+:~_-]*)\))?\s*', term)
            if not match:
                raise PayloadError('payload_dependency_syntax')
            terms.append(match.groups())
        result.append(terms)
    return result


def version_satisfies(actual, operator, expected):
    if operator is None:
        return True
    result = subprocess.run(['/usr/bin/dpkg', '--compare-versions', actual, operator, expected],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5, check=False)
    if result.returncode not in (0, 1):
        raise PayloadError('payload_dependency_version_comparator')
    return result.returncode == 0


def dependency_closure(components, roots):
    selected, queue = set(), list(sorted(roots))
    while queue:
        name = queue.pop()
        if name in selected:
            continue
        if name not in components:
            raise PayloadError('payload_missing_required_root')
        selected.add(name)
        row = components[name]
        for terms in dependencies(row.get('depends', '')) + dependencies(row.get('pre_depends', '')):
            chosen = next((candidate for candidate, op, value in terms
                if candidate in components and version_satisfies(components[candidate]['version'], op, value)), None)
            if chosen is None:
                raise PayloadError('payload_unsatisfied_versioned_dependency')
            queue.append(chosen)
    return selected


def inventory(records):
    specification = importlib.util.spec_from_file_location('offline_h10_root_inventory', HERE.parent / 'h10/root_inventory.py')
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module.package_inventory(records)


def generated_artifact(path):
    return (path.endswith(('gschemas.compiled', 'icon-theme.cache', 'mime.cache', 'loaders.cache',
             'immodules.cache', 'giomodule.cache', 'hwdb.bin')) or
            path.startswith('/etc/dconf/db/') and '.d/' not in path and not path.endswith('.d') or
            path.startswith('/usr/lib/modules/') and '/modules.' in path and PurePosixPath(path).name not in MODULE_INPUTS)


def cache_namespace(path, entries):
    """Known producer input namespaces, including directory/link identities."""
    parent = str(PurePosixPath(path).parent) + '/'
    if path.endswith('/gschemas.compiled'):
        selected = {key: row for key, row in entries.items() if key.startswith(parent) and key.endswith(('.xml', '.override'))}
    elif path.endswith('/icon-theme.cache'):
        selected = {key: row for key, row in entries.items() if key.startswith(parent) and key != path}
    elif path.endswith('/mime.cache'):
        selected = {key: row for key, row in entries.items() if key.startswith(parent + 'packages/')}
    elif path.endswith('/hwdb.bin'):
        selected = {key: row for key, row in entries.items() if key.startswith(('/usr/lib/udev/hwdb.d/', '/etc/udev/hwdb.d/'))}
    elif path.startswith('/etc/dconf/db/'):
        selected = {key: row for key, row in entries.items() if key.startswith(path + '.d/')}
    elif path.startswith('/usr/lib/modules/'):
        release = PurePosixPath(path).parent.name
        selected = {key: row for key, row in entries.items() if key.startswith(parent)
            and (not PurePosixPath(key).name.startswith('modules.') or PurePosixPath(key).name in MODULE_INPUTS)}
        source_map = '/boot/System.map-' + release
        if source_map in entries:
            selected[source_map] = entries[source_map]
    elif path.endswith(('loaders.cache', 'immodules.cache', 'giomodule.cache')):
        selected = {key: row for key, row in entries.items() if key.startswith(parent) and key != path}
    else:
        raise PayloadError('payload_generated_cache_family_unqualified')
    if not selected:
        raise PayloadError('payload_generated_cache_inputs_empty')
    return selected


def validate_generated(records, entries, bindings):
    if not isinstance(bindings, dict):
        raise PayloadError('payload_generated_bindings_required')
    required = {path for path, row in entries.items() if 'sha256' in row and generated_artifact(path)}
    if set(bindings) != required:
        raise PayloadError('payload_generated_cache_binding_incomplete')
    for path, binding in bindings.items():
        if not isinstance(binding, dict) or set(binding) != {'output_sha256', 'tool', 'inputs', 'input_namespace_sha256', 'native_evidence_sha256'} or binding['output_sha256'] != entries[path]['sha256'] or not isinstance(binding['native_evidence_sha256'], str) or not HASH.fullmatch(binding['native_evidence_sha256']):
            raise PayloadError('payload_generated_cache_binding')
        tool = binding['tool']
        if not isinstance(tool, dict) or set(tool) != {'path', 'sha256'} or not isinstance(tool['sha256'], str) or not HASH.fullmatch(tool['sha256']) or entries.get(tool['path'], {}).get('sha256') != tool['sha256']:
            raise PayloadError('payload_generated_tool_binding')
        if not isinstance(binding['inputs'], dict) or not binding['inputs']:
            raise PayloadError('payload_generated_inputs')
        for source, expected in binding['inputs'].items():
            if not isinstance(expected, str) or not HASH.fullmatch(expected) or entries.get(source, {}).get('sha256') != expected:
                raise PayloadError('payload_generated_input_not_selected')
        namespace = cache_namespace(path, entries)
        expected = {key: row['sha256'] for key, row in namespace.items() if 'sha256' in row}
        if binding['inputs'] != expected or binding['input_namespace_sha256'] != hashlib.sha256(encoded(namespace)).hexdigest():
            raise PayloadError('payload_schema_union_inputs_differ' if path.endswith('/gschemas.compiled') else 'payload_generated_namespace_differs')
    return {'owned_cache_bindings': bindings,
            'native_regeneration_required': sorted({path for record in records for path in record.get('generated_paths', [])})}


def rounded(size,block):
    if type(size) is not int or size<0 or type(block) is not int or block<=0:raise PayloadError('payload_storage_measurement')
    return ((size+block-1)//block)*block


def available_bytes(path):
    info=os.statvfs(path);return info.f_bavail*info.f_frsize


def require_capacity(parent,additional):
    if type(additional) is not int or additional<0 or available_bytes(parent)<RESERVE_BYTES+additional:
        raise PayloadError('payload_storage_reserve_requires_16gib_plus_measured_copy')


def file_tree_storage_bound(files,block):
    """Copied regular files, merged actual names and rounded data/index space."""
    directories={'.'}
    for name,size in files.items():
        canonical(name,absolute=False);rounded(size,block)
        directories.update(parent.as_posix() for parent in PurePosixPath(name).parents)
    if directories & files.keys():raise PayloadError('payload_storage_parent_conflict')
    entries={name:24 for name in directories}
    for name in (set(files)|directories)-{'.'}:
        entries[PurePosixPath(name).parent.as_posix()]+=rounded(8+len(os.fsencode(PurePosixPath(name).name)),4)
    return (sum(rounded(size,block)+block for size in files.values())+
        sum(rounded(size,block)+block for size in entries.values()))


def storage_measurements(measurements,owned,block):
    """Merge actual member names/classes; identical SHA never implies a hardlink."""
    members={};classes={};control=listing=conffiles=control_count=0
    for package,row in sorted(measurements.items()):
        control+=row['control_bytes'];listing+=row['list_bytes'];conffiles+=row['conffile_lines'];control_count+=row['control_files']
        for path,member in row['members'].items():
            if path in members and member['kind']!='directory':raise PayloadError('payload_storage_duplicate_path')
            members[path]=member
            if member['kind']=='regular':
                key=(package,member['hardlink_class'])
                if key in classes and classes[key]!=member['bytes']:raise PayloadError('payload_storage_hardlink_size')
                classes[key]=member['bytes']
    # Fresh directories are explicit source inputs, not inherited runtime state.
    for relative in owned['fresh_directories']:members.setdefault('/'+relative,{'kind':'directory'})
    directories={path:24 for path,member in members.items() if member['kind']=='directory'}
    directories.setdefault('/',24)
    for path in members:
        parent=str(PurePosixPath(path).parent)
        if parent not in directories:raise PayloadError('payload_storage_unowned_parent')
        directories[parent]+=rounded(8+len(os.fsencode(PurePosixPath(path).name)),4)
    data=sum(rounded(size,block) for size in classes.values())
    links=sum(max(block,rounded(row['bytes'],block)) for row in members.values() if row['kind']=='symlink')
    # Directory data plus one index/inode block per measured namespace node.
    namespace=sum(rounded(size,block)+block for size in directories.values())+block*(len(classes)+sum(row['kind']=='symlink' for row in members.values()))
    # Native status/status-old and temporary update copies; selected control and
    # per-package path-list bytes are measured, including conffile hash fields.
    database=rounded(3*(control+listing+64*conffiles),block)+block*(2*(control_count+len(measurements))+20)
    cache=max((member.get('bytes',0) for row in measurements.values() for path,member in row['members'].items()
               if generated_artifact(path)),default=0)
    return {'version':1,'block_bytes':block,'logical_regular_path_bytes':sum(row.get('bytes',0) for row in members.values() if row['kind']=='regular'),
        'unique_regular_bytes':sum(classes.values()),'regular_inodes':len(classes),
        'hardlink_aliases':sum(row['kind']=='regular' for row in members.values())-len(classes),
        'namespace_entries':len(members),'rounded_file_data_bytes':data,'symlink_storage_bound_bytes':links,
        'namespace_storage_bound_bytes':namespace,'native_database_staging_bound_bytes':database,
        'owned_cache_temporary_bound_bytes':rounded(cache,block),
        'root_storage_bound_bytes':data+links+namespace+database+rounded(cache,block)}


def prepare(*, profile_path, projection_path, records_directory, archive_directory,
            catalog_path, destination, trust, generated_bindings, additional_components=(),
            required_additions=MANDATORY_ADDITIONS, required_recovery_paths=RECOVERY_PATHS):
    """Create only a fresh verified input bundle. Does not assert a ready root."""
    profile_path, projection_path = map(regular, (profile_path, projection_path))
    profile, projection = strict(profile_path.read_bytes()), strict(projection_path.read_bytes())
    if projection.get('schema_version') != 1 or type(projection.get('schema_version')) is not int or projection.get('profile_sha256') != digest(profile_path):
        raise PayloadError('payload_projection_profile_binding')
    rows = [*projection['components'], *additional_components]
    components, records, filenames, measurements = {}, [], set(), {}
    for component in rows:
        name, version, architecture = (component.get(key) for key in ('name', 'version', 'architecture'))
        if not isinstance(name, str) or not NAME.fullmatch(name) or name in components or not isinstance(version, str) or not VERSION.fullmatch(version) or architecture not in ('all', 'amd64'):
            raise PayloadError('payload_component_identity')
        stem = name + '_' + version + '_' + architecture
        record_path = regular(Path(records_directory) / (stem + '.json'))
        archive_path = regular(Path(archive_directory) / (stem + '.deb'))
        if digest(record_path) != component['component_record_sha256'] or digest(archive_path) != component['archive_sha256']:
            raise PayloadError('payload_component_custody')
        record = strict(record_path.read_bytes())
        if record.get('installed') is not True or record.get('name') != name or record.get('version') != version or record.get('archive_sha256') != component['archive_sha256'] or record.get('recipe_sha256') != component['recipe_sha256'] or not HASH.fullmatch(record['recipe_sha256']):
            raise PayloadError('payload_qualified_record')
        normalized_sources = [{('public_verification_material_sha256' if k == 'key_sha256' else k): v for k, v in source.items()} for source in record.get('sources', [])]
        if normalized_sources != component.get('sources'):
            raise PayloadError('payload_source_provenance')
        for source in normalized_sources:
            if not isinstance(source, dict) or not HASH.fullmatch(source.get('sha256', '')):
                raise PayloadError('payload_source_integrity')
        measured={}
        control, actual, installed_bytes = archive_contents(archive_path,storage=measured)
        measurements[name]=measured
        if control.get('Pre-Depends'):
            raise PayloadError('payload_predepends_install_order_unqualified')
        if (control.get('Package'), control.get('Version'), control.get('Architecture')) != (name, version, architecture) or control.get('Depends', '') != component.get('depends', '') or actual != record.get('payload'):
            raise PayloadError('payload_archive_control_or_owned_bytes_differ')
        for field in ('copyright', 'source_notices_index'):
            notice = component.get(field)
            if field == 'copyright' and not notice:
                raise PayloadError('payload_legal_provenance_missing')
            if notice and actual.get(notice['path'], {}).get('sha256') != notice['sha256']:
                raise PayloadError('payload_legal_provenance_missing')
        if digest(archive_path) != component['archive_sha256'] or digest(record_path) != component['component_record_sha256']:
            raise PayloadError('payload_inputs_changed_during_review')
        row = dict(component, archive=stem + '.deb', record=stem + '.json',
            archive_bytes=archive_path.stat().st_size, installed_bytes=installed_bytes,
            pre_depends=control.get('Pre-Depends', ''))
        components[name] = row
        records.append(record)
        filenames.add(row['archive'])
    roots = set(profile['retained_foundation_packages']) | set(profile['desktop_roots']) | set(required_additions)
    selected = dependency_closure(components, roots)
    if selected != set(components) or selected & ACQUIRED:
        raise PayloadError('payload_offline_package_set_not_exact')
    projection_names = {row['name'] for row in projection['components']}
    if projection_names & set(profile['excluded_product_roots']) or set(components) - projection_names != set(required_additions):
        raise PayloadError('payload_unreviewed_additional_roots')
    owned = inventory(records)
    for path in required_recovery_paths:
        if 'sha256' not in owned['entries'].get(path, {}):
            raise PayloadError('payload_foundation_recovery_missing')
    generated = validate_generated(records, owned['entries'], generated_bindings)
    repository = trust.verify(list(components.values()))
    expected_archives = {row['archive']: row['archive_sha256'] for row in components.values()}
    if repository.get('verified') is not True or repository.get('archives') != expected_archives:
        raise PayloadError('payload_signed_repository_not_verified')
    destination=Path(destination)
    block=os.statvfs(destination.parent).f_frsize
    storage=storage_measurements(measurements,owned,block)
    manifest = {'schema_version': 1, 'scope': 'verified-offline-input-bundle-not-installed-root',
        'profile_sha256': digest(profile_path), 'projection_sha256': digest(projection_path),
        'catalog_sha256': digest(regular(catalog_path)),
        'components': [components[name] for name in sorted(components)], 'repository': repository,
        'ownership': owned, 'generated': generated, 'required_finalizer_checks': sorted(CHECKS),
        'required_recovery_paths': list(required_recovery_paths), 'installed_ready': False,
        'bytes': sum(archive['installed_bytes'] for archive in components.values()),'storage':storage}
    destination = Path(destination)
    if destination.resolve() != destination or destination.exists() or destination.is_symlink():
        raise PayloadError('payload_fresh_output_required')
    planned={'archives/'+row['archive']:row['archive_bytes'] for row in manifest['components']}
    planned.update({'records/'+row['record']:regular(Path(records_directory)/row['record']).stat().st_size for row in manifest['components']})
    planned.update({'repository/'+name:len(data) for name,data in trust.materials().items()})
    planned.update({'profile.json':profile_path.stat().st_size,'projection.json':projection_path.stat().st_size,
        'catalog.json':regular(catalog_path).stat().st_size,'preparation-state.json':256,
        'manifest.json':len(encoded(manifest))+block})
    # One extra manifest block bounds its own additive capacity-summary field.
    storage['bundle_copy_bound_bytes']=file_tree_storage_bound(planned,block)
    require_capacity(destination.parent,storage['bundle_copy_bound_bytes'])
    destination.mkdir(mode=0o700)
    # Preserve incomplete output for diagnosis. Never reuse it as a success marker.
    (destination / 'preparation-state.json').write_bytes(encoded({'state': 'copying-inputs'}))
    for kind in ('archives', 'records', 'repository'):
        (destination / kind).mkdir(mode=0o700)
    for component in manifest['components']:
        for kind, directory, key, expected in [('archives', archive_directory, 'archive', component['archive_sha256']),
                ('records', records_directory, 'record', component['component_record_sha256'])]:
            target = destination / kind / component[key]
            with regular(Path(directory) / component[key]).open('rb') as source, target.open('xb') as output:
                shutil.copyfileobj(source, output, 1024 * 1024)
                output.flush()
                os.fsync(output.fileno())
            target.chmod(0o400)
            if digest(target) != expected:
                raise PayloadError('payload_transfer_integrity')
    materials = trust.materials()
    expected_materials = {'trusted-keyring.gpg': repository['public_key_sha256'],
        'Release': repository['release_sha256'], 'Release.gpg': repository['signature_sha256'],
        'Packages': repository['packages_sha256']}
    if set(materials) != set(expected_materials):
        raise PayloadError('payload_repository_materials')
    for leaf, data in materials.items():
        if hashlib.sha256(data).hexdigest() != expected_materials[leaf]:
            raise PayloadError('payload_repository_materials_changed')
        (destination / 'repository' / leaf).write_bytes(data)
        (destination / 'repository' / leaf).chmod(0o400)
    shutil.copyfile(regular(catalog_path), destination / 'catalog.json')
    (destination / 'catalog.json').chmod(0o400)
    if digest(destination / 'catalog.json') != manifest['catalog_sha256']:
        raise PayloadError('payload_catalog_changed')
    for leaf, original, expected in [('profile.json', profile_path, manifest['profile_sha256']),
                                   ('projection.json', projection_path, manifest['projection_sha256'])]:
        shutil.copyfile(original, destination / leaf)
        (destination / leaf).chmod(0o400)
        if digest(destination / leaf) != expected:
            raise PayloadError('payload_input_policy_changed')
    (destination / 'manifest.json').write_bytes(encoded(manifest))
    (destination / 'manifest.json').chmod(0o400)
    (destination / 'preparation-state.json').write_bytes(encoded({'state': 'prepared-inputs', 'manifest_sha256': digest(destination / 'manifest.json')}))
    return manifest


class PreparedPayload:
    """Installer callbacks for a pinned bundle and qualified native finalizer.

    Finalizer reports are required but do not replace independent installed
    ownership/namespace readback. No current-root copy method is provided.
    """
    def __init__(self, directory, *, manifest_sha256, runner, finalizer,
                 mount_base='/run/toddy-installer', target_guard=None,
                 expected_additions=MANDATORY_ADDITIONS):
        self.directory = Path(directory)
        self.manifest_sha256 = manifest_sha256
        self.runner = runner
        self.finalizer = finalizer
        self.mount_base = Path(mount_base)
        self.target_guard = target_guard or self._target_guard
        self.expected_additions = set(expected_additions)

    def _load(self):
        path = regular(self.directory / 'manifest.json')
        if digest(path) != self.manifest_sha256:
            raise PayloadError('payload_manifest_changed')
        manifest = strict(path.read_bytes())
        state = strict(regular(self.directory / 'preparation-state.json').read_bytes())
        if manifest.get('schema_version') != 1 or manifest.get('installed_ready') is not False or state != {'state': 'prepared-inputs', 'manifest_sha256': self.manifest_sha256}:
            raise PayloadError('payload_preparation_incomplete')
        if set(manifest['required_finalizer_checks']) != CHECKS:
            raise PayloadError('payload_finalizer_contract')
        if not self.expected_additions <= {row['name'] for row in manifest['components']} or {row['name'] for row in manifest['components']} & ACQUIRED:
            raise PayloadError('payload_offline_component_contract')
        if digest(regular(self.directory / 'catalog.json')) != manifest['catalog_sha256']:
            raise PayloadError('payload_catalog_changed')
        for leaf, key in [('profile.json', 'profile_sha256'), ('projection.json', 'projection_sha256')]:
            if digest(regular(self.directory / leaf)) != manifest[key]:
                raise PayloadError('payload_bundle_policy_changed')
        for component in manifest['components']:
            for kind, key, hash_key in [('archives', 'archive', 'archive_sha256'), ('records', 'record', 'component_record_sha256')]:
                canonical(component[key], absolute=False)
                if '/' in component[key] or digest(regular(self.directory / kind / component[key])) != component[hash_key]:
                    raise PayloadError('payload_bundle_custody_changed')
        repository = manifest['repository']
        base = self.directory / 'repository'
        trust = ReleaseTrust(keyring=base / 'trusted-keyring.gpg', expected_key_sha256=repository['public_key_sha256'],
            release=base / 'Release', signature=base / 'Release.gpg', packages=base / 'Packages',
            index_path=repository['index_path'], origin=repository['origin'])
        if trust.verify(manifest['components']) != repository:
            raise PayloadError('payload_bundle_signed_trust_changed')
        return manifest

    def verify_payload(self, plan):
        manifest = self._load()
        if not callable(self.finalizer) or plan['payload'] != {'sha256': self.manifest_sha256,
                'catalog_sha256': manifest['catalog_sha256'], 'bytes': manifest['bytes']}:
            raise PayloadError('payload_installer_plan_binding')
        return {'verified': True, 'payload_sha256': self.manifest_sha256, 'catalog_sha256': manifest['catalog_sha256']}

    def _target_guard(self, root, plan):
        root = Path(root)
        expected = self.mount_base / ('target-' + plan['options']['operation_id'])
        if root != expected or root.resolve() != root or root == Path('/') or not os.path.ismount(root):
            raise PayloadError('payload_designated_mounted_target_required')
        info = root.stat()
        if info.st_uid != 0 or info.st_gid != 0 or stat.S_IMODE(info.st_mode) != 0o755:
            raise PayloadError('payload_target_root_metadata')
        device = '{}:{}'.format(os.major(info.st_dev), os.minor(info.st_dev))
        sysfs = (Path('/sys/dev/block') / device).resolve(strict=True)
        if (sysfs / 'partition').read_text().strip() != '2' or (sysfs.parent / 'dev').read_text().strip() != plan['target']['major_minor']:
            raise PayloadError('payload_target_partition_identity')
        return True

    def install_payload(self, root, plan):
        receipt = self.verify_payload(plan)
        manifest = self._load()
        root = Path(root)
        self.runner.require_root()
        if self.target_guard(root, plan) is not True:
            raise PayloadError('payload_target_guard')
        if any(path.name != 'lost+found' or not path.is_dir() or path.is_symlink() or list(path.iterdir()) for path in root.iterdir()):
            raise PayloadError('payload_target_not_fresh')
        # Never replay an uncertain partial unpack into an existing target.
        archives = [str(self.directory / 'archives' / row['archive']) for row in manifest['components']]
        # dpkg's default log is independent of --root. Keep native diagnostics
        # in private operation custody outside both the live OS log and image.
        if self.mount_base.resolve()!=self.mount_base or self.mount_base.is_relative_to(root):
            raise PayloadError('payload_log_custody')
        self.mount_base.mkdir(mode=0o700,parents=True,exist_ok=True)
        info=self.mount_base.stat()
        if info.st_uid!=os.geteuid() or stat.S_IMODE(info.st_mode)!=0o700:
            raise PayloadError('payload_log_custody')
        log_directory=Path(tempfile.mkdtemp(prefix='payload-',dir=self.mount_base))
        log='--log='+str(log_directory/'dpkg.log')
        self.runner.run(['/usr/bin/dpkg', '--root=' + str(root), log, '--unpack', *archives], timeout=1800)
        self.runner.run(['/usr/bin/dpkg', '--root=' + str(root), log, '--configure', '--pending'], timeout=900)
        observed = self.runner.run(['/usr/bin/dpkg-query', '--admindir=' + str(root / 'var/lib/dpkg'), '-W',
            '-f=${Package}\t${Version}\t${Architecture}\t${Status}\n'])
        actual = {}
        for line in observed.splitlines():
            parts = line.split('\t')
            if len(parts) != 4 or parts[3] != 'install ok installed' or parts[0] in actual:
                raise PayloadError('payload_native_database_unconfigured')
            actual[parts[0]] = parts[1:3]
        expected = {row['name']: [row['version'], row['architecture']] for row in manifest['components']}
        if actual != expected:
            raise PayloadError('payload_native_database_component_mismatch')
        final = self.finalizer(root, manifest)
        if not isinstance(final, dict) or set(final) != {'checks', 'generated_entries', 'image_manifest_sha256'} or set(final['checks']) != CHECKS:
            raise PayloadError('payload_native_finalizer_incomplete')
        for check, result in final['checks'].items():
            if not isinstance(result, dict) or set(result) != {'passed', 'exit_status', 'report', 'report_sha256'} or result['passed'] is not True or type(result['exit_status']) is not int or result['exit_status'] != 0 or not isinstance(result['report_sha256'], str) or not HASH.fullmatch(result['report_sha256']):
                raise PayloadError('payload_native_finalizer_failed')
            report = regular(result['report'])
            if report.is_relative_to(root) or digest(report) != result['report_sha256']:
                raise PayloadError('payload_native_finalizer_report_custody')
            observed = strict(report.read_bytes())
            if not isinstance(observed, dict) or observed.get('check') != check or observed.get('input_manifest_sha256') != self.manifest_sha256 or observed.get('passed') is not True or type(observed.get('exit_status')) is not int or observed['exit_status'] != 0 or not isinstance(observed.get('postconditions'), dict) or not observed['postconditions']:
                raise PayloadError('payload_native_finalizer_report_postconditions')
        snapshot = self.audit_tree(root, manifest, final['generated_entries'])
        if hashlib.sha256(encoded(snapshot)).hexdigest() != final['image_manifest_sha256']:
            raise PayloadError('payload_independent_image_manifest_differs')
        # Verify input trust after the finalizer too. No callback may mutate the
        # native archive/record bundle while constructing the target.
        self.verify_payload(plan)
        if self.target_guard(root, plan) is not True:
            raise PayloadError('payload_target_guard')
        return receipt

    @staticmethod
    def audit_tree(root, manifest, generated):
        if not isinstance(generated, dict):
            raise PayloadError('payload_generated_attribution_required')
        expected = dict(manifest['ownership']['entries'])
        for path, row in generated.items():
            canonical(path)
            if path in expected or not isinstance(row, dict) or row.get('origin') not in CHECKS | {'fresh-filesystem'}:
                raise PayloadError('payload_generated_attribution_conflict')
            if row.get('origin') == 'fresh-filesystem' and path != '/lost+found':
                raise PayloadError('payload_fresh_filesystem_attribution')
            expected[path] = {key: value for key, value in row.items() if key != 'origin'}
        actual = {}
        root = Path(root)
        device = root.stat().st_dev
        for base, directories, files in os.walk(root, followlinks=False):
            for leaf in sorted(directories + files):
                path = Path(base) / leaf
                virtual = '/' + path.relative_to(root).as_posix()
                metadata = path.lstat()
                if metadata.st_dev != device or os.listxattr(path, follow_symlinks=False):
                    raise PayloadError('payload_unreviewed_device_or_xattrs')
                row = {'mode': metadata.st_mode, 'uid': metadata.st_uid, 'gid': metadata.st_gid}
                if stat.S_ISREG(metadata.st_mode):
                    row['sha256'] = digest(path)
                elif stat.S_ISLNK(metadata.st_mode):
                    row['symlink'] = os.readlink(path)
                elif stat.S_ISDIR(metadata.st_mode):
                    row['directory'] = True
                else:
                    raise PayloadError('payload_unattributed_special_node')
                actual[virtual] = row
        if actual != expected:
            raise PayloadError('payload_independent_whole_image_attribution')
        for path in manifest['required_recovery_paths']:
            if actual.get(path) != manifest['ownership']['entries'].get(path):
                raise PayloadError('payload_foundation_recovery_changed')
        return actual


def component_from_record(record_path, archive_directory, *, storage=None):
    """Collect one explicitly qualified additional package, without installing."""
    record_path = regular(record_path)
    record = strict(record_path.read_bytes())
    stem = record_path.name.removesuffix('.json')
    architecture = stem.rsplit('_', 1)[-1]
    if record.get('installed') is not True or architecture not in ('amd64', 'all') or stem != record['name'] + '_' + record['version'] + '_' + architecture:
        raise PayloadError('payload_additional_record_identity')
    archive = regular(Path(archive_directory) / (stem + '.deb'))
    if digest(archive) != record['archive_sha256']:
        raise PayloadError('payload_additional_archive_custody')
    control, actual, _ = archive_contents(archive,storage=storage)
    if (control.get('Package'), control.get('Version'), control.get('Architecture')) != (record['name'], record['version'], architecture) or actual != record['payload']:
        raise PayloadError('payload_additional_control_or_bytes')
    legal = '/usr/share/doc/' + record['name'] + '/copyright'
    index = '/usr/share/doc/' + record['name'] + '/source-notices/index.json'
    if 'sha256' not in actual.get(legal, {}):
        raise PayloadError('payload_legal_provenance_missing')
    return {'name': record['name'], 'version': record['version'], 'architecture': architecture,
        'depends': control.get('Depends', ''), 'archive_sha256': record['archive_sha256'],
        'component_record_sha256': digest(record_path), 'recipe_sha256': record['recipe_sha256'],
        'sources': [{('public_verification_material_sha256' if key == 'key_sha256' else key): value
                    for key, value in source.items()} for source in record['sources']],
        'copyright': {'path': legal, 'sha256': actual[legal]['sha256']},
        'source_notices_index': {'path': index, 'sha256': actual[index]['sha256']} if index in actual else None}


def requirements(projection_path, records_directory):
    """Read-only exact input checklist; no readiness or acceptance is inferred."""
    projection_path = regular(projection_path)
    projection = strict(projection_path.read_bytes())
    records = []
    components = []
    for component in projection['components']:
        stem = component['name'] + '_' + component['version'] + '_' + component['architecture']
        path = regular(Path(records_directory) / (stem + '.json'))
        if digest(path) != component['component_record_sha256']:
            raise PayloadError('payload_component_custody')
        record = strict(path.read_bytes())
        records.append(record)
        components.append({'record': stem + '.json', 'record_sha256': component['component_record_sha256'],
            'archive': stem + '.deb', 'archive_sha256': component['archive_sha256']})
    owned = inventory(records)
    return {'schema_version': 1, 'scope': 'input-checklist-not-composed-root',
        'projection_sha256': digest(projection_path), 'packages': components,
        'additional_required_packages': sorted(MANDATORY_ADDITIONS),
        'generated_bindings_required': {path: {'output_sha256': row['sha256'], 'tool': None,
            'inputs': {key: value['sha256'] for key, value in cache_namespace(path, owned['entries']).items() if 'sha256' in value},
            'input_namespace_sha256': hashlib.sha256(encoded(cache_namespace(path, owned['entries']))).hexdigest(),
            'native_evidence_sha256': None} for path, row in sorted(owned['entries'].items())
            if 'sha256' in row and generated_artifact(path)},
        'native_finalizer_checks': sorted(CHECKS), 'required_recovery_paths': list(RECOVERY_PATHS),
        'ready_for_install': False}


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest='command', required=True)
    collect = subcommands.add_parser('requirements', help='Read records and list exact missing composition inputs')
    collect.add_argument('--projection', required=True, type=Path)
    collect.add_argument('--records', required=True, type=Path)
    create = subcommands.add_parser('prepare', help='Prepare a new verified offline input bundle; never install')
    for option in ('profile', 'projection', 'records', 'cache', 'catalog', 'keyring', 'release',
                   'signature', 'packages', 'generated-bindings', 'output'):
        create.add_argument('--' + option, required=True, type=Path)
    create.add_argument('--key-sha256', required=True)
    create.add_argument('--index-path', required=True)
    create.add_argument('--origin', default='Toddy OS')
    create.add_argument('--additional-record', action='append', default=[], type=Path)
    args = parser.parse_args()
    if args.command == 'requirements':
        result = requirements(args.projection, args.records)
    else:
        trust = ReleaseTrust(keyring=args.keyring, expected_key_sha256=args.key_sha256,
            release=args.release, signature=args.signature, packages=args.packages,
            index_path=args.index_path, origin=args.origin)
        additions = [component_from_record(path, args.cache) for path in args.additional_record]
        manifest = prepare(profile_path=args.profile, projection_path=args.projection,
            records_directory=args.records, archive_directory=args.cache, catalog_path=args.catalog,
            destination=args.output, trust=trust, generated_bindings=strict(regular(args.generated_bindings).read_bytes()),
            additional_components=additions)
        result = {'state': 'prepared-inputs', 'manifest_sha256': digest(args.output / 'manifest.json'),
            'catalog_sha256': manifest['catalog_sha256'], 'bytes': manifest['bytes'],
            'configured_installed_root': False, 'native_finalizer_required': sorted(CHECKS)}
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
