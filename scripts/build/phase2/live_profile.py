"""Fresh source-attributed GNOME live account/session after real finalization."""
import configparser
import hashlib
import io
import os
from pathlib import Path
import re
import stat
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from runtime.installer.live_session import LIVE_UID,LIVE_USER,IMAGE_CLASS,UNIT,UNIT_PATH
from runtime.installer.native_finalizer import payload_module
from runtime.installer.composition import SOURCES,source_path,secured,validate_finalizer_report
from runtime.installer.installed_identity import regular

WORK=Path('/sources/stage/toddy-live-image-2')
GENERATED_INPUT=Path('/sources/stage/toddy-live-native-inputs/generated-entries.json')
HELPER='/usr/libexec/toddy-live-session'
RULE='/etc/polkit-1/rules.d/49-toddy-live-installer.rules'
PRODUCER='/usr/lib/toddy/installer/live_session.py'
WRAPPER=b'''#!/usr/bin/python3 -I
import runpy
import sys
sys.dont_write_bytecode=True
sys.path.insert(0,'/usr/lib')
runpy.run_module('toddy.installer.live_session',run_name='__main__',alter_sys=True)
'''
UNIT_TEXT='''[Unit]
Description=Attribute the fresh Toddy live GNOME session
ConditionKernelCommandLine=toddy.live
ConditionPathExists=/run/toddy/live-session
ConditionPathExists=/usr/share/toddy/live-image.json
After=gdm.service systemd-logind.service
Requires=gdm.service
PartOf=gdm.service
StartLimitIntervalSec=60
StartLimitBurst=3

[Service]
Type=simple
ExecStart=/usr/libexec/toddy-live-session produce
RuntimeDirectory=toddy-live-owner
RuntimeDirectoryMode=0700
UMask=0077
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
PrivateDevices=yes
CapabilityBoundingSet=
RestrictAddressFamilies=AF_UNIX
ReadWritePaths=/run/toddy-live-owner
Restart=on-failure
RestartSec=5

[Install]
WantedBy=graphical.target
'''
RULE_TEXT='''// Live image only. The root entry independently verifies boot/unit/session facts.
polkit.addRule(function(action, subject) {
    if (action.id === "io.github.markaraujo.Toddy.Install" &&
        action.lookup("program") === "/usr/libexec/toddy-installer-auth" &&
        subject.user === "toddy-live" && subject.local === true && subject.active === true) {
        return polkit.Result.YES;
    }
});
'''
DROPIN='''[Unit]
ConditionKernelCommandLine=toddy.live
ConditionPathExists=/run/toddy/live-session
ConditionPathExists=/usr/share/toddy/live-image.json
'''
DCONF='''[org/gnome/desktop/lockdown]
disable-lock-screen=true

[org/gnome/desktop/screensaver]
lock-enabled=false

[org/gnome/desktop/session]
idle-delay=uint32 0
'''
PAM_GUARD='''# Fresh live user only; preserve the selected GDM50.2 upstream stack below.
auth requisite pam_succeed_if.so user = toddy-live quiet
auth requisite pam_exec.so quiet /usr/libexec/toddy-live-session pam
'''


def media_identity(payload_manifest_sha256,policy_sha256):
    if any(not isinstance(value,str) or not re.fullmatch('[a-f0-9]{64}',value) for value in (payload_manifest_sha256,policy_sha256)):raise ValueError('Live media input hash')
    p=payload_module()
    return hashlib.sha256(p.encoded({'version':1,'kind':'toddy-live-media-v1',
        'payload_manifest_sha256':payload_manifest_sha256,'policy_sha256':policy_sha256,
        'producer_sha256':p.digest(__file__)})).hexdigest()


