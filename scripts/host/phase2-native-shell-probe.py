"""First actual installed Shell on native kernel; private bus, no login claim."""
from pathlib import Path
import base64,ctypes,hashlib,json,os,re,signal,struct,subprocess,tempfile,time,zlib

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
 report={'scope':'First actual native Shell headless Wayland/software rendering with supported automation, private user bus and real GTK perf-helper window. No GDM/authenticated GNOME session/basic apps/physical acceptance. No unsafe-mode or installed preference change.','kernel':os.uname().release,'pid1':'systemd','uid':101,'stock_schema_cache_sha256':cache_sha,'all_selected_exits_zero':False}
 with tempfile.TemporaryDirectory(prefix='toddy-native-shell-') as directory:
  root=Path(directory);os.chown(root,101,101)
  runtime=root/'runtime';runtime.mkdir(mode=0o700);os.chown(runtime,101,101)
  script=root/'automation.js';script.write_text(AUTOMATION);script.chmod(0o644)
  env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':str(root),'XDG_RUNTIME_DIR':str(runtime),'XDG_CACHE_HOME':str(root/'cache'),'XDG_CONFIG_HOME':str(root/'config'),'XDG_DATA_HOME':str(root/'data'),'XDG_SESSION_TYPE':'wayland','XDG_CURRENT_DESKTOP':'GNOME','LIBGL_ALWAYS_SOFTWARE':'1','GALLIUM_DRIVER':'llvmpipe','GDK_DISABLE':'vulkan','GSETTINGS_BACKEND':'memory','TODDY_NATIVE_OUTPUT':str(root),'PYTHONDONTWRITEBYTECODE':'1'}
  def nnp():
   assert os.geteuid()==101 and ctypes.CDLL(None,use_errno=True).prctl(38,1,0,0,0)==0
  args=['dbus-run-session','--','gnome-shell','--wayland','--headless','--virtual-monitor=1280x720','--wayland-display=toddy-shell-proof','--automation-script='+str(script)]
  started=time.monotonic()
  with (root/'shell.log').open('wb') as log:
   process=subprocess.Popen(args,env=env,cwd=root,user=101,group=101,extra_groups=[],preexec_fn=nnp,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
   try:code=process.wait(timeout=150)
   except subprocess.TimeoutExpired:
    os.killpg(process.pid,signal.SIGTERM)
    try:process.wait(timeout=10)
    except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=10)
    code=None;report['observation_timeout_seconds']=150
  report.update(shell_exit=code,elapsed_seconds=round(time.monotonic()-started,3),command=args,shell_log=(root/'shell.log').read_text(errors='replace')[-100000:])
  result=root/'actions.json';report['actions']=json.loads(result.read_text()) if result.exists() else None
  images=[]
  for p in sorted(root.glob('*.png')):
   data=p.read_bytes();assert data.startswith(b'\x89PNG\r\n\x1a\n') and len(data)<=1024**2
   width,height=struct.unpack('>II',data[16:24]);assert (width,height)==(1280,720)
   images.append({'name':p.name,'width':width,'height':height,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'png_base64':base64.b64encode(data).decode()})
  report['native_client_images']=images
  report['all_selected_exits_zero']=code==0 and report['actions'] is not None and report['actions'].get('passed') is True and len(images)==4
 assert hashlib.sha256(cache.read_bytes()).hexdigest()==cache_sha
 raw=json.dumps(report,sort_keys=True).encode();assert len(raw)<4*1024**2
 encoded=base64.b64encode(zlib.compress(raw,9)).decode();chunks=[encoded[i:i+1024] for i in range(0,len(encoded),1024)]
 for i,chunk in enumerate(chunks):print('TODDY_B02_RUNTIME_DATA',i,chunk,flush=True)
 print('TODDY_B02_RUNTIME_RESULT',json.dumps({'kernel':os.uname().release,'all_selected_exits_zero':report['all_selected_exits_zero'],'report_sha256':hashlib.sha256(raw).hexdigest(),'chunks':len(chunks)}),flush=True)
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
