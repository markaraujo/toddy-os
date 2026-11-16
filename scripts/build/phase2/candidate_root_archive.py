"""Full metadata snapshot and streaming archive proof for one candidate1 root.

No extraction, commands, privileged state or implicit filesystem scope at import.
H10 snapshot fields are extended with raw xattrs and stable inode/ctime pins.
"""
import base64,hashlib,json,os,stat,struct,tarfile
from decimal import Decimal
from pathlib import Path,PurePosixPath

CHUNK=1024**2


def encoded(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()+b'\n'

def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def names(root):
    paths=['.']
    for base,dirs,files in os.walk(root,followlinks=False):paths.extend((Path(base)/name).relative_to(root).as_posix() for name in dirs+files)
    return sorted(paths,key=os.fsencode)

def canonical(name):
    path=PurePosixPath(name)
    if not isinstance(name,str) or not name or path.is_absolute() or '..' in path.parts or path.as_posix()!=name or any(ord(char)<32 for char in name):raise ValueError('candidate_root_archive_path')
    return name


def snapshot(root):
    root=Path(root)
    if root.resolve()!=root or not root.is_dir():raise ValueError('candidate_root_archive_root')
    device=root.stat().st_dev;rows={};identities={};classes={};digests={};regular=allocated=attrs=0
    for name in names(root):
        canonical(name);path=root if name=='.' else root/name;before=path.lstat()
        if path.parent.resolve()!=path.parent or before.st_dev!=device:raise ValueError('candidate_root_archive_redirect_or_device')
        row={'mode':before.st_mode,'uid':before.st_uid,'gid':before.st_gid,'mtime_ns':before.st_mtime_ns,
            'xattrs':{key:base64.b64encode(os.getxattr(path,key,follow_symlinks=False)).decode() for key in sorted(os.listxattr(path,follow_symlinks=False))}}
        attrs+=sum(len(base64.b64decode(value)) for value in row['xattrs'].values())
        identity=(before.st_dev,before.st_ino)
        if stat.S_ISREG(before.st_mode):
            if identity not in digests:digests[identity]=sha(path);regular+=before.st_size;allocated+=before.st_blocks*512
            row.update(sha256=digests[identity],size=before.st_size)
        elif stat.S_ISLNK(before.st_mode):row['symlink']=os.readlink(path)
        elif not stat.S_ISDIR(before.st_mode):raise ValueError('candidate_root_archive_special_node')
        if not stat.S_ISDIR(before.st_mode):classes.setdefault(identity,[]).append(name)
        after=path.lstat()
        fields=('st_dev','st_ino','st_mode','st_uid','st_gid','st_size','st_mtime_ns','st_ctime_ns','st_nlink')
        if any(getattr(before,key)!=getattr(after,key) for key in fields):raise ValueError('candidate_root_archive_changed_during_snapshot')
        identities[name]={'device':before.st_dev,'inode':before.st_ino,'links':before.st_nlink,'ctime_ns':before.st_ctime_ns}
        rows[name]=row
    for group in classes.values():
        if any(identities[name]['links']!=len(group) for name in group):raise ValueError('candidate_root_archive_external_hardlink')
    groups=sorted(sorted(group) for group in classes.values() if len(group)>1)
    return {'version':1,'entries':rows,'hardlink_groups':groups,'identities':identities,
        'unique_regular_bytes':regular,'allocated_regular_bytes':allocated,
        # Conservative streaming admission, not a reclamation/sparse-host claim.
        'tar_upper_bound_bytes':2*regular+16384*len(rows)+8*attrs+128*1024**2}


def acl_text(raw,mode=None):
    if raw is None:
        if mode is None:return None
        rows=[(1,(mode>>6)&7,0xffffffff),(4,(mode>>3)&7,0xffffffff),(32,mode&7,0xffffffff)]
    else:
        if len(raw)<4 or (len(raw)-4)%8 or struct.unpack('<I',raw[:4])[0]!=2:raise ValueError('candidate_root_archive_ACL_binary')
        rows=[struct.unpack('<HHI',raw[index:index+8]) for index in range(4,len(raw),8)]
    result=[];tags={1:'user',2:'user',4:'group',8:'group',16:'mask',32:'other'}
    for tag,perms,identifier in rows:
        if tag not in tags or perms>7 or (tag in (2,8))!=(identifier!=0xffffffff):raise ValueError('candidate_root_archive_ACL_entry')
        result.append(tags[tag]+':'+(str(identifier) if tag in (2,8) else '')+':'+''.join(letter if perms&bit else '-' for letter,bit in (('r',4),('w',2),('x',1))))
    return '\n'.join(result)


def verify_tar(stream,expected):
    """Independent logical member/byte/PAX/ACL/hardlink read; never extract."""
    if expected.get('version')!=1 or not isinstance(expected.get('entries'),dict):raise ValueError('candidate_root_archive_manifest')
    rows=expected['entries'];seen={};groups={};class_for={name:group[0] for group in expected['hardlink_groups'] for name in group}
    with tarfile.open(fileobj=stream,mode='r|',encoding='utf-8',errors='surrogateescape') as archive:
        for member in archive:
            name=canonical(member.name.rstrip('/') or '.')
            if name not in rows or name in seen:raise ValueError('candidate_root_archive_unselected_or_duplicate_member')
            row=rows[name];kind=stat.S_IFMT(row['mode']);perms=stat.S_IMODE(row['mode'])
            stamp=Decimal(member.pax_headers.get('mtime',str(member.mtime)))
            if not stamp.is_finite() or len(stamp.as_tuple().digits)>40 or abs(stamp.as_tuple().exponent)>40:raise ValueError('candidate_root_archive_mtime_bound')
            mtime=int(stamp*1000000000)
            if (member.mode,member.uid,member.gid,mtime)!=(perms,row['uid'],row['gid'],row['mtime_ns']):raise ValueError('candidate_root_archive_metadata_differs')
            pax=member.pax_headers
            allowed={'mtime','path','linkpath','size','uid','gid','uname','gname','hdrcharset','SCHILY.acl.access','SCHILY.acl.default'}
            if any(key not in allowed and not key.startswith(('SCHILY.xattr.','GNU.sparse.')) for key in pax):raise ValueError('candidate_root_archive_unknown_PAX')
            if member.islnk():
                target=canonical(member.linkname)
                if target not in seen or class_for.get(name)!=class_for.get(target) or class_for.get(name) is None:raise ValueError('candidate_root_archive_hardlink_class_differs')
                effective=seen[target];xattrs=effective['xattrs']
                if any(key.startswith('SCHILY.xattr.') or key.startswith('SCHILY.acl.') for key in pax):raise ValueError('candidate_root_archive_hardlink_metadata_override')
                if {key:row.get(key) for key in ('sha256','size','symlink')}!={key:effective.get(key) for key in ('sha256','size','symlink')}:raise ValueError('candidate_root_archive_hardlink_content_differs')
                groups.setdefault(target,[target]).append(name)
            else:
                xattrs={key.removeprefix('SCHILY.xattr.'):base64.b64encode(value.encode('utf-8','surrogateescape')).decode() for key,value in pax.items() if key.startswith('SCHILY.xattr.')}
                if xattrs!=row['xattrs']:raise ValueError('candidate_root_archive_xattrs_differs')
                access=base64.b64decode(xattrs['system.posix_acl_access']) if 'system.posix_acl_access' in xattrs else None
                default=base64.b64decode(xattrs['system.posix_acl_default']) if 'system.posix_acl_default' in xattrs else None
                if (access is not None and 'SCHILY.acl.access' not in pax or default is not None and 'SCHILY.acl.default' not in pax or
                        'SCHILY.acl.access' in pax and pax['SCHILY.acl.access']!=acl_text(access,perms) or
                        'SCHILY.acl.default' in pax and pax['SCHILY.acl.default']!=acl_text(default)):
                    raise ValueError('candidate_root_archive_ACL_differs')
                if kind==stat.S_IFREG:
                    if not member.isfile() or member.size!=row['size']:raise ValueError('candidate_root_archive_regular_kind_or_size')
                    actual=hashlib.sha256();size=0;source=archive.extractfile(member)
                    while chunk:=source.read(CHUNK):size+=len(chunk);actual.update(chunk)
                    if size!=row['size'] or actual.hexdigest()!=row['sha256']:raise ValueError('candidate_root_archive_file_bytes_differs')
                elif kind==stat.S_IFLNK:
                    if not member.issym() or member.linkname!=row['symlink']:raise ValueError('candidate_root_archive_symlink_differs')
                elif kind==stat.S_IFDIR:
                    if not member.isdir():raise ValueError('candidate_root_archive_directory_kind')
                else:raise ValueError('candidate_root_archive_special_member')
            if xattrs!=row['xattrs']:raise ValueError('candidate_root_archive_link_xattrs_differs')
            seen[name]=row
    if set(seen)!=set(rows) or sorted(sorted(group) for group in groups.values())!=expected['hardlink_groups']:raise ValueError('candidate_root_archive_inventory_or_hardlinks_differs')
    return {'state':'all-members-bytes-metadata-verified','entries':len(rows),'unique_regular_bytes':expected['unique_regular_bytes'],
        'xattrs_ACLs_symlinks_hardlink_classes_verified':True,'privileged_extraction_performed':False}
