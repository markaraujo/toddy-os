"""Select the existing owned recovery entry through actual QMP keyboard input."""
import json,socket,time

def select_recovery(context,stop):
 deadline=time.monotonic()+30;events=[];s=None
 try:
  while not (context/'q').exists():
   assert time.monotonic()<deadline,'QMP missing before recovery selection'
   if stop.wait(.05):raise InterruptedError('Controller stopped')
  s=socket.socket(socket.AF_UNIX);s.settimeout(5);s.connect(str(context/'q'));stream=s.makefile('rwb',buffering=0);assert 'QMP' in json.loads(stream.readline())
  def call(name,args=None):
   stream.write((json.dumps({'execute':name,**({'arguments':args} if args else {})})+'\n').encode())
   while True:
    row=json.loads(stream.readline())
    if 'event' in row:continue
    assert 'return' in row,row
    events.append({'execute':name,'return':row['return']});return row['return']
  call('qmp_capabilities')
  while True:
   p=context/'serial.log';text=p.read_text(errors='replace') if p.exists() else ''
   if 'foundation recovery)' in text:break
   assert time.monotonic()<deadline,'Owned GRUB recovery menu not observed'
   if stop.wait(.05):raise InterruptedError('Controller stopped')
  for key in ['down','ret']:
   call('send-key',{'keys':[{'type':'qcode','data':key}],'hold-time':80});time.sleep(.15)
  result={'selected':True,'scope':'Actual keyboard down+Enter after owned GRUB menu observed; native running foundation config hash separately required. No config/default/disk modification.','events':events}
 except Exception as error:result={'selected':False,'error':type(error).__name__,'message':str(error),'events':events}
 finally:
  if s:s.close()
 (context/'recovery-menu-selection.json').write_text(json.dumps(result,indent=2)+'\n')
