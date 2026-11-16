"""Signed root-owned native releases, separate from descriptive candidate wishes."""
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import time

from .pending import SetupError, _strict, _encode
from ..shared.openpgp import public_key_only
from .runtime_compat import RUNTIME_PROFILE,RUNTIME_VERSION,RUNTIME_ARCHIVE_SHA256,compatible,cpu_features

DIRECTORY = Path('/usr/share/toddy/software/native')
SOURCES = Path('/etc/apt/sources.list.d/toddy-native.list')
RELEASE_PACKAGES = {'agent-backend':{'toddy-agent','toddy-executor','nodejs'},
    'local-runtime':{'llama-cpp'},'agent-local':{'toddy-agent','toddy-executor','nodejs','llama-cpp'}}
PACKAGES = set.union(*RELEASE_PACKAGES.values())
RELEASE_PERMISSIONS = {'agent-backend':['user-agent-service','privileged-executor-without-grant'],
    'local-runtime':['optional-local-cpu-runtime-without-model'],
    'agent-local':['user-agent-service','privileged-executor-without-grant','optional-local-cpu-runtime-without-model']}
LOCAL_CHECKS = {'local_runtime_cpu_denial','runtime_profile_compatibility'}
REQUIRED_CHECKS = {'absent_agent_setup', 'polkit_owner_authorization', 'signed_metadata_tamper_rejected',
    'exact_closure_install', 'package_remove_upgrade_recovery', 'no_automatic_activation',
    'no_grant_or_model_or_keys', 'reconnect_no_replay', 'offline_deferred'}
POSTCONDITIONS = {
    '/usr/lib/toddy/broker/service.py': 'toddy-agent',
    '/usr/lib/toddy/worker/worker.mjs': 'toddy-agent',
    '/usr/lib/systemd/user/toddy-agent.service': 'toddy-agent',
    '/usr/lib/toddy/executor/service.py': 'toddy-executor',
    '/usr/lib/systemd/system/toddy-executor.service': 'toddy-executor',
    '/usr/bin/node': 'nodejs',
    '/usr/bin/llama-server':'llama-cpp','/usr/bin/llama-completion':'llama-cpp',
    '/usr/share/doc/llama-cpp/cpu-profile.json':'llama-cpp'}
HEX = re.compile('[a-f0-9]{64}\\Z')
VERSION = re.compile('[0-9][A-Za-z0-9.+:~_-]{0,95}\\Z')
ID = re.compile('[a-z][a-z0-9-]{0,63}\\Z')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def private_metadata(path, *, owner_uid=0, maximum=65536):
    for parent in (path.parent, *path.parent.parents):
        info = parent.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != owner_uid or stat.S_IMODE(info.st_mode) & 0o022:
            raise SetupError('release_custody')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != owner_uid or info.st_nlink != 1 or \
                stat.S_IMODE(info.st_mode) & 0o022 or not 0 < info.st_size <= maximum:
            raise SetupError('release_custody')
        data = os.read(fd, maximum + 1)
        if len(data) != info.st_size:
            raise SetupError('release_custody')
        return data
    finally:
        os.close(fd)


def signature(keyring, signature_path, catalog_path):
    result = subprocess.run(['/usr/bin/gpgv', '--status-fd=1', '--keyring', str(keyring),
        *([str(signature_path)] if signature_path is not None else []), str(catalog_path)], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        timeout=10, env={'PATH':'/usr/bin:/usr/sbin', 'HOME':'/nonexistent', 'LC_ALL':'C'})
    if result.returncode or len(result.stdout) > 16384:
        raise SetupError('release_signature')
    statuses=result.stdout.decode('ascii',errors='strict').splitlines()
    if any(line.startswith('[GNUPG:] '+tag+' ') for line in statuses for tag in ('BADSIG','ERRSIG','EXPSIG','EXPKEYSIG','REVKEYSIG','KEYREVOKED','KEYEXPIRED','SIGEXPIRED','NO_PUBKEY')):
        raise SetupError('release_signature')
    valid = []
    for line in result.stdout.decode('ascii', errors='strict').splitlines():
        if line.startswith('[GNUPG:] VALIDSIG '):
            fields = line.split()
            valid.append(fields[-1] if len(fields) == 12 else fields[2])
    if len(valid) != 1 or not re.fullmatch('[A-F0-9]{40}|[A-F0-9]{64}', valid[0]):
        raise SetupError('release_signature')
    return valid[0]


def exact(value, fields):
    if not isinstance(value, dict) or set(value) != set(fields):
        raise SetupError('release_schema')


def digest_field(value):
    if not isinstance(value, str) or not HEX.fullmatch(value):
        raise SetupError('release_schema')


