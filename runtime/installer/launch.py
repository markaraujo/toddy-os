"""Fixed authenticated live-only Wayland launch; no user environment passthrough."""
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import socket
import struct
import stat
import sys
from .composition import secured
from .disk_plan import InstallError

CALAMARES='/usr/bin/calamares'
MODULE='/usr/lib/calamares/modules/toddy/libcalamares_viewmodule_toddy.so'
PLATFORM='/usr/plugins/platforms/libqwayland.so'
SHELL='/usr/plugins/wayland-shell-integration/libxdg-shell.so'
CONFIG='/usr/share/toddy/installer/calamares'
QUALIFICATION_CONFIG='/usr/share/toddy/installer/calamares-qualification'
RECEIPT='/usr/share/toddy/installer/launch-qualification.json'
OBSERVED={'root_gui','native_wayland','active_local_owner','no_session_bus_inherited','en_visible','pt_visible',
          'keyboard_focus','scale_100','scale_200','cancel_before_write'}


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def session_properties(uid):
    import gi
    gi.require_version('Gio','2.0')
    from gi.repository import Gio,GLib
    connection=Gio.bus_get_sync(Gio.BusType.SYSTEM,None)
    def call(path,interface,method,parameters,reply):
        return connection.call_sync('org.freedesktop.login1',path,interface,method,parameters,
            GLib.VariantType(reply),Gio.DBusCallFlags.NO_AUTO_START,3000,None).unpack()
    user=call('/org/freedesktop/login1','org.freedesktop.login1.Manager','GetUser',GLib.Variant('(u)',(uid,)),'(o)')[0]
    props=call(user,'org.freedesktop.DBus.Properties','GetAll',GLib.Variant('(s)',('org.freedesktop.login1.User',)),'(a{sv})')[0]
    display=props.get('Display')
    if not isinstance(display,(tuple,list)) or len(display)!=2 or not display[0] or not display[1].startswith('/org/freedesktop/login1/session/'):
        raise InstallError('installer_active_wayland_owner_required')
    return call(display[1],'org.freedesktop.DBus.Properties','GetAll',GLib.Variant('(s)',('org.freedesktop.login1.Session',)),'(a{sv})')[0]


def validate_session(uid,properties):
    if type(uid) is not int or not 1000<=uid<=60000 or not isinstance(properties,dict) or \
            not isinstance(properties.get('User'),(tuple,list)) or len(properties['User'])!=2 or type(properties['User'][0]) is not int or properties['User'][0]!=uid or \
            properties.get('Active') is not True or properties.get('Remote') is not False or properties.get('LockedHint') is not False or \
            properties.get('Type')!='wayland' or properties.get('Class')!='user' or properties.get('State')!='active':
        raise InstallError('installer_active_wayland_owner_required')


def validate_socket(uid,name):
    if not isinstance(name,str) or not re.fullmatch('wayland-[0-9]{1,4}',name):raise InstallError('installer_wayland_socket')
    directory=Path('/run/user')/str(uid);path=directory/name
    info=directory.lstat();metadata=path.lstat()
    if directory.resolve()!=directory or not stat.S_ISDIR(info.st_mode) or info.st_uid!=uid or stat.S_IMODE(info.st_mode)!=0o700 or \
            path.is_symlink() or not stat.S_ISSOCK(metadata.st_mode) or metadata.st_uid!=uid:
        raise InstallError('installer_wayland_socket')
    return directory,path


def verify_peer(path,uid):
    # A metadata-only socket check is insufficient. Query actual kernel peer
    # credentials without sending Wayland requests or inherited session data.
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM|socket.SOCK_CLOEXEC) as connection:
        connection.settimeout(2);connection.connect(str(path))
        _pid,peer_uid,_gid=struct.unpack('3i',connection.getsockopt(socket.SOL_SOCKET,socket.SO_PEERCRED,12))
        if peer_uid!=uid:raise InstallError('installer_wayland_peer_identity')