def account_transform(data):
    """Add only one fresh locked UID/GID1000; never reuse a builder identity."""
    expected={'passwd':7,'group':4,'shadow':9,'gshadow':4};rows={}
    for name,count in expected.items():
        rows[name]=[line.split(':') for line in data[name].decode().splitlines()]
        if any(len(row)!=count for row in rows[name]) or len({row[0] for row in rows[name]})!=len(rows[name]):raise ValueError('Live account input format')
    if any(row[0]==LIVE_USER or row[2]==str(LIVE_UID) for row in rows['passwd']+rows['group']):raise ValueError('Live identity collision')
    if any(row[0] in ('lfs','builder','tester') or row[2].isdigit() and 1000<=int(row[2])<65534 for row in rows['passwd']):raise ValueError('Live inherited personal identity')
    if not any(row[0]=='root' and row[1]=='!' for row in rows['shadow']) or not any(row==['wheel','x','97',''] for row in rows['group']):raise ValueError('Live root/wheel policy')
    result=dict(data)
    additions={'passwd':f'{LIVE_USER}:x:{LIVE_UID}:{LIVE_UID}:Toddy Live Session:/home/{LIVE_USER}:/bin/bash\n',
        'group':f'{LIVE_USER}:x:{LIVE_UID}:\n','shadow':f'{LIVE_USER}:!:::::::\n','gshadow':f'{LIVE_USER}:!::\n'}
    for name,text in additions.items():
        if data[name] and not data[name].endswith(b'\n'):raise ValueError('Live account missing final newline')
        result[name]=data[name]+text.encode()
    return result


def _selected(root,manifest,virtual):
    p=payload_module();path=root/virtual.lstrip('/');row=manifest['ownership']['entries'].get(virtual,{})
    if path.parent.resolve()!=path.parent or path.is_symlink() or not row.get('sha256') or p.digest(path)!=row['sha256']:raise ValueError('Live input differs from selected archive ownership')
    return path


def plan(root,manifest,media_id,policy_sha256):
    p=payload_module();manifest_sha=hashlib.sha256(p.encoded(manifest)).hexdigest()
    if media_id!=media_identity(manifest_sha,policy_sha256):raise ValueError('Live media identity differs')
    versions={row['name']:row['version'] for row in manifest['components']}
    for name,version in (('gdm','50.2'),('gsettings-desktop-schemas','50.1'),('dconf','0.49.0')):
        if not versions.get(name,'').startswith(version+'-'):raise ValueError('Live frozen native component unavailable')
    # Schema names/types are read from actual selected archive XML, not guesses.
    for schema,keys in {'org.gnome.desktop.lockdown':{'disable-lock-screen':'b'},
        'org.gnome.desktop.screensaver':{'lock-enabled':'b'},'org.gnome.desktop.session':{'idle-delay':'u'}}.items():
        path=_selected(root,manifest,'/usr/share/glib-2.0/schemas/'+schema+'.gschema.xml')
        tree=ET.fromstring(path.read_bytes());node=next((row for row in tree.iter('schema') if row.get('id')==schema),None)
        if node is None or any(not any(row.get('name')==key and row.get('type')==kind for row in node.findall('key')) for key,kind in keys.items()):raise ValueError('Live schema contract changed')
    for virtual in (PRODUCER,'/usr/bin/dconf','/usr/bin/loginctl','/usr/bin/systemctl','/usr/lib/security/pam_exec.so','/usr/lib/security/pam_succeed_if.so','/usr/share/wayland-sessions/gnome.desktop'):_selected(root,manifest,virtual)
    config=_selected(root,manifest,'/etc/gdm/custom.conf')
    conf=configparser.ConfigParser(interpolation=None);conf.optionxform=str;conf.read_string(config.read_text())
    if not conf.has_section('daemon'):raise ValueError('Live GDM config format')
    for key,value in {'AutomaticLoginEnable':'true','AutomaticLogin':LIVE_USER,'TimedLoginEnable':'false','InitialSetupEnable':'false','WaylandEnable':'true'}.items():conf.set('daemon',key,value)
    rendered=io.StringIO();conf.write(rendered)
    pam=_selected(root,manifest,'/etc/pam.d/gdm-autologin').read_bytes()
    if b'pam_succeed_if.so uid >= 1000 quiet' not in pam or b'account  include        system-account' not in pam or b'session  include        system-session' not in pam or b'toddy-live' in pam:raise ValueError('Live GDM upstream PAM contract changed')
    account_data={name:(root/'etc'/name).read_bytes() for name in ('passwd','group','shadow','gshadow')}
    transformed=account_transform(account_data)
    files={'/etc/'+name:(data,0o600 if name in ('shadow','gshadow') else 0o644) for name,data in transformed.items()}
    files.update({'/etc/gdm/custom.conf':(rendered.getvalue().encode(),0o644),'/etc/pam.d/gdm-autologin':(PAM_GUARD.encode()+pam,0o644),
        HELPER:(WRAPPER,0o755),str(UNIT_PATH):(UNIT_TEXT.encode(),0o644),RULE:(RULE_TEXT.encode(),0o644),
        '/etc/systemd/system/gdm.service.d/50-toddy-live.conf':(DROPIN.encode(),0o644),
        '/etc/dconf/db/toddy-live.d/00-session':(DCONF.encode(),0o644)})
    profile=root/'etc/dconf/profile/user'
    if profile.exists() or profile.is_symlink():
        previous=_selected(root,manifest,'/etc/dconf/profile/user').read_bytes()
        lines=previous.decode().splitlines()
        if not lines or lines[0]!='user-db:user' or any(not re.fullmatch('(user-db:user|system-db:[a-zA-Z0-9_-]+)',line) for line in lines) or any('toddy-live' in line for line in lines):raise ValueError('Live dconf profile contract')
    else:previous=b'user-db:user\n'
    existing_lines=previous.decode().splitlines()
    live_profile='\n'.join([existing_lines[0],'system-db:toddy-live',*existing_lines[1:]])+'\n'
    files['/etc/dconf/profile/user']=(live_profile.encode(),0o644)
    image={'version':1,'image_class':'phase2-live-installer','live_uid':LIVE_UID,'live_user':LIVE_USER,'media_id':media_id,
        'producer_sha256':p.digest(root/PRODUCER.lstrip('/')),'unit_sha256':hashlib.sha256(UNIT_TEXT.encode()).hexdigest(),'profile_source_sha256':p.digest(__file__)}
    files[str(IMAGE_CLASS)]=(p.encoded(image),0o644)
    links={'/etc/systemd/system/graphical.target.wants/'+UNIT:str(UNIT_PATH)}
    return files,links,image


