"""Source-only owner preference persistence measurement and companion validation."""
import hashlib,json,os,re,socket,stat,subprocess
from pathlib import Path

SCHEMA='org.gnome.desktop.interface'
KEY='clock-show-seconds'


def owner_marker(plan_sha):
    return (json.dumps({'version':1,'plan_sha256':plan_sha,'owner_setting':{'schema':SCHEMA,'key':KEY,'value':True}},sort_keys=True,separators=(',',':'))+'\n').encode()


OWNER_CHILD=r'''
import hashlib,json,os,re,stat,sys
from pathlib import Path
import gi
gi.require_version('Gio','2.0')
from gi.repository import Gio
value=json.loads(sys.stdin.buffer.read(65537))
assert set(value)=={'uid','gid','home','operation_id','plan_sha256','round','recovery'}
assert os.getuid()==os.geteuid()==value['uid'] and os.getgid()==os.getegid()==value['gid']
assert re.fullmatch('[a-f0-9]{32}',value['operation_id']) and re.fullmatch('[a-f0-9]{64}',value['plan_sha256'])
assert not os.getgroups() and type(value['round']) is int and value['round'] in (1,2,3) and value['recovery'] is (value['round']==3)
home=Path(value['home']);assert home.resolve()==home and os.environ['HOME']==str(home)
assert os.environ['XDG_CONFIG_HOME']==str(home/'.config') and os.environ['GSETTINGS_BACKEND']=='dconf'
assert (home/'.config/dconf/user').resolve()==home/'.config/dconf/user'
for directory in (home,home/'.config',home/'.config/dconf'):
    if directory.exists():
        metadata=directory.lstat();assert stat.S_ISDIR(metadata.st_mode) and metadata.st_uid==value['uid'] and not metadata.st_mode&0o022
settings=Gio.Settings.new('org.gnome.desktop.interface');key='clock-show-seconds'
initial_value=settings.get_boolean(key);initial_variant=settings.get_user_value(key)
initial_user_value=None if initial_variant is None else initial_variant.unpack()
if value['round']==1:
    assert initial_value is False and initial_user_value in (None,False)
    assert settings.is_writable(key) and settings.set_boolean(key,True)
    Gio.Settings.sync()
actual=settings.get_boolean(key);variant=settings.get_user_value(key)
assert actual is True and variant is not None and variant.get_type_string()=='b' and variant.unpack() is True
path=home/'.config/dconf/user';assert path.resolve()==path
info=path.lstat();assert stat.S_ISREG(info.st_mode) and info.st_uid==value['uid'] and info.st_nlink==1 and not info.st_mode&0o022 and stat.S_IMODE(info.st_mode)&0o400
fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
try:
    if value['round']==1:os.fsync(fd)
    with os.fdopen(os.dup(fd),'rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
finally:os.close(fd)
setting={'schema':'org.gnome.desktop.interface','key':key,'value':actual,'user_value':variant.unpack(),'variant_type':variant.get_type_string(),
    'initial_value':initial_value,'initial_user_value':initial_user_value,'backend':'dconf','uid':os.getuid(),'gid':os.getgid(),'home':str(home),
    'operation':'set-sync-read' if value['round']==1 else 'read-only',
    'session_bus':'native-owner-session' if os.environ['DBUS_SESSION_BUS_ADDRESS'].startswith('unix:path=/run/user/') else 'offline-read',
    'database':{'path':str(path),'sha256':digest,'bytes':info.st_size,'mode':stat.S_IMODE(info.st_mode),'uid':info.st_uid,'gid':info.st_gid,'nlink':info.st_nlink}}
content=(json.dumps({'version':1,'plan_sha256':value['plan_sha256'],'owner_setting':{'schema':'org.gnome.desktop.interface','key':key,'value':actual}},sort_keys=True,separators=(',',':'))+'\n').encode()
marker=home/('.toddy-install-proof-'+value['operation_id'])
if value['round']==1:
    fd=os.open(marker,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as stream:stream.write(content);stream.flush();os.fsync(stream.fileno())
    fd=os.open(home,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)
info=marker.lstat();assert (info.st_mode,info.st_uid,info.st_gid,info.st_nlink)==(stat.S_IFREG|0o600,value['uid'],value['gid'],1)
assert marker.read_bytes()==content
print(json.dumps({'marker_sha256':hashlib.sha256(content).hexdigest(),'setting':setting},sort_keys=True,separators=(',',':')))
'''


