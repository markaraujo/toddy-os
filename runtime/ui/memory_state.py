"""Headless owner-memory validation and private FD handoff boundaries."""
import fcntl
import hashlib
import stat
import os
import re

from .model import open_profile_import
from .task_state import body,REVISION
from ..shared.json import strict_json


def sealed_local_backup(path):
    source=open_profile_import(path)
    target=os.memfd_create('toddy-owner-memory-restore',os.MFD_CLOEXEC|os.MFD_ALLOW_SEALING)
    try:
        os.fchmod(target,0o600)
        size=os.fstat(source).st_size
        data=os.pread(source,8*1024*1024+1,0)
        if len(data)!=size:raise ValueError('memory_backup_changed')
        view=memoryview(data)
        while view:view=view[os.write(target,view):]
        fcntl.fcntl(target,fcntl.F_ADD_SEALS,fcntl.F_SEAL_SEAL|fcntl.F_SEAL_WRITE|fcntl.F_SEAL_GROW|fcntl.F_SEAL_SHRINK)
        result=os.open('/proc/self/fd/'+str(target),os.O_RDONLY|os.O_CLOEXEC)
        return result
    finally:
        os.close(source);os.close(target)


def page(encoded,profile):
    value=body(encoded,49152)
    if value.get('profile_id')!=profile or not isinstance(value.get('profile_revision'),str) or not REVISION.fullmatch(value['profile_revision']) or \
            type(value.get('memory_generation')) is not int or not 0<=value['memory_generation']<2**53 or \
            not isinstance(value.get('records'),list) or len(value['records'])>32 or \
            type(value.get('complete')) is not bool or type(value.get('user_document_review_required')) is not bool or \
            not isinstance(value.get('next_cursor'),str) or len(value['next_cursor'])>128:
        raise ValueError('invalid_memory_page')
    seen=set()
    for row in value['records']:
        if not isinstance(row,dict) or not isinstance(row.get('id'),str) or not re.fullmatch(r'[a-z][a-z0-9-]{0,63}',row['id']) or \
                row['id'] in seen or not isinstance(row.get('text'),str) or len(row['text'].encode('utf-8'))>4096 or \
                row.get('kind') not in ('document','preference') or \
                any(not isinstance(row.get(key),str) or len(row[key].encode('utf-8'))>1024 for key in ('source_kind','source_ref','source_revision')):
            raise ValueError('invalid_memory_record')
        seen.add(row['id'])
    return value


def reviewed_document(descriptor,snapshot):
    info=os.fstat(descriptor)
    seals=fcntl.F_SEAL_SEAL|fcntl.F_SEAL_WRITE|fcntl.F_SEAL_GROW|fcntl.F_SEAL_SHRINK
    if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or info.st_mode&0o077 or not 0<=info.st_size<=65536 or \
            fcntl.fcntl(descriptor,fcntl.F_GET_SEALS)&seals!=seals:
        raise ValueError('invalid_review_document')
    data=os.pread(descriptor,65537,0)
    if len(data)!=info.st_size or info.st_size!=snapshot.get('user_document_bytes') or \
            hashlib.sha256(data).hexdigest()!=snapshot.get('user_document_sha256'):
        raise ValueError('review_document_changed')
    text=data.decode('utf-8')
    if any(ord(char)<32 and char not in '\t\r\n' for char in text):raise ValueError('review_document_controls')
    return text


def reviewed_preferences(encoded):
    if len(encoded.encode('utf-8'))>60000:raise ValueError('review_preferences_limit')
    value=strict_json(encoded.encode('utf-8'))
    if not isinstance(value,dict) or len(value)>32:raise ValueError('review_preferences_limit')
    for key,text in value.items():
        if not re.fullmatch(r'[a-z][a-z0-9-]{0,63}',key) or not isinstance(text,str) or not text or len(text.encode('utf-8'))>4096:
            raise ValueError('review_preferences_schema')
    return value


