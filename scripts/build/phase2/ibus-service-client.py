"""Actual installed IBus engine IPC with private data, no graphical claim."""
from pathlib import Path
import json,os,subprocess,sys,time
import gi
gi.require_version('IBus','1.0');gi.require_version('Gio','2.0')
from gi.repository import IBus,Gio,GLib
mode,profile=sys.argv[1:];IBus.init();main=GLib.MainContext.default()
def until(predicate,seconds=8):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  while main.pending():main.iteration(False)
  if predicate():return
  time.sleep(.02)
 raise AssertionError('Bounded IBus postcondition not reached')
assert os.getuid()==101
log=Path(profile)/(mode+'-daemon.log')
with log.open('x') as output:
 daemon=subprocess.Popen(['ibus-daemon','--cache=none','--panel=disable','--config=/usr/libexec/ibus-memconf','--emoji-extension=disable'],stdout=output,stderr=subprocess.STDOUT)
 try:
  until(lambda: bool(IBus.get_address()))
  bus=IBus.Bus.new();until(bus.is_connected)
  engines=bus.list_engines();names={e.get_name() for e in engines};assert 'xkb:us::eng' in names
  cancelled=Gio.Cancellable.new();cancelled.cancel();outcome={}
  def finished(obj,res,_):
   try:obj.list_engines_async_finish(res);outcome['unexpected_success']=True
   except GLib.Error as e:outcome['cancelled']=e.matches(Gio.io_error_quark(),Gio.IOErrorEnum.CANCELLED)
  bus.list_engines_async(2000,cancelled,finished,None)
  until(lambda:bool(outcome));assert outcome=={'cancelled':True}
  assert {e.get_name() for e in bus.list_engines()}==names
  context=bus.create_input_context('toddy-native-ibus-'+mode);assert context
  commits=[];context.connect('commit-text',lambda _,text:commits.append(text.get_text()))
  context.set_capabilities(IBus.Capabilite.PREEDIT_TEXT|IBus.Capabilite.FOCUS)
  context.focus_in();assert bus.set_global_engine('xkb:us::eng')
  until(lambda: context.get_engine() is not None and context.get_engine().get_name()=='xkb:us::eng')
  # Default upstream simple engine leaves optional Ctrl+Shift+U disabled.
  assert 'IBUS_ENABLE_CTRL_SHIFT_U' not in os.environ and 'IBUS_ENABLE_CONTROL_SHIFT_U' not in os.environ
  assert not context.process_key_event(IBus.KEY_U,0,IBus.ModifierType.CONTROL_MASK|IBus.ModifierType.SHIFT_MASK)
  for key,mods in [(IBus.KEY_dead_tilde,0),(IBus.KEY_a,0)]:
   assert context.process_key_event(key,0,mods)
   while main.pending():main.iteration(False)
  until(lambda:bool(commits));assert commits==['ã'],commits
  context.focus_out();context.destroy()
  session=Gio.bus_get_sync(Gio.BusType.SESSION,None)
  result={'mode':mode,'bus_guid':session.get_guid(),'IBus_address':IBus.get_address(),'actual_installed_engine_commit':commits,'precancelled_read_refused':True,'post_cancel_engine_read_recovered':True,'default_dead_key_Compose':True,'optional_hex_hotkey_not_handled':True,'engine':'xkb:us::eng','engine_count':len(names),'daemon_pid':daemon.pid,'graphical_keyboard_tested':False}
  bus.exit(False);assert daemon.wait(timeout=8)==0;result['requested_Stop_exit']=0
  print(json.dumps(result))
 finally:
  if daemon.poll() is None:daemon.terminate();daemon.wait(timeout=8)
