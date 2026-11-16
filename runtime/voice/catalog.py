"""Fixed root-native artifact/license metadata. Missing catalog leaves voice off."""
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat

from .artifacts import Artifact, Consent, VoiceError
from .process import ProcessRunner
from .session import VoiceSession

FIXED={
 'capture':'/usr/lib/toddy/voice/pw-record',
 'playback':'/usr/lib/toddy/voice/pw-play',
 'device-list':'/usr/bin/pw-dump',
 'stt-engine':'/usr/bin/whisper-cli',
 'stt-model':'/usr/share/toddy/voice/models/ggml-base.bin',
 'tts-engine':'/usr/bin/espeak-ng'}
VERSIONS={'pipewire':'1.6.8','wireplumber':'0.5.15','whisper-cpp':'1.9.5','espeak-ng':'1.52.0'}
HEX=re.compile('[0-9a-f]{64}\\Z')


def root_read(path,maximum,*,content=True):
    path=Path(path)
    if not path.is_absolute():raise VoiceError('voice_native_catalog_unavailable')
    for component in (path,*path.parents):
        info=component.lstat()
        if stat.S_ISLNK(info.st_mode) or info.st_uid!=0 or info.st_mode&0o022:
            raise VoiceError('voice_native_catalog_unavailable')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
    try:
        info=os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1 or not 0<info.st_size<=maximum:
            raise VoiceError('voice_native_catalog_unavailable')
        return os.read(fd,maximum+1) if content else info
    finally:os.close(fd)


def decode(data):
    def pairs(items):
        value={}
        for key,item in items:
            if key in value:raise VoiceError('voice_native_catalog_invalid')
            value[key]=item
        return value
    value=json.loads(data.decode(),object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(VoiceError('voice_native_catalog_invalid')))
    def check(item,depth=0):
        if depth>32:raise VoiceError('voice_native_catalog_invalid')
        if isinstance(item,str):item.encode('utf-8',errors='strict')
        elif isinstance(item,dict):
            for key,child in item.items():check(key,depth+1);check(child,depth+1)
        elif isinstance(item,list):
            for child in item:check(child,depth+1)
        elif isinstance(item,(int,float)) and not isinstance(item,bool):
            if not math.isfinite(item) or abs(item)>2**53-1:raise VoiceError('voice_native_catalog_invalid')
    check(value)
    return value