def validate_declaration(row,*,directory,read=private_metadata):
    """Pure curated metadata validation; no readiness/authority or effect."""
    release_id=row.get('id') if isinstance(row,dict) else None
    if not isinstance(release_id,str) or release_id not in RELEASE_PACKAGES:raise SetupError('release_schema')
    fields={'id','artifact_id','packages','postconditions','terms_sha256','license','permissions',
                'requires_owner_authorization','auto_activate'}
    local='llama-cpp' in RELEASE_PACKAGES[release_id]
    exact(row,fields|({'runtime_profile'} if local else set()))
    if local and _encode(row['runtime_profile'])!=_encode(RUNTIME_PROFILE):raise SetupError('native_runtime_profile_changed')
    if not isinstance(row['artifact_id'], str) or not ID.fullmatch(row['artifact_id']) or \
            row['requires_owner_authorization'] is not True or row['auto_activate'] is not False or \
            row['permissions'] != RELEASE_PERMISSIONS[release_id] or \
            not isinstance(row['license'], str) or not 0 < len(row['license']) <= 256:
        raise SetupError('release_schema')
    for field in ('terms_sha256',):
        digest_field(row[field])
    terms = read(directory/'terms'/(row['terms_sha256']+'.txt'), maximum=65536)
    if sha(terms) != row['terms_sha256']:
        raise SetupError('release_terms')
    terms.decode('utf-8', errors='strict')
    packages = row['packages']
    if not isinstance(packages,list) or len(packages) != len(RELEASE_PACKAGES[release_id]):
        raise SetupError('release_schema')
    seen = set()
    for package in packages:
        exact(package, ('name','version','architecture','bytes','installed_bytes','sha256'))
        if not isinstance(package['name'],str) or package['name'] not in PACKAGES or package['name'] in seen or \
                not isinstance(package['version'],str) or not VERSION.fullmatch(package['version']) or \
                package['architecture'] not in ('amd64','all') or \
                any(type(package[key]) is not int or not 0 < package[key] <= 2*1024**3 for key in ('bytes','installed_bytes')):
            raise SetupError('release_schema')
        digest_field(package['sha256']); seen.add(package['name'])
        if package['name']=='llama-cpp' and (package['version']!=RUNTIME_VERSION or package['sha256']!=RUNTIME_ARCHIVE_SHA256 or package['architecture']!='amd64'):
            raise SetupError('native_runtime_profile_changed')
    if seen != RELEASE_PACKAGES[release_id]:
        raise SetupError('release_schema')
    expected = {path:owner for path,owner in POSTCONDITIONS.items() if owner in seen}
    if not isinstance(row['postconditions'],dict) or set(row['postconditions']) != set(expected):
        raise SetupError('release_schema')
    for digest in row['postconditions'].values():
        digest_field(digest)
    return local


ASSISTANT_MANIFEST=Path('/usr/share/doc/toddy-assistant/source-manifest.json')
POLICY_PATH='/usr/share/polkit-1/actions/io.github.markaraujo.Toddy.AcquireNative.policy'
MIN_CODE_PATHS={'/usr/bin/toddy',POLICY_PATH,*('/usr/lib/toddy/setup/'+name for name in
    ('pending.py','acquisition.py','acquisition_journal.py','native_backend.py','native_acquire.py','releases.py','platform.py','runtime_compat.py')),
    '/usr/lib/toddy/shared/openpgp.py','/usr/lib/toddy/ui/app.py','/usr/lib/toddy/ui/model.py'}
COMPONENT_CHECKS={'absent_agent_native_backend','polkit_helper_owner_authentication','other_uid_refused',
    'signed_metadata_tamper_rejected','safe_stop_before_write','offline_deferred',
    'native_write_reconciliation_no_replay','native_package_postconditions',
    'no_automatic_activation','no_grant_or_model_or_keys'}
LEVELS={'native-components','native-full-flow'}


def code_pinset(read=private_metadata):
    data=read(ASSISTANT_MANIFEST);manifest=_strict(data)
    if not isinstance(manifest,dict) or manifest.get('schema_version')!=1 or manifest.get('package')!='toddy-assistant' or not isinstance(manifest.get('payload'),dict):
        raise SetupError('release_code_pins')
    files={}
    for virtual,row in manifest['payload'].items():
        path=Path(virtual)
        if not path.is_absolute() or '..' in path.parts or virtual.startswith('//') or any(ord(c)<32 for c in virtual) or path.as_posix()!=virtual:raise SetupError('release_code_pins')
        if not (virtual.startswith('/usr/lib/toddy/') or virtual in ('/usr/bin/toddy',POLICY_PATH)):continue
        if not isinstance(row,dict):raise SetupError('release_code_pins')
        digest_field(row.get('sha256'))
        actual=sha(read(path,maximum=1048576))
        if actual!=row['sha256']:raise SetupError('release_code_pins')
        files[virtual]=actual
    if not MIN_CODE_PATHS<=set(files):raise SetupError('release_code_pins')
    return {'assistant_code_manifest_sha256':sha(_encode(files)),'files':files}