def run_owner_state(account,plan,round_number,recovery):
    """Native fork/exec credential drop, no Python preexec or root preferences."""
    home=Path(account.pw_dir);runtime=Path('/run/user')/str(account.pw_uid);bus=runtime/'bus'
    available=bus.exists()
    if available:
        info=bus.lstat();directory=runtime.lstat()
        if runtime.resolve()!=runtime or directory.st_uid!=account.pw_uid or stat.S_IMODE(directory.st_mode)!=0o700 or not stat.S_ISSOCK(info.st_mode) or info.st_uid!=account.pw_uid:raise ValueError('actual_owner_session_bus_required')
    elif not recovery:raise ValueError('actual_graphical_owner_session_bus_required')
    environment={'PATH':'/usr/bin:/usr/sbin','HOME':str(home),'LANG':'C.UTF-8','LC_ALL':'C.UTF-8',
        'XDG_CONFIG_HOME':str(home/'.config'),'XDG_DATA_HOME':str(home/'.local/share'),
        'XDG_RUNTIME_DIR':str(runtime),'DBUS_SESSION_BUS_ADDRESS':'unix:path='+str(bus) if available else 'unix:path=/run/toddy-no-owner-session-bus',
        'GSETTINGS_BACKEND':'dconf','DCONF_PROFILE':'user','PYTHONDONTWRITEBYTECODE':'1'}
    request={'uid':account.pw_uid,'gid':account.pw_gid,'home':str(home),'operation_id':plan['operation_id'],
        'plan_sha256':plan['plan_sha256'],'round':round_number,'recovery':recovery}
    result=subprocess.run(['/usr/bin/python3','-I','-c',OWNER_CHILD],input=json.dumps(request).encode(),stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
        user=account.pw_uid,group=account.pw_gid,extra_groups=(),umask=0o077,env=environment,close_fds=True,timeout=30,check=True)
    if len(result.stdout)>65536:raise ValueError('owner_setting_measurement_bound')
    return json.loads(result.stdout)


def validate_setting(value,owner,number):
    fields={'schema','key','value','user_value','variant_type','initial_value','initial_user_value','backend','uid','gid','home','operation','session_bus','database'}
    if not isinstance(value,dict) or set(value)!=fields or value['schema']!=SCHEMA or value['key']!=KEY or value['value'] is not True or value['user_value'] is not True or value['variant_type']!='b' or value['backend']!='dconf' or value['uid']!=owner['uid'] or value['gid']!=owner['gid'] or value['home']!='/home/'+owner['username'] or value['operation']!=('set-sync-read' if number==1 else 'read-only') or value['session_bus'] not in (('native-owner-session','offline-read') if number==3 else ('native-owner-session',)):
        raise ValueError('actual_owner_setting_readback_required')
    if number==1 and (value['initial_value'] is not False or (value['initial_user_value'] is not None and value['initial_user_value'] is not False)) or number!=1 and (value['initial_value'] is not True or value['initial_user_value'] is not True):raise ValueError('actual_representative_setting_change_and_retained_value_required')
    if any(type(value[key]) is not int for key in ('uid','gid')):raise ValueError('actual_numeric_owner_identity_required')
    database=value['database']
    if not isinstance(database,dict) or set(database)!={'path','sha256','bytes','mode','uid','gid','nlink'} or any(type(database[key]) is not int for key in ('bytes','mode','uid','gid','nlink')) or database['path']!=value['home']+'/.config/dconf/user' or database['mode']&~0o777 or database['mode']&0o022 or not database['mode']&0o400 or database['uid']!=owner['uid'] or database['nlink']!=1 or not 0<=database['gid']<2**31 or not isinstance(database['sha256'],str) or not re.fullmatch('[a-f0-9]{64}',database['sha256']) or type(database['bytes']) is not int or database['bytes']<=0:raise ValueError('actual_protected_owner_dconf_database_required')
    return value


def validate_companion(value,boot_report,boot_sha,*,iso_sha256=None):
    fields={'version','kind','firmware','boot_receipt_sha256','source','expected_owner','plan_sha256','rounds'}
    if not isinstance(value,dict) or set(value)!=fields or type(value['version']) is not int or value['version']!=1 or value['kind']!='native-owner-setting-persistence-v1' or value['firmware']!=boot_report['firmware'] or value['boot_receipt_sha256']!=boot_sha or not re.fullmatch('[a-f0-9]{64}',value.get('plan_sha256','')):raise ValueError('actual_bound_owner_settings_companion_required')
    source=value['source'];required={'iso_sha256','live_inputs_sha256','live_controller_sha256','cold_sha256','disk_sha256','handoff_sha256','owner_boot_inputs_sha256','observer_sha256','setting_helper_sha256'}
    if not isinstance(source,dict) or set(source)!=required or any(not isinstance(source[key],str) or not re.fullmatch('[a-f0-9]{64}',source[key]) for key in required) or source['setting_helper_sha256']!=hashlib.sha256(Path(__file__).read_bytes()).hexdigest() or iso_sha256 is not None and source['iso_sha256']!=iso_sha256:raise ValueError('actual_owner_setting_source_iso_binding_required')
    owner=value['expected_owner']
    if not isinstance(owner,dict) or set(owner)!={'username','uid','gid'} or not isinstance(owner['username'],str) or not re.fullmatch('[a-z][a-z0-9_-]{0,31}',owner['username']) or owner['username'] in ('root','lfs','tester','builder','toddy','toddy-live') or any(type(owner[key]) is not int or not 1000<=owner[key]<=60000 for key in ('uid','gid')):raise ValueError('actual_settings_owner_required')
    if not isinstance(value['rounds'],list) or len(value['rounds'])!=2:raise ValueError('two_actual_owner_setting_boots_required')
    marker=hashlib.sha256(owner_marker(value['plan_sha256'])).hexdigest()
    for number,(row,boot) in enumerate(zip(value['rounds'],boot_report['boots']),1):
        if not isinstance(row,dict) or set(row)!={'round','boot_id','root_uuid','persistent_marker_sha256','setting'} or row['round']!=number or any(row[key]!=boot[key] for key in ('boot_id','root_uuid','persistent_marker_sha256')) or row['persistent_marker_sha256']!=marker:raise ValueError('owner_setting_same_boot_file_binding_required')
        validate_setting(row['setting'],owner,number)
    return value