class NativeVoiceCatalog:
    def __init__(self):
        try:
            raw=root_read('/usr/share/toddy/voice/catalog.json',65536);value=decode(raw)
            keys={'voice_catalog_version','status','tts_engine','native_dependencies','process_control','artifacts'}
            if not isinstance(value,dict) or set(value)!=keys or type(value['voice_catalog_version']) is not int or value['voice_catalog_version']!=1 or value['status']!='native-qualified' or value['tts_engine']!='espeak-ng' or set(value['artifacts'])!=set(FIXED) or set(value['native_dependencies'])!=set(VERSIONS):
                raise VoiceError('voice_native_catalog_invalid')
            for name,version in VERSIONS.items():
                row=value['native_dependencies'][name]
                if set(row)!={'version','component_record_sha256'} or row['version']!=version or not HEX.fullmatch(row['component_record_sha256']):
                    raise VoiceError('voice_native_catalog_invalid')
            control=value['process_control']
            if set(control)!={'launcher_sha256','runner_sha256','pw_cat_sha256','pw_cat_bytes','evidence_sha256'} or not HEX.fullmatch(control['evidence_sha256']):
                raise VoiceError('voice_native_catalog_invalid')
            for name,key in [('child.py','launcher_sha256'),('process.py','runner_sha256')]:
                if hashlib.sha256(root_read(Path(__file__).with_name(name),65536)).hexdigest()!=control[key]:
                    raise VoiceError('voice_native_process_control_unqualified')
            self.artifacts={}
            for role,row in value['artifacts'].items():
                row=dict(row)
                if row['path']!=FIXED[role] or not row['license_path'].startswith('/usr/share/doc/'):
                    raise VoiceError('voice_native_catalog_invalid')
                row['path']=Path(row['path']);row['license_path']=Path(row['license_path']);row['languages']=tuple(row['languages'])
                artifact=Artifact(**row).validate_metadata()
                if role=='stt-model' and (artifact.size!=147951465 or artifact.sha256!='60ed5bc3dd14eea856493d334349b405782ddcaf0028d4b5df4088345fba2efe'):
                    raise VoiceError('voice_native_catalog_invalid')
                if artifact.kind!=('stt-model' if role=='stt-model' else 'engine'):
                    raise VoiceError('voice_native_catalog_invalid')
                root_read(artifact.path,4*1024**3,content=False)
                root_read(artifact.license_path,65536,content=False)
                self.artifacts[role]=artifact
            if len({a.artifact_id for a in self.artifacts.values()})!=len(self.artifacts):
                raise VoiceError('voice_native_catalog_invalid')
            self.pin=hashlib.sha256(raw).hexdigest();self.value=value
        except (OSError,ValueError,TypeError,KeyError,AttributeError,RecursionError):
            raise VoiceError('voice_native_catalog_unavailable') from None

    def preview(self):
        notices={}
        for artifact in self.artifacts.values():
            data=root_read(artifact.license_path,65536)
            if hashlib.sha256(data).hexdigest()!=artifact.license_sha256:
                raise VoiceError('voice_license_changed')
            notices[artifact.license_sha256]={'license_id':artifact.license_id,'text':data.decode(),
                'source_url':artifact.source_url}
        return {'catalog_pin':self.pin,'tts_engine':'espeak-ng','languages':['en','pt-BR'],
            'artifacts':[{'role':role,'id':a.artifact_id,'version':a.version,'license_id':a.license_id} for role,a in self.artifacts.items()],
            'notices':list(notices.values()),'text_available':True,'always_listening':False,'automatic_download':False,
            'integrity_rechecked_on_action':True}

    def _consents(self):return {a.artifact_id:Consent(a.sha256,a.license_sha256) for a in self.artifacts.values()}

    def _transport(self):
        control=self.value['process_control']
        root_read('/usr/bin/pw-cat',64*1024**2,content=False)
        Artifact._hash(Path('/usr/bin/pw-cat'),control['pw_cat_sha256'],maximum=64*1024**2,
            expected_size=control['pw_cat_bytes'],executable=True)

    def session(self,*,accepted_pin,changed):
        if accepted_pin!=self.pin:raise VoiceError('voice_license_review_changed')
        self._transport()
        return VoiceSession(self.artifacts,self._consents(),tts_engine='espeak-ng',changed=changed)

    def devices(self,*,accepted_pin,cancel):
        if accepted_pin!=self.pin:raise VoiceError('voice_license_review_changed')
        artifact=self.artifacts['device-list'];program=artifact.verify(self._consents().get(artifact.artifact_id))
        result=ProcessRunner().run([program],cancel=cancel,timeout=5,capture_stdout=True,output_limit=1024*1024)
        data=decode(result.stdout)
        if not isinstance(data,list) or len(data)>8192:raise VoiceError('voice_device_list_invalid')
        devices=[];seen=set()
        for row in data:
            if not isinstance(row,dict) or row.get('type')!='PipeWire:Interface:Node':continue
            props=row.get('info',{}).get('props',{})
            direction={'Audio/Source':'input','Audio/Sink':'output'}.get(props.get('media.class'))
            serial=props.get('object.serial');label=props.get('node.description',props.get('node.name',''))
            if direction is None:continue
            if type(serial) is not int or not 1<=serial<2**53 or not isinstance(label,str) or not 0<len(label)<=512 or any(ord(char)<32 for char in label):
                raise VoiceError('voice_device_list_invalid')
            key=(direction,str(serial))
            if key in seen:raise VoiceError('voice_device_list_invalid')
            seen.add(key);devices.append({'direction':direction,'target':str(serial),'label':label})
            if len(devices)>64:raise VoiceError('voice_device_list_limit')
        return devices