def describe(row,*,revision,generation,origin,level,hardware=cpu_features):
    """Advisory descriptor only; component fixtures cannot mint catalog readiness."""
    local='llama-cpp' in RELEASE_PACKAGES[row['id']]
    compatibility=compatible(hardware=hardware) if local else {}
    review={'version':1,'release_id':row['id'],'artifact_id':row['artifact_id'],
        'catalog_revision':revision,'repository_id':'toddy-native','repository_origin':origin,'catalog_generation':generation,
        'qualification_level':level,'preview_only':level!='native-full-flow',
        'packages':row['packages'],'postconditions':row['postconditions'],
        'download_bytes':sum(p['bytes'] for p in row['packages']),
        'installed_bytes':sum(p['installed_bytes'] for p in row['packages']),
        'terms_sha256':row['terms_sha256'],'license':row['license'],'permissions':row['permissions'],
        'requires_owner_authorization':True,'auto_activate':False}
    if local:review.update(runtime_profile=row['runtime_profile'],**compatibility)
    review['review_sha256']=sha(_encode(review))
    return review


class NativeCatalog:
    """Production callers use load() fixed defaults; injection is source-test only."""
    @classmethod
    def load(cls, *, directory=DIRECTORY, sources=SOURCES, read=private_metadata,
             verify=signature, clock=time.time, hardware=cpu_features):
        trust = _strict(read(directory/'trust.json'))
        exact(trust, ('version', 'fingerprint', 'keyring_sha256'))
        if type(trust['version']) is not int or trust['version'] != 1 or not isinstance(trust['fingerprint'], str) or \
                not re.fullmatch('[A-F0-9]{40}|[A-F0-9]{64}', trust['fingerprint']):
            raise SetupError('release_trust')
        digest_field(trust['keyring_sha256'])
        keyring_data=read(directory/'archive-keyring.gpg',maximum=1048576)
        try:public_key_only(keyring_data)
        except ValueError:raise SetupError('release_public_keyring_required') from None
        if sha(keyring_data) != trust['keyring_sha256']:
            raise SetupError('release_trust')
        data = read(directory/'releases.json'); read(directory/'releases.json.asc', maximum=16384)
        if verify(directory/'archive-keyring.gpg', directory/'releases.json.asc', directory/'releases.json') != trust['fingerprint']:
            raise SetupError('release_signature')
        # Re-read after gpgv's independent open; changed bytes are not trusted.
        if data != read(directory/'releases.json'):
            raise SetupError('release_changed')
        value = _strict(data)
        exact(value, ('version', 'generation', 'not_before', 'expires', 'repository', 'releases'))
        if type(value['version']) is not int or value['version'] != 1 or any(type(value[k]) is not int for k in ('generation','not_before','expires')) or \
                not 1 <= value['generation'] < 2**53 or not value['not_before'] <= clock() < value['expires'] or \
                not 0 < value['expires'] - value['not_before'] <= 31*86400:
            raise SetupError('release_expired')
        repo = value['repository']
        exact(repo, ('id','sources_sha256','inrelease_sha256','inrelease_bytes'))
        if repo['id'] != 'toddy-native' or type(repo['inrelease_bytes']) is not int or not 0 < repo['inrelease_bytes'] <= 1048576:
            raise SetupError('release_origin')
        digest_field(repo['sources_sha256']); digest_field(repo['inrelease_sha256'])
        source_data=read(sources)
        if sha(source_data) != repo['sources_sha256']:
            raise SetupError('release_origin')
        lines=[line.strip() for line in source_data.decode('ascii',errors='strict').splitlines() if line.strip() and not line.lstrip().startswith('#')]
        pattern=r'deb \[signed-by='+re.escape(str(directory/'archive-keyring.gpg'))+r'\] (\S+) (?:[a-z0-9][a-z0-9.-]{0,63}|\./)(?: main)?'
        match=re.fullmatch(pattern,lines[0]) if len(lines)==1 else None
        if match is None:raise SetupError('release_origin')
        from urllib.parse import urlsplit
        origin=urlsplit(match[1])
        if origin.username or origin.password or origin.query or origin.fragment or not (
            origin.scheme=='https' and origin.hostname or origin.scheme=='file' and not origin.netloc and origin.path==str(directory/'repository')):
            raise SetupError('release_origin')
        if not isinstance(value['releases'], list) or len(value['releases']) > 3:
            raise SetupError('release_schema')
        instance = cls(); instance.revision = sha(data); instance.value = value
        instance.repository_origin=match[1]; instance.directory = directory; instance.releases = {}; instance.levels = {}; instance.fingerprint = trust['fingerprint']; instance.keyring_sha256 = trust['keyring_sha256']; instance.verify = verify; instance.read = read; instance.sources = sources; instance.clock = clock; instance.hardware = hardware
        for release in value['releases']:
            if isinstance(release,dict) and isinstance(release.get('id'),str) and release['id'] in instance.releases:raise SetupError('release_schema')
            instance._release(release, read)
            instance.releases[release['id']] = release
        return instance

    def _release(self, row, read):
        if not isinstance(row,dict) or 'qualification_sha256' not in row:raise SetupError('release_qualification')
        digest_field(row['qualification_sha256'])
        declaration={key:value for key,value in row.items() if key!='qualification_sha256'}
        local=validate_declaration(declaration,directory=self.directory,read=read)
        release_id=row['id'];packages=row['packages']
        report_data = read(self.directory/'qualifications'/(row['qualification_sha256']+'.json'))
        if sha(report_data) != row['qualification_sha256']:
            raise SetupError('release_qualification')
        report = _strict(report_data)
        exact(report, ('version','scope','native_result','qualification_level','package_set_sha256','code_pins','trust_pins','checks','retained_evidence_sha256'))
        level=report['qualification_level']
        if not isinstance(level,str) or level not in LEVELS:raise SetupError('release_qualification')
        expected_checks=(COMPONENT_CHECKS if level=='native-components' else REQUIRED_CHECKS)|(LOCAL_CHECKS if local else set())
        trust_pins={'fingerprint':self.fingerprint,'keyring_sha256':self.keyring_sha256,
            'sources_sha256':self.value['repository']['sources_sha256'],'inrelease_sha256':self.value['repository']['inrelease_sha256']}
        if report['trust_pins']!=trust_pins or report['code_pins']!=code_pinset(read):raise SetupError('release_code_or_trust_changed')
        if type(report['version']) is not int or report['version'] != 1 or report['scope'] != 'installed-native-agent-acquisition' or report['native_result'] != 'passed' or \
                report['package_set_sha256'] != sha(_encode(packages)) or not isinstance(report['checks'],dict) or \
                set(report['checks']) != expected_checks or any(value is not True for value in report['checks'].values()):
            raise SetupError('release_qualification')
        digest_field(report['retained_evidence_sha256'])
        evidence=read(self.directory/'qualifications'/(report['retained_evidence_sha256']+'.evidence.json'))
        if sha(evidence)!=report['retained_evidence_sha256']:
            raise SetupError('release_qualification')
        native=_strict(evidence)
        if not isinstance(native,dict) or native.get('scope')!='installed-native-agent-acquisition' or native.get('environment')!='native-installed-user' or native.get('fixture_only') is not False or type(native.get('runner_exit')) is not int or native['runner_exit']!=0 or type(native.get('postconditions_exit')) is not int or native['postconditions_exit']!=0 or native.get('package_set_sha256')!=report['package_set_sha256'] or native.get('qualification_level')!=level or native.get('code_pins')!=report['code_pins'] or native.get('trust_pins')!=trust_pins:
            raise SetupError('release_qualification')
        self.levels[release_id]=level

    def require_full_flow(self):
        if not self.releases or any(level!='native-full-flow' for level in self.levels.values()):raise SetupError('release_full_flow_required')
        if not ({'agent-backend','local-runtime'}<=set(self.releases) or 'agent-local' in self.releases):raise SetupError('release_full_scope_required')
        return {'version':1,'native_acquisition':'native-full-flow','catalog_revision':self.revision,'release_ids':sorted(self.releases)}

    def ensure_current(self):
        current=type(self).load(directory=self.directory,sources=self.sources,read=self.read,verify=self.verify,clock=self.clock,hardware=self.hardware)
        if current.revision!=self.revision:raise SetupError('release_changed')


    def terms(self,release_id='agent-backend'):
        if not isinstance(release_id,str) or release_id not in self.releases:raise SetupError('release_unavailable')
        digest=self.releases[release_id]['terms_sha256']
        data=self.read(self.directory/'terms'/(digest+'.txt'))
        if sha(data)!=digest:raise SetupError('release_terms')
        return data.decode('utf-8',errors='strict')


    def review(self, release_id='agent-backend'):
        if not isinstance(release_id,str) or release_id not in self.releases:
            raise SetupError('release_unavailable')
        return describe(self.releases[release_id],revision=self.revision,generation=self.value['generation'],
            origin=self.repository_origin,level=self.levels[release_id],hardware=self.hardware)
