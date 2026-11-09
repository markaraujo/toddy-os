"""Compile/run real generated C and reject invalid Vala, using synthetic inputs."""
from pathlib import Path
import json,os,subprocess,sys
prefix=Path(sys.argv[1]);work=Path(sys.argv[2]);assert not work.exists();work.mkdir()
compiler=prefix/'usr/bin/valac';vapi=prefix/'usr/share/vala-0.56/vapi';assert compiler.is_file() and vapi.is_dir()
version=subprocess.check_output([str(compiler),'--version'],text=True).strip();assert version=='Vala 0.56.19'
valid='''class NativeProbe : GLib.Object {
 public string label { get; set; default = "Calendário local"; }
 public signal void observed (int value);
 public static bool checked (int value) throws GLib.Error {
  if (value < 0) throw new GLib.IOError.INVALID_ARGUMENT ("synthetic invalid value");
  return true;
 }
 public static int main () {
  var probe = new NativeProbe ();
  assert (probe.label == "Calendário local");
  int received = 0; probe.observed.connect ((value) => { received = value; });
  probe.observed (7); assert (received == 7);
  try { checked (-1); assert_not_reached (); }
  catch (GLib.IOError.INVALID_ARGUMENT error) { assert (error.message == "synthetic invalid value"); }
  catch (GLib.Error error) { assert_not_reached (); }
  try { assert (checked (1)); } catch (GLib.Error error) { assert_not_reached (); }
  return 0;
 }
}
'''
runs=[]
for cycle in range(2):
    p=work/str(cycle);p.mkdir();source=p/'probe.vala';source.write_text(valid);exe=p/'probe'
    args=[str(compiler),'--pkg','gio-2.0','--vapidir',str(vapi),'--directory',str(p),'-X','-std=gnu17','-o',str(exe),str(source)]
    result=subprocess.run(args,capture_output=True,text=True,timeout=30)
    (p/'compile.stdout').write_text(result.stdout);(p/'compile.stderr').write_text(result.stderr);assert result.returncode==0
    subprocess.run([str(exe)],check=True,timeout=10)
    runs.append({'cycle':cycle,'compile_exit':0,'generated_native_exit':0})
    if cycle==0:
        bad=p/'bad.vala';bad.write_text('int main () { int value = "wrong type"; return value; }\n');rejected=p/'rejected'
        result=subprocess.run([str(compiler),'--vapidir',str(vapi),'--directory',str(p),'-o',str(rejected),str(bad)],capture_output=True,text=True,timeout=15)
        (p/'rejected.stdout').write_text(result.stdout);(p/'rejected.stderr').write_text(result.stderr)
        assert result.returncode!=0 and 'Cannot convert' in result.stderr and not rejected.exists()
print(json.dumps({'compiler_version':version,'actual_generated_GObject_UTF8_signal_error_ABI':True,'invalid_typed_source_refused':True,'no_rejected_executable':True,'post_refusal_recovery_cycles':runs,'real_credentials_used':False}))
