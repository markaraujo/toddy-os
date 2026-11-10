"""First actual installed Shell on native kernel; private bus, no login claim."""
from pathlib import Path
import base64,ctypes,hashlib,json,os,re,select,signal,stat,struct,subprocess,tempfile,termios,time,zlib

REGISTERED_SESSION = False

def output(args):
 return subprocess.check_output(args,text=True,timeout=25).strip()
def main():
 assert os.geteuid()==0 and os.uname().release=='7.1.8-toddy'
 assert Path('/proc/1/comm').read_text().strip()=='systemd'
 assert output(['systemd-detect-virt','--vm']) in ['kvm','qemu']
 device=output(['findmnt','-n','-o','SOURCE','/']);assert re.fullmatch('/dev/[a-z0-9]+',device)
 parent=output(['lsblk','-ndo','PKNAME',device]);assert re.fullmatch('[a-z0-9]+',parent)
 assert output(['lsblk','-dnro','SERIAL','/dev/'+parent])=='TODDY-BOOT-TEST'
 assert output(['blkid','-s','LABEL','-o','value',device])=='TODDY_LFS'
 assert output(['findmnt','-n','-o','FSTYPE','/'])=='ext4'
 assert output(['ip','-o','link','show']).count('\n')==0
 assert output(['gnome-shell','--version'])=='GNOME Shell 50.4'
 assert output(['dpkg-query','-W','-f=${Version}','gtk'])=='4.22.4-1+toddy8'
 cache=Path('/usr/share/glib-2.0/schemas/gschemas.compiled')
 cache_sha=hashlib.sha256(cache.read_bytes()).hexdigest()
 assert cache_sha=='824567b089fb951595e4d961162d8f59406a7f70d7b86b9b01de93515bb42a2f'
 subprocess.run(['systemctl','start','dbus.service','systemd-logind.service'],check=True,timeout=30)
 uid=101;session=None;client=None;wrapper=None;user=None
 if REGISTERED_SESSION:
  uid=12401;user='toddy-shell-probe';home=Path('/home')/user
  assert not home.exists() and not any(r.split(':')[0]==user or r.split(':')[2]==str(uid) for r in Path('/etc/passwd').read_text().splitlines())
  fixture=Path('/sources/phase2/native-fixtures/login-policy-1');accepted=json.loads((fixture/'accepted.json').read_text())
  assert hashlib.sha256((fixture/'accepted.json').read_bytes()).hexdigest()=='e465ac100db9eb3a8d47371b4425a087a365d586eb205e988acad17976689166'
  for name,sha in accepted['artifacts'].items():assert hashlib.sha256((fixture/name).read_bytes()).hexdigest()==sha
  for name,sha in accepted['installed_artifacts'].items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==sha
  subprocess.run(['useradd','-m','-U','-u',str(uid),'-s','/bin/bash',user],check=True,capture_output=True,timeout=20)
  wrapper=Path('/etc/pam.d/toddy-session');assert not wrapper.exists()
  wrapper.write_text('auth include system-auth\naccount include system-account\npassword include system-password\nsession include system-session\n')
  client=subprocess.Popen([str(fixture/'session-consumer'),'/etc/pam.d',user],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8'})
  assert select.select([client.stdout],[],[],25)[0],'Actual PAM session ready missing'
  session=json.loads(client.stdout.readline());assert session['phase']=='ready' and session['session_id']
  actual=dict(line.split('=',1) for line in output(['loginctl','show-session',session['session_id'],'-p','User','-p','Name','-p','State','-p','Type','-p','Service']).splitlines())
  assert actual['User']==str(uid) and actual['Name']==user and actual['State'] in ['active','online']
  deadline=time.monotonic()+25
  while not Path('/run/user',str(uid),'bus').is_socket():
   assert time.monotonic()<deadline;time.sleep(.05)
  assert output(['systemctl','is-active','user@'+str(uid)+'.service'])=='active'
  session['actual_logind']=actual
 report={'scope':'First actual native Shell headless Wayland/software rendering with supported automation, private user bus and real GTK perf-helper window. No GDM/authenticated GNOME session/basic apps/physical acceptance. No unsafe-mode or installed preference change.','kernel':os.uname().release,'pid1':'systemd','uid':uid,'registered_ephemeral_session':session,'stock_schema_cache_sha256':cache_sha,'all_selected_exits_zero':False}
 with tempfile.TemporaryDirectory(prefix='toddy-native-shell-') as directory:
  root=Path(directory);os.chown(root,uid,uid)
  if REGISTERED_SESSION:runtime=Path('/run/user')/str(uid)
  else:
   runtime=root/'runtime';runtime.mkdir(mode=0o700);os.chown(runtime,uid,uid)
  assert runtime.stat().st_uid==uid and stat.S_IMODE(runtime.stat().st_mode)==0o700
  script=root/'automation.js';script.write_text(AUTOMATION);script.chmod(0o644)
  env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':str(root),'XDG_RUNTIME_DIR':str(runtime),'XDG_CACHE_HOME':str(root/'cache'),'XDG_CONFIG_HOME':str(root/'config'),'XDG_DATA_HOME':str(root/'data'),'XDG_SESSION_TYPE':'wayland','XDG_CURRENT_DESKTOP':'GNOME','LIBGL_ALWAYS_SOFTWARE':'1','GALLIUM_DRIVER':'llvmpipe','GDK_DISABLE':'vulkan','GSETTINGS_BACKEND':'memory','TODDY_NATIVE_OUTPUT':str(root),'PYTHONDONTWRITEBYTECODE':'1'}
  def nnp():
   assert os.geteuid()==uid and ctypes.CDLL(None,use_errno=True).prctl(38,1,0,0,0)==0
  args=['dbus-run-session','--','gnome-shell','--wayland','--headless','--virtual-monitor=1280x720','--wayland-display=toddy-shell-proof','--automation-script='+str(script)]
  if REGISTERED_SESSION:
   env.update(USER=user,LOGNAME=user,XDG_SESSION_ID=session['session_id'],DBUS_SESSION_BUS_ADDRESS='unix:path='+str(runtime/'bus'))
   args=args[2:]
  started=time.monotonic()
  with (root/'shell.log').open('wb') as log:
   process=subprocess.Popen(args,env=env,cwd=root,user=uid,group=uid,extra_groups=[],preexec_fn=nnp,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
   try:code=process.wait(timeout=150)
   except subprocess.TimeoutExpired:
    os.killpg(process.pid,signal.SIGTERM)
    try:process.wait(timeout=10)
    except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=10)
    code=None;report['observation_timeout_seconds']=150
  report.update(shell_exit=code,elapsed_seconds=round(time.monotonic()-started,3),command=args,shell_log=(root/'shell.log').read_text(errors='replace')[-100000:])
  result=root/'actions.json';report['actions']=json.loads(result.read_text()) if result.exists() else None
  report['startup_state']=json.loads((root/'startup-state.json').read_text()) if (root/'startup-state.json').exists() else None
  images=[]
  for p in sorted(root.glob('*.png')):
   data=p.read_bytes();assert data.startswith(b'\x89PNG\r\n\x1a\n') and len(data)<=1024**2
   width,height=struct.unpack('>II',data[16:24]);assert (width,height)==(1280,720)
   images.append({'name':p.name,'width':width,'height':height,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'png_base64':base64.b64encode(data).decode()})
  report['native_client_images']=images
  report['all_selected_exits_zero']=code==0 and report['actions'] is not None and report['actions'].get('passed') is True and len([i for i in images if i['name'].startswith(('01-','02-','03-','04-'))])==4
 if REGISTERED_SESSION:
  closed,err=client.communicate('\n',timeout=25);assert client.returncode==0
  session['closed']=json.loads(closed.strip());assert session['closed']=={'phase':'closed','close':0,'end':0}
  subprocess.run(['loginctl','terminate-user',str(uid)],check=True,capture_output=True,timeout=25)
  deadline=time.monotonic()+20
  while Path('/run/user',str(uid)).exists():
   assert time.monotonic()<deadline;time.sleep(.05)
  subprocess.run(['userdel','-r',user],check=True,capture_output=True,timeout=20);wrapper.unlink()
  assert not home.exists();report['ephemeral_PAM_user_and_runtime_removed']=True
 assert hashlib.sha256(cache.read_bytes()).hexdigest()==cache_sha
 raw=json.dumps(report,sort_keys=True).encode();assert len(raw)<4*1024**2
 encoded=base64.b64encode(zlib.compress(raw,9)).decode();chunks=[encoded[i:i+1024] for i in range(0,len(encoded),1024)]
 # Dedicated second virtual UART: kernel/getty/journal console cannot mix into
 # this evidence stream. Original chunk/full-report SHA verification is unchanged.
 fd=os.open('/dev/ttyS1',os.O_WRONLY|os.O_NOCTTY)
 attrs=termios.tcgetattr(fd);attrs[0]=attrs[1]=attrs[3]=0
 attrs[2]|=termios.CLOCAL|termios.CREAD;attrs[4]=attrs[5]=termios.B115200
 termios.tcsetattr(fd,termios.TCSANOW,attrs)
 with os.fdopen(fd,'w',buffering=1) as evidence:
  for i,chunk in enumerate(chunks):print('TODDY_B02_RUNTIME_DATA',i,chunk,file=evidence,flush=True)
  print('TODDY_B02_RUNTIME_RESULT',json.dumps({'kernel':os.uname().release,'all_selected_exits_zero':report['all_selected_exits_zero'],'report_sha256':hashlib.sha256(raw).hexdigest(),'chunks':len(chunks)}),file=evidence,flush=True)
  termios.tcdrain(evidence.fileno())
 print('TODDY_B02_RUNTIME_EVIDENCE_WRITTEN',hashlib.sha256(raw).hexdigest(),flush=True)
 if not report['all_selected_exits_zero']:raise AssertionError('Actual native Shell gate failed; retained exact report')

AUTOMATION=r'''
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import Shell from 'gi://Shell';
import St from 'gi://St';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import * as Scripting from 'resource:///org/gnome/shell/ui/scripting.js';
export const METRICS = {};
const root = GLib.getenv('TODDY_NATIVE_OUTPUT');
const actions = [];
const startupSamples = [];
let automationStartPath = 'startup-complete-handler';
function check(value, name) {
    actions.push({name, passed: Boolean(value)});
    if (!value) throw new Error(name);
}
async function capture(name) {
    const stream = Gio.File.new_for_path(`${root}/${name}.png`).replace(null, false, Gio.FileCreateFlags.NONE, null);
    const shot = new Shell.Screenshot();
    await new Promise((resolve, reject) => {
        shot.screenshot(false, stream, (object, result) => {
            try { object.screenshot_finish(result); resolve(); } catch (e) { reject(e); }
        });
    });
    stream.close(null);
}
export function init() {
    function record() {
        const state = {monitors: Main.layoutManager.monitors.length,
            primaryIndex: Main.layoutManager.primaryIndex,
            startingUp: Main.layoutManager._startingUp,
            panelWidth: Main.panel.width, panelHeight: Main.panel.height,
            stageWidth: global.stage.width, stageHeight: global.stage.height,
            overviewVisible: Main.overview.visible, actions: actions.length};
        startupSamples.push({...state, monotonicUs: GLib.get_monotonic_time()});
        GLib.file_set_contents(`${root}/startup-state.json`, JSON.stringify({state, startupSamples, automationStartPath}));
    }
    if (!Main.layoutManager._startingUp) {
        // Main awaits importing the automation module before connecting its
        // startup-complete handler. Fast no-animation startup may finish first.
        // Use the same upstream runner once only when that signal is already past.
        automationStartPath = 'late-automation-hook-after-startup';
        GLib.idle_add_once(GLib.PRIORITY_DEFAULT, () => {
            Scripting.runPerfScript({run, METRICS}, null);
        });
    }
    record();
    GLib.timeout_add_once(GLib.PRIORITY_DEFAULT, 5000, () => {
        record();
        capture('00-diagnostic').catch(error => console.error(String(error)));
    });
    GLib.timeout_add_once(GLib.PRIORITY_DEFAULT, 45000, record);
}
export async function run() {
    try {
        await Scripting.sleep(1000);
        Main.overview.hide();
        await Scripting.sleep(600);
        check(Main.panel.width > 0 && Main.layoutManager.monitors.length === 1, 'native-panel-and-monitor');
        await capture('01-desktop');
        Main.overview.show();
        await Scripting.sleep(600);
        check(Main.overview.visible, 'overview-open');
        await capture('02-overview');
        Main.overview.hide();
        await Scripting.sleep(600);
        check(!Main.overview.visible, 'overview-close');
        Main.panel.statusArea.quickSettings.menu.open();
        await Scripting.sleep(600);
        check(Main.panel.statusArea.quickSettings.menu.isOpen, 'quick-settings-open');
        check(Main.panel.navigate_focus(null, St.DirectionType.TAB_FORWARD, false), 'native-panel-keyboard-focus');
        await capture('03-quick-settings');
        Main.panel.statusArea.quickSettings.menu.close();
        await Scripting.createTestWindow({width: 640, height: 400, textInput: true});
        await Scripting.waitTestWindows();
        await Scripting.sleep(600);
        const windows = global.get_window_actors();
        check(windows.length > 0, 'actual-GTK-window-mapped');
        const window = windows[0].meta_window;
        window.activate(global.get_current_time());
        await Scripting.sleep(600);
        check(global.display.focus_window === window, 'actual-GTK-window-focused');
        await capture('04-gtk-window');
        await Scripting.destroyTestWindows();
        await Scripting.sleep(600);
        check(global.get_window_actors().length === 0, 'window-close-recovery');
        GLib.file_set_contents(`${root}/actions.json`, JSON.stringify({passed: true, actions}));
    } catch (error) {
        GLib.file_set_contents(`${root}/actions.json`, JSON.stringify({passed: false, actions, error: String(error)}));
        throw error;
    }
}
'''
if __name__=='__main__':
 try:main()
 except Exception as error:
  print('TODDY_B02_RUNTIME_FAIL',type(error).__name__,str(error),flush=True)
  raise
