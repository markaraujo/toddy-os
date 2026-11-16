"""Exact disposable candidate180->204GiB geometry; never generic disk selection."""
import binascii
import hashlib
import json
import struct

OLD=180*1024**3;NEW=204*1024**3;SECTOR=512
UUID='e7726c1a-8f91-445f-96ac-88721b58caf8'
DISK_ID='D0DEB477-38D0-41A4-A76D-99F68B865452'
SERIAL='TODDY-LFS-TARGET';ROOT_PARTUUID='5e491ca4-ea89-4e55-94b3-cb0b3fcc4694'
PARTITIONS=[
 {'node':'/dev/vdb1','start':2048,'size':4096,'type':'21686148-6449-6E6F-744E-656564454649','uuid':'DE9720D1-1ECC-4062-A094-7F7F61E3DB0D','name':'bios'},
 {'node':'/dev/vdb2','start':6144,'size':1048576,'type':'C12A7328-F81F-11D2-BA4B-00A0C93EC93B','uuid':'C6F094FC-C95F-4BAB-98D5-80062EF6B62F','name':'esp'},
 {'node':'/dev/vdb3','start':1054720,'size':16777216,'type':'0657FD6D-A4AB-43C4-84E5-0933C84B4F4F','uuid':'9EA6FCFC-6A80-4D38-99F8-C25F802A52C5','name':'swap'},
 {'node':'/dev/vdb4','start':17831936,'size':359653376,'type':'0FC63DAF-8483-4772-8E79-3D69D8477DE4','uuid':'5E491CA4-EA89-4E55-94B3-CB0B3FCC4694','name':'lfs'}]


def table(size):
    if size not in (OLD,NEW):raise ValueError('Exact candidate disk size required')
    parts=[dict(row) for row in PARTITIONS];parts[3]['size']+=(size-OLD)//SECTOR
    return {'label':'gpt','id':DISK_ID,'device':'/dev/vdb','unit':'sectors','firstlba':34,'lastlba':size//SECTOR-34,'sectorsize':512,'partitions':parts}


def verify_table(actual,size):
    if actual!=table(size):raise ValueError('Exact target GPT identity/start/type/size required')


def partition_bytes(size):return table(size)['partitions'][3]['size']*SECTOR


def script():
    value=table(NEW)
    header='label: gpt\nlabel-id: '+DISK_ID+'\ndevice: /dev/vdb\nunit: sectors\nfirst-lba: 34\nlast-lba: '+str(value['lastlba'])+'\nsector-size: 512\n\n'
    return header+''.join(row['node']+' : start='+str(row['start'])+', size='+str(row['size'])+', type='+row['type']+', uuid='+row['uuid']+', name="'+row['name']+'"\n' for row in value['partitions'])


def gpt(read_at,size):
    """Validate both existing GPT CRCs/arrays via a supplied read-only reader."""
    sectors=size//512;headers=[];arrays=[]
    for lba,alternate in ((1,sectors-1),(sectors-1,1)):
        block=read_at(512,lba*512)
        if len(block)!=512 or block[:8]!=b'EFI PART':raise ValueError('GPT header signature missing')
        revision,length,checksum=struct.unpack_from('<III',block,8)
        if revision!=0x10000 or length!=92:raise ValueError('GPT header format differs')
        checked=bytearray(block[:length]);checked[16:20]=b'\0'*4
        current,other,first,last=struct.unpack_from('<QQQQ',block,24)
        entries_lba,count,entry_size,entry_crc=struct.unpack_from('<QIII',block,72)
        if binascii.crc32(checked)&0xffffffff!=checksum or current!=lba or other!=alternate or first!=34 or last!=sectors-34 or count!=128 or entry_size!=128 or entries_lba!=(2 if lba==1 else sectors-33):raise ValueError('GPT header CRC/geometry differs')
        array=read_at(count*entry_size,entries_lba*512)
        if len(array)!=count*entry_size or binascii.crc32(array)&0xffffffff!=entry_crc:raise ValueError('GPT entry array CRC differs')
        headers.append(block);arrays.append(array)
    if arrays[0]!=arrays[1] or headers[0][56:72]!=headers[1][56:72]:raise ValueError('GPT replicas differ')
    return {'primary_sha256':hashlib.sha256(headers[0]).hexdigest(),'backup_sha256':hashlib.sha256(headers[1]).hexdigest(),'entries_sha256':hashlib.sha256(arrays[0]).hexdigest()}


def encoded(value):return json.dumps(value,sort_keys=True,separators=(',',':')).encode()
