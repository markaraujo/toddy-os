"""Exercise installed-layout UPower GI and CLI without inventing hardware state."""
import json,subprocess,sys
from pathlib import Path
import gi
gi.require_version('UPowerGlib','1.0')
from gi.repository import UPowerGlib as Up
prefix=Path(sys.argv[1])
r=subprocess.run([str(prefix/'usr/bin/upower'),'--help'],capture_output=True,text=True,timeout=10,check=True)
assert '--enumerate' in r.stdout and '--version' in r.stdout
assert (Up.MAJOR_VERSION,Up.MINOR_VERSION,Up.MICRO_VERSION)==(1,91,3)
assert Up.Device.kind_to_string(Up.DeviceKind.BATTERY)=='battery'
assert Up.Device.state_to_string(Up.DeviceState.DISCHARGING)=='discharging'
assert Up.Device.kind_from_string('toddy-invalid-kind')==Up.DeviceKind.UNKNOWN
item=Up.HistoryItem.new();item.set_value(42.5);item.set_time(123456);item.set_state(Up.DeviceState.DISCHARGING)
assert item.get_value()==42.5 and item.get_time()==123456 and item.get_state()==Up.DeviceState.DISCHARGING
assert Up.Device.__gtype__.name=='UpDevice' and Up.Client.__gtype__.name=='UpClient'
print(json.dumps({'version':'1.91.3','cli_help_exit':0,'typed_history_roundtrip':True,'unknown_kind_refused_to_unknown':True,'native_gi_types':['UpDevice','UpClient'],'scope':'CLI/types/history object only; no live power/device acceptance'}))
