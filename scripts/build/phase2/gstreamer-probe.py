#!/usr/bin/env python3
"""Synthetic native Gst GI pipeline only; never a device/screencast claim."""
import json
import gi
gi.require_version('Gst','1.0')
from gi.repository import Gst,GLib
Gst.init(None)
assert Gst.version()[:3]==(1,28,6)
caps=Gst.Caps.from_string('audio/x-raw,format=S16LE,rate=48000,channels=2')
assert caps.is_fixed() and caps.get_structure(0).get_int('rate')==(True,48000)
buffer=Gst.Buffer.new_allocate(None,4,None);assert buffer.fill(0,b'TODY')==4
assert buffer.extract_dup(0,4)==b'TODY'
refused=False
try:Gst.parse_launch('toddy_nonexistent_element_xyz')
except GLib.Error:refused=True
assert refused
cycles=[]
for cycle in range(2):
 pipeline=Gst.parse_launch('fakesrc num-buffers=3 sizetype=fixed sizemax=16 ! identity ! fakesink')
 try:
  state=pipeline.set_state(Gst.State.PLAYING);assert state!=Gst.StateChangeReturn.FAILURE
  message=pipeline.get_bus().timed_pop_filtered(5*Gst.SECOND,Gst.MessageType.EOS|Gst.MessageType.ERROR)
  assert message is not None and message.type==Gst.MessageType.EOS
 finally:
  assert pipeline.set_state(Gst.State.NULL)!=Gst.StateChangeReturn.FAILURE
 state,current,pending=pipeline.get_state(Gst.SECOND);assert current==Gst.State.NULL
 cycles.append({'cycle':cycle,'EOS_received':True,'stop_NULL_verified':True})
print(json.dumps({'version':'1.28.6','typed_caps_and_buffer':True,'missing_element_refused':refused,'synthetic_pipeline_cycles':cycles,'hardware_audio_video_screencast_tested':False}))
