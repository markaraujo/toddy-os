#!/usr/bin/env python3
"""Deterministically stage the lightweight assistant; no archive/install/target writes.

Native archive ownership/dependency verification stays in stage_package.py and
its designated-guest transaction flow. No maintainer scripts are generated.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat

APP_ID='io.github.markaraujo.Toddy'
PACKAGE='toddy-assistant'
MODULES={
    'ui':('app.py','bridge.py','credentials.py','model.py','task_state.py'),
    'setup':('pending.py',),
    'shared':('json.py',),
    'connections':('secret_store.py',),
}
DATA=(
    'ui/phase2/messages.json',
    'ui/phase2/identity.json',
    'config/phase2/software-catalog.json',
)
DOCS=(
    ('runtime/ui/README.md','native-ui.md'),
    ('runtime/setup/README.md','setup-intent.md'),
    ('runtime/connections/README.md','protected-connections.md'),
)
LAUNCHER='''#!/usr/bin/python3 -I
# Original Toddy OS code: MIT. Fixed package path; no cwd/PYTHONPATH imports.
import runpy
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, '/usr/lib')
runpy.run_module('toddy.ui.app', run_name='__main__', alter_sys=True)
'''
INIT='"""Original Toddy OS package namespace; optional components own child modules."""\n'
README='''Toddy lightweight assistant stage

This payload is the agent-independent native setup/conversation client. It can
open with broker/Node/Pi/executor/models absent; corresponding task controls stay
unavailable. API/local/later preferences are non-secret intent, not activation.
The package owns /usr/lib/toddy's root namespace plus ui/setup/shared/connections.
Optional agent/executor/voice/integration packages own only their child payloads.
The exact icon identity is supplied by toddy-branding; approved artwork is not
copied, modified or owned here.

The fixed /usr/bin/toddy launcher uses Python isolated mode, disables bytecode
writes and imports only the fixed /usr/lib/toddy namespace. Installed data is at
/usr/share/toddy. No environment/cwd import alias or cyclic runtime symlink is
required. The desktop identity remains io.github.markaraujo.Toddy. The optional
shortcut target is this same fixed launcher. No global binding is assigned or
existing shortcut/user setting changed; conflict-checked registration remains
B06 runtime work. Ordinary application activation is the fallback.

There is no DEBIAN control directory, maintainer script, secret, user profile,
model, worker closure, root service, autostart, keybinding assignment or package
transaction in this stage. Native stage_package.py still verifies ownership,
notices and target identity before building a native archive. This generator
never invokes it and never installs onto the host or target. Actual native
runtime dependency versions, package install/upgrade/removal and UI lifecycle
must be qualified separately. Stage/import fixtures are not B06 acceptance.

Original Python/generator code is MIT (copyright). Original documentation,
semantic copy/catalog inputs and approved art references are CC BY4.0
(CC-BY-4.0.txt). Referenced upstream names/project links are information only;
no third-party executable or art is incorporated by this package. The source
manifest records exact file hashes and original-art references, with no host
paths, runtime state, credentials, timestamps or invented source-build success.
'''


class StageError(ValueError):
    pass


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encode(value):
    return (json.dumps(value,sort_keys=True,ensure_ascii=False,indent=2)+'\n').encode()


def stage(repository,destination,*,version='0.2.0-1+toddy1'):
    repository=Path(repository)
    destination=Path(destination)
    if not repository.is_absolute() or repository.resolve()!=repository or not repository.is_dir():
        raise StageError('canonical_repository_required')
    if not destination.is_absolute() or destination.resolve()!=destination or \
            destination.exists() or destination.is_symlink() or not destination.parent.is_dir():
        raise StageError('fresh_canonical_stage_required')
    if not isinstance(version,str) or not re.fullmatch(r'[0-9][0-9A-Za-z.+:~_-]{0,127}',version):
        raise StageError('invalid_package_version')
    inputs={}
    payload={}

    def source(relative):
        path=repository/relative
        for component in (path,*path.parents):
            if component.is_symlink():
                raise StageError('symlink_source_refused')
        info=path.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1:
            raise StageError('regular_source_required')
        data=path.read_bytes()
        inputs[relative]={'bytes':len(data),'sha256':sha(data)}
        return data

    def put(relative,data,mode=0o644,origin=None):
        if not relative.startswith('/') or '..' in Path(relative).parts or relative in payload:
            raise StageError('invalid_payload_path')
        payload[relative]={'bytes':len(data),'sha256':sha(data),'mode':format(mode,'04o'),
                           'source':origin or 'generated-by-assistant-package'}
        path=destination/relative.lstrip('/')
        path.parent.mkdir(mode=0o755,parents=True,exist_ok=True)
        path.write_bytes(data)
        path.chmod(mode)

    # Validate all identity/provenance inputs before creating a stage. A later
    # unexpected write failure leaves the partial stage for explicit inspection.
    identity=json.loads(source('ui/phase2/identity.json'))
    if identity['application']['id']!=APP_ID or identity['application']['icon_name']!=APP_ID or \
            identity['assistant_package']!=PACKAGE:
        raise StageError('application_identity_mismatch')
    package_map=json.loads(source('config/phase2/packages.json'))
    rows=[row for row in package_map['packages'] if row['name']==PACKAGE]
    if len(rows)!=1 or rows[0].get('offline_base') is not True or rows[0].get('optional_backend') is None:
        raise StageError('offline_ownership_contract')
    template=source('ui/phase2/io.github.markaraujo.Toddy.desktop.in').decode('utf-8')
    if template.count('@TODDY_EXECUTABLE@')!=1 or 'Icon='+APP_ID+'\n' not in template or \
            'DBusActivatable=false\n' not in template:
        raise StageError('desktop_identity_mismatch')
    desktop=template.replace('@TODDY_EXECUTABLE@','/usr/bin/toddy')
    if '@' in desktop or 'pkexec' in desktop or 'sudo' in desktop:
        raise StageError('unsafe_desktop_template')
    assets=json.loads(source('assets/brand/assets.json'))
    icon_relative=identity['protected_identity']
    if icon_relative!='assets/brand/toddy-os-system-icon.png':
        raise StageError('approved_icon_reference')
    icon=source(icon_relative)
    expected=[row for row in assets if row['file']=='toddy-os-system-icon.png']
    if len(expected)!=1 or expected[0]['sha256']!=sha(icon):
        raise StageError('approved_icon_integrity')
    recipe='scripts/build/phase2/assistant_package.py'
    source(recipe)
    code={f'runtime/{name}/{filename}':source(f'runtime/{name}/{filename}')
          for name,files in MODULES.items() for filename in files}
    data={relative:source(relative) for relative in DATA}
    docs={name:source(relative) for relative,name in DOCS}
    notices={'copyright':source('LICENSE'),'CC-BY-4.0.txt':source('LICENSES/CC-BY-4.0.txt')}
    destination.mkdir(mode=0o755)
    put('/usr/lib/toddy/__init__.py',INIT.encode())
    for name in MODULES:
        put('/usr/lib/toddy/'+name+'/__init__.py',b'"""Original Toddy OS component."""\n')
    for relative,contents in code.items():
        put('/usr/lib/toddy/'+relative.removeprefix('runtime/'),contents,origin=relative)
    for relative,contents in data.items():
        put('/usr/share/toddy/'+relative,contents,origin=relative)
    put('/usr/bin/toddy',LAUNCHER.encode(),0o755)
    put('/usr/share/applications/'+APP_ID+'.desktop',desktop.encode(),
        origin='ui/phase2/io.github.markaraujo.Toddy.desktop.in')
    put('/usr/share/toddy/ui/shortcut.json',encode({'schema_version':1,'application_id':APP_ID,
        'command':'/usr/bin/toddy','default_binding':None,'requires_conflict_check':True}))
    doc='/usr/share/doc/'+PACKAGE+'/'
    for name,contents in notices.items():
        put(doc+name,contents,origin='LICENSE' if name=='copyright' else 'LICENSES/CC-BY-4.0.txt')
    for name,contents in docs.items():
        put(doc+name,contents,origin=next(relative for relative,target in DOCS if target==name))
    put(doc+'README',README.encode())
    manifest={'schema_version':1,'package':PACKAGE,'version':version,'architecture':'all',
        'status':'payload-staged-not-archive-or-runtime-acceptance','native_archive_built':False,
        'installed':False,'offline_base':True,'namespace_owner':PACKAGE,
        'optional_backend':'toddy-agent','requires_capabilities':rows[0]['requires_capabilities'],
        'source_inputs':dict(sorted(inputs.items())),'payload':dict(sorted(payload.items())),
        'original_asset_references':[{'source':icon_relative,'sha256':sha(icon),
            'installed_icon_name':APP_ID,'payload_owner':'toddy-branding','copied_by_this_package':False}],
        'excluded_components':['broker','worker','engine','executor','voice','integrations','local-models'],
        'maintainer_scripts':[],'active_global_shortcut':None}
    # The manifest intentionally excludes its own hash to avoid a recursive hash.
    put(doc+'source-manifest.json',encode(manifest))
    for path in sorted(destination.rglob('*'),key=lambda value:len(value.parts),reverse=True):
        if path.is_dir():path.chmod(0o755)
        os.utime(path,(0,0),follow_symlinks=False)
    destination.chmod(0o755)
    os.utime(destination,(0,0))
    return manifest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository',type=Path,default=Path(__file__).resolve().parents[3])
    parser.add_argument('--destination',type=Path,required=True)
    parser.add_argument('--version',default='0.2.0-1+toddy1')
    args=parser.parse_args()
    try:
        manifest=stage(args.repository,args.destination,version=args.version)
    except (StageError,OSError,ValueError,KeyError) as exc:
        raise SystemExit('Assistant staging refused: '+type(exc).__name__) from None
    print(json.dumps({'package':manifest['package'],'status':manifest['status'],
                      'files':len(manifest['payload'])+1},sort_keys=True))


if __name__=='__main__':main()