def launch_receipt():
    from ..shared.json import strict_json
    path=secured(RECEIPT,131072);value=strict_json(path.read_bytes())
    expected={'kind','calamares_version','qt_version','module_sha256','launch_source_sha256','platform_sha256','shell_integration_sha256','calamares_sha256','config_sha256','strings_sha256','observed','boot_id'}
    if not isinstance(value,dict) or set(value)!=expected or value['kind']!='native-calamares-wayland-v1' or value['calamares_version']!='3.4.3' or value['qt_version']!='6.11.2' or \
            not isinstance(value['observed'],dict) or set(value['observed'])!=OBSERVED or any(item is not True for item in value['observed'].values()) or \
            not isinstance(value['boot_id'],str) or not re.fullmatch('[a-f0-9-]{36}',value['boot_id']):raise InstallError('installer_root_wayland_not_qualified')
    for field,source in (('calamares_sha256',CALAMARES),('config_sha256',CONFIG+'/settings.conf'),('strings_sha256','/usr/share/calamares/modules/toddy/strings.json'),('module_sha256',MODULE),('launch_source_sha256',__file__),('platform_sha256',PLATFORM),('shell_integration_sha256',SHELL)):
        if value[field]!=digest(secured(source)):raise InstallError('installer_launch_qualified_bytes_changed')
    return value


def environment(uid,display,locale='en_US.UTF-8'):
    if locale not in ('en_US.UTF-8','pt_BR.UTF-8'):raise InstallError('installer_launch_locale')
    validate_session(uid,session_properties(uid));directory,path=validate_socket(uid,display);verify_peer(path,uid)
    for source in (CALAMARES,MODULE,PLATFORM,SHELL):secured(source)
    base=Path('/run/toddy-installer');base.mkdir(mode=0o700,exist_ok=True)
    info=base.lstat()
    if base.resolve()!=base or info.st_uid!=0 or info.st_gid!=0 or stat.S_IMODE(info.st_mode)!=0o700:raise InstallError('installer_private_runtime')
    home=base/('gui-'+os.urandom(12).hex());home.mkdir(mode=0o700)
    return clean_environment(directory,home,display,locale)


def clean_environment(directory,home,display,locale):
    if locale not in ('en_US.UTF-8','pt_BR.UTF-8') or not re.fullmatch('wayland-[0-9]{1,4}',display):raise InstallError('installer_launch_environment')
    return {'PATH':'/usr/bin:/usr/sbin','HOME':str(home),'LANG':locale,'LC_ALL':locale,
            'XDG_RUNTIME_DIR':str(directory),'WAYLAND_DISPLAY':display,'QT_QPA_PLATFORM':'wayland',
            'QT_PLUGIN_PATH':'/usr/plugins','QT_QPA_PLATFORM_PLUGIN_PATH':'/usr/plugins/platforms',
            'XDG_CONFIG_HOME':str(home/'config'),'XDG_CACHE_HOME':str(home/'cache'),'XDG_DATA_HOME':str(home/'data')}


def qualification_command(uid,display,locale='en_US.UTF-8'):
    """Coordinator-only source harness: real root GUI with show-only fixed config.

    This function is not exposed by the installed Polkit entry and never returns
    the production config or an execution job. Real/effective UID0 remains required;
    no upstream test/debug bypass is used.
    """
    if os.getuid()!=0 or os.geteuid()!=0:raise InstallError('installer_root_required')
    resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.umask(0o077)
    secured(QUALIFICATION_CONFIG+'/settings.conf')
    return [CALAMARES,'-c',QUALIFICATION_CONFIG],environment(uid,display,locale)


def main():
    from ..shared.json import strict_json
    try:
        if os.getuid()!=0 or os.geteuid()!=0 or sys.argv[1:]:raise InstallError('installer_root_required')
        resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.umask(0o077)
        raw=os.environ.get('PKEXEC_UID','')
        if not re.fullmatch('[0-9]{1,5}',raw):raise InstallError('installer_native_owner_authorization_required')
        uid=int(raw);data=sys.stdin.buffer.read(4097)
        if len(data)>4096:raise InstallError('installer_launch_request_limit')
        request=strict_json(data)
        if not isinstance(request,dict) or set(request)!={'version','display','locale'} or type(request['version']) is not int or request['version']!=1:
            raise InstallError('installer_launch_request')
        from .live_session import authorize_live_owner
        authorize_live_owner(uid)
        launch_receipt()
        from .live_bindings import create
        create().readiness()
        env=environment(uid,request['display'],request['locale']);secured(CONFIG+'/settings.conf')
        os.execve(CALAMARES,[CALAMARES,'-c',CONFIG],env)
    except Exception:
        # No paths, request contents, tokens or caller environment in the error.
        raise SystemExit('Toddy installer unavailable: native composition/display qualification required.') from None

if __name__=='__main__':main()
