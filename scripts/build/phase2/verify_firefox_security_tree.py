"""Read-only archive/content reconciliation of an already extracted candidate."""
from pathlib import Path, PurePosixPath
import hashlib
import os
import stat
import tarfile


def verify(archive, source, progress, expected_non_dot=510287, expected_bytes=3515456965):
    seen=set();counts={'members':0,'non_dot_members':0,'expanded_regular_bytes':0,'verified_regular_files':0}
    with tarfile.open(archive,mode='r|xz') as bundle:
        for member in bundle:
            counts['members']+=1
            parts=PurePosixPath(member.name).parts
            if not parts:
                assert member.name=='.' and member.isdir();continue
            assert parts[0]==source.name and '..' not in parts and not member.name.startswith('/')
            counts['non_dot_members']+=1
            relative=PurePosixPath(*parts[1:]);p=source.joinpath(*parts[1:])
            assert relative not in seen,'Duplicate archive path';seen.add(relative)
            st=p.lstat()
            if member.isfile():
                assert stat.S_ISREG(st.st_mode) and st.st_size==member.size
                counts['expanded_regular_bytes']+=member.size
                archived=bundle.extractfile(member);assert archived
                expected=hashlib.file_digest(archived,'sha256').hexdigest()
                with p.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==expected,str(relative)
                filtered=tarfile.data_filter(member,str(source.parent))
                assert filtered and stat.S_IMODE(st.st_mode)==filtered.mode and st.st_uid==st.st_gid==0
                counts['verified_regular_files']+=1
            elif member.isdir():assert stat.S_ISDIR(st.st_mode)
            elif member.issym():assert stat.S_ISLNK(st.st_mode) and os.readlink(p)==member.linkname
            elif member.islnk():
                target=PurePosixPath(member.linkname);assert target.parts[0]==source.name and '..' not in target.parts
                other=source.joinpath(*target.parts[1:]);assert p.stat().st_ino==other.stat().st_ino
            else:raise AssertionError('Unexpected archive object')
            if counts['members']%4096==0:progress(counts)
    actual=set()
    for parent,dirs,files in os.walk(source,followlinks=False):
        for name in dirs+files:actual.add(PurePosixPath(str((Path(parent)/name).relative_to(source))))
    seen.discard(PurePosixPath('.'))
    assert actual==seen,'Missing/extra extracted paths'
    assert counts['members']==expected_non_dot+1 and counts['non_dot_members']==expected_non_dot and counts['expanded_regular_bytes']==expected_bytes
    progress(counts);return counts
