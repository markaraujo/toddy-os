#!/usr/bin/env python3
"""Actual synthetic Gst audio/video samples; no device/GL/display claim."""
import json
import gi
for name in ['Gst','GstApp','GstAudio','GstVideo']:gi.require_version(name,'1.0')
from gi.repository import Gst,GstApp,GstAudio,GstVideo
Gst.init(None)
assert Gst.version()[:3]==(1,28,6)
video_caps=Gst.Caps.from_string('video/x-raw,format=RGB,width=8,height=8,framerate=1/1')
v=GstVideo.VideoInfo.new_from_caps(video_caps);assert (v.width,v.height,v.size)==(8,8,192)
audio_caps=Gst.Caps.from_string('audio/x-raw,format=S16LE,layout=interleaved,rate=48000,channels=2')
a=GstAudio.AudioInfo.new_from_caps(audio_caps);assert (a.rate,a.channels,a.bpf)==(48000,2,4)
cycles=[]
for cycle in range(2):
 for kind,text,expected in [
  ('video','videotestsrc num-buffers=1 pattern=red ! video/x-raw,format=RGB,width=8,height=8,framerate=1/1 ! appsink name=out sync=false wait-on-eos=false',b'\xff\x00\x00'*64),
  ('audio','audiotestsrc num-buffers=1 samplesperbuffer=16 wave=silence ! audio/x-raw,format=S16LE,rate=48000,channels=2 ! appsink name=out sync=false wait-on-eos=false',b'\x00'*64)]:
  pipeline=Gst.parse_launch(text)
  try:
   assert pipeline.set_state(Gst.State.PLAYING)!=Gst.StateChangeReturn.FAILURE
   sink=pipeline.get_by_name('out');assert isinstance(sink,GstApp.AppSink)
   sample=sink.emit('try-pull-sample',5*Gst.SECOND);assert sample is not None
   buffer=sample.get_buffer();data=buffer.extract_dup(0,buffer.get_size());assert data==expected
   message=pipeline.get_bus().timed_pop_filtered(5*Gst.SECOND,Gst.MessageType.EOS|Gst.MessageType.ERROR)
   assert message is not None and message.type==Gst.MessageType.EOS
  finally:assert pipeline.set_state(Gst.State.NULL)!=Gst.StateChangeReturn.FAILURE
  state,current,pending=pipeline.get_state(Gst.SECOND);assert current==Gst.State.NULL
  cycles.append({'cycle':cycle,'kind':kind,'exact_sample_bytes':len(data),'EOS_received':True,'stop_NULL_verified':True})
print(json.dumps({'version':'1.28.6','GstApp_Audio_Video_GI':True,'typed_video_8x8_RGB':True,'typed_audio_48k_stereo':True,'synthetic_samples':cycles,'devices_GL_audio_playback_screencast_tested':False}))