def stage(assembly,manifest,policy,media_id,system):
    """Post-finalizer live-only transform; no production gate or boot claim."""
    from scripts.build.phase2.resource_recipe import snapshot,save
    system.require_root();assembly.recheck();p=payload_module();root=Path(assembly.root);work=Path(assembly.work)
    mvp=manifest.get('delivery_class')=='phase2-mvp-preinstalled-v1'
    expected_work=Path('/sources/stage/toddy-mvp-live-image-2') if mvp else WORK
    generated_input=Path('/sources/stage/toddy-mvp-live-native-inputs/generated-entries.json') if mvp else GENERATED_INPUT
    if mvp and manifest.get('g2_eligible') is not False:raise ValueError('MVP live profile cannot be G2 eligible')
    if work!=expected_work or root.parent!=work or root.resolve()!=root:raise ValueError('Live profile requires fixed reviewed generation2')
    intent=work/'live-profile-intent.json'
    if intent.exists() or intent.is_symlink() or (work/'live-profile-receipt.json').exists():raise ValueError('Preserve uncertain live profile generation')
    receipt=p.strict(secured(work/'finalized.json').read_bytes())
    keys={'version','state','root','assembly_pin','payload_manifest_sha256','policy_sha256','generated_entries_sha256','image_manifest_sha256','checks','source_sha256','production_ready','native_boot_verified'}
    if not isinstance(receipt,dict) or set(receipt)!=keys or type(receipt['version']) is not int or receipt['version']!=1 or receipt['state']!='native-finalizer-verified' or receipt['root']!=str(root) or receipt['assembly_pin']!=list(assembly.identity()) or receipt['payload_manifest_sha256']!=hashlib.sha256(p.encoded(manifest)).hexdigest() or receipt['policy_sha256']!=hashlib.sha256(p.encoded(policy)).hexdigest() or receipt['production_ready'] is not False or receipt['native_boot_verified'] is not False:raise ValueError('Live profile actual finalization receipt required')
    if set(receipt['source_sha256'])!=SOURCES or any(p.digest(secured(source_path(name)))!=expected for name,expected in receipt['source_sha256'].items()):raise ValueError('Live profile finalizer source changed')
    if set(receipt['checks'])!=p.CHECKS:raise ValueError('Live profile complete actual finalizer checks required')
    for name,binding in receipt['checks'].items():
        path=secured(binding['report']);report=p.strict(path.read_bytes())
        if binding.get('passed') is not True or binding.get('exit_status')!=0 or p.digest(path)!=binding.get('report_sha256'):raise ValueError('Live profile actual report custody')
        validate_finalizer_report(report,name,receipt)
    if p.digest(secured(generated_input))!=receipt['generated_entries_sha256']:raise ValueError('Live profile reviewed generated map changed')
    generated=p.strict(generated_input.read_bytes());before=p.PreparedPayload.audit_tree(root,manifest,generated)
    if hashlib.sha256(p.encoded(before)).hexdigest()!=receipt['image_manifest_sha256']:raise ValueError('Live profile base image changed')
    for relative in ('etc/systemd/system/getty@tty1.service.d/50-toddy-live.conf','etc/systemd/system/serial-getty@ttyS0.service.d/50-toddy-live.conf','run/toddy/live-session','run/toddy-live-owner/session.json'):
        if os.path.lexists(root/relative):raise ValueError('Live profile inherited root console/runtime authority')
    files,links,image=plan(root,manifest,media_id,receipt['policy_sha256'])
    replacement={'/etc/'+name for name in ('passwd','group','shadow','gshadow')}|{'/etc/gdm/custom.conf','/etc/pam.d/gdm-autologin','/etc/dconf/profile/user'}
    for virtual in set(files)|set(links):
        if virtual in before and virtual not in replacement:raise ValueError('Live profile would replace existing nonreviewed state')
    home=root/'home'/LIVE_USER
    if home.exists() or home.is_symlink():raise ValueError('Live home is not fresh')
    save(intent,{'version':1,'kind':'source-attributed-live-transform','base_image_manifest_sha256':receipt['image_manifest_sha256'],
        'source_sha256':p.digest(__file__),'media_id':media_id,'production_ready':False})
    for virtual,(data,mode) in files.items():regular(root,virtual.lstrip('/'),data,mode)
    home.mkdir(mode=0o700);os.chown(home,LIVE_UID,LIVE_UID)
    for virtual,target in links.items():
        path=root/virtual.lstrip('/');path.parent.mkdir(mode=0o755,parents=True,exist_ok=True)
        if path.parent.resolve()!=path.parent:raise ValueError('Live service parent redirects')
        os.symlink(target,path)
    tool=_selected(root,manifest,'/usr/bin/dconf')
    system.run(['/usr/sbin/chroot',str(root),'/usr/bin/dconf','update'],timeout=120);assembly.recheck()
    after=snapshot(root);allowed=set(files)|set(links)|{'/home/'+LIVE_USER,'/etc/dconf/db/toddy-live'}
    for path in list(allowed):
        parent=Path(path).parent
        while str(parent)!='/':allowed.add(parent.as_posix());parent=parent.parent
    changed={path for path in set(before)|set(after) if before.get(path)!=after.get(path)}
    if not changed<=allowed or any(path not in after for path in before):raise ValueError('Live native transform changed an unreviewed path')
    for virtual,(data,mode) in files.items():
        expected={'mode':stat.S_IFREG|mode,'uid':0,'gid':0,'sha256':hashlib.sha256(data).hexdigest()}
        if after.get(virtual)!=expected:raise ValueError('Live attributed file readback differs')
    if after.get('/home/'+LIVE_USER)!={'mode':stat.S_IFDIR|0o700,'uid':LIVE_UID,'gid':LIVE_UID,'directory':True}:raise ValueError('Live home attribution differs')
    database=after.get('/etc/dconf/db/toddy-live',{})
    if database.get('mode')!=stat.S_IFREG|0o644 or database.get('uid')!=0 or database.get('gid')!=0:raise ValueError('Live dconf native output differs')
    save(work/'live-image-manifest.json',after)
    result={'version':1,'state':'source-attributed-live-profile-candidate','root':str(root),'assembly_pin':list(assembly.identity()),
        'base_image_manifest_sha256':receipt['image_manifest_sha256'],'live_image_manifest_sha256':p.digest(work/'live-image-manifest.json'),
        'media_id':media_id,'image_class_sha256':p.digest(root/str(IMAGE_CLASS).lstrip('/')),'source_sha256':p.digest(__file__),
        'attributed_delta':{path:{'before':before.get(path),'after':after.get(path),'origin':'fresh-live-gnome-profile'} for path in sorted(changed)},
        'native_commands':[['/usr/bin/dconf','update']],'native_dconf_tool_sha256':p.digest(tool),
        'passwords_locked':True,'live_uid':LIVE_UID,'live_user':LIVE_USER,'wheel_membership':False,
        'native_boot_verified':False,'native_login_verified':False,'production_ready':False,
        'next':'Independent delta review, full H10 compression snapshot/journal, then actual live GDM/PAM/installer authorization and installed-image exclusion proof.'}
    save(work/'live-profile-receipt.json',result);assembly.recheck();return result
