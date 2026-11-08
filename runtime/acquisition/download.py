"""Explicit optional public-artifact acquisition. No activation or execution.

The caller supplies a trusted pinned catalog record, never an imported URL grant.
Only HTTPS; TLS defaults remain enabled. Errors expose codes, not URLs/headers.
"""
from contextlib import contextmanager
import fcntl
import hashlib
import http.client
import os
from pathlib import Path
import re
import shutil
import stat
import urllib.error
import urllib.request
from urllib.parse import urlsplit


class AcquisitionError(Exception):
    pass


def public_url(value):
    try:
        url = urlsplit(value)
        if url.scheme != 'https' or not url.hostname or url.username or url.password or url.fragment:
            raise ValueError()
        _ = url.port
    except (ValueError, TypeError):
        raise AcquisitionError('invalid_artifact_url') from None
    return value


class PublicRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        public_url(newurl)
        # Artifact URLs may redirect to signed CDN URLs. No credentials/custom
        # headers are accepted; a Range is safe to retain across public origins.
        redirected = super().redirect_request(request, fp, code, message, headers, newurl)
        if redirected:
            redirected.headers = {key: value for key, value in redirected.headers.items()
                                  if key.lower() in ('range', 'if-range', 'user-agent')}
            redirected.unredirected_hdrs.clear()
        return redirected


def _open(request):
    # Disable implicit environment proxies: credentials must never enter this flow.
    return urllib.request.build_opener(urllib.request.ProxyHandler({}), PublicRedirect()).open(request, timeout=30)


def _regular(directory, name, flags, mode=0o600):
    fd = os.open(name, flags | os.O_NOFOLLOW | os.O_CLOEXEC, mode, dir_fd=directory)
    info = os.fstat(fd)
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1 or stat.S_IMODE(info.st_mode) != 0o600:
        os.close(fd)
        raise AcquisitionError('unsafe_cache_file')
    return fd


def _digest(file):
    file.seek(0)
    digest = hashlib.sha256()
    while chunk := file.read(1024 * 1024):
        digest.update(chunk)
    return digest


@contextmanager
def _cache(path):
    path = Path(path)
    if os.getuid() == 0 or not path.is_absolute() or path.resolve() != path:
        raise AcquisitionError('unsafe_cache_directory')
    path.mkdir(mode=0o700, exist_ok=True)
    directory = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        info = os.fstat(directory)
        if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
            raise AcquisitionError('unsafe_cache_directory')
        yield directory
    finally:
        os.close(directory)


def acquire(record, cache, *, consent, canceled=lambda: False, progress=lambda done, total: None,
            reserve_bytes=1024**3, _transport=_open):
    """Resume a private partial; publish only exact size+SHA256 verified bytes.

    consent must name this artifact, license and network decision. It is supplied
    by an explicit local action, never by model output or downloaded content.
    _transport is an internal deterministic-test seam, not profile configuration.
    No automatic retries. Cancellation leaves the owned partial for explicit resume.
    """
    if not isinstance(record, dict) or not re.fullmatch(r'[0-9a-f]{64}', record.get('sha256', '')) or \
       type(record.get('bytes')) is not int or not 0 < record['bytes'] <= 128 * 1024**3 or \
       not isinstance(record.get('license'), str) or not record['license']:
        raise AcquisitionError('invalid_artifact_record')
    public_url(record.get('url'))
    sha, total = record['sha256'], record['bytes']
    if consent != {'sha256': sha, 'license': record['license'], 'network_approved': True}:
        raise AcquisitionError('acquisition_consent_required')
    if type(reserve_bytes) is not int or reserve_bytes < 0:
        raise AcquisitionError('invalid_space_reserve')
    with _cache(cache) as directory:
        with os.fdopen(_regular(directory, sha+'.lock', os.O_RDWR | os.O_CREAT), 'r+b') as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise AcquisitionError('acquisition_busy') from None
            final, part = sha+'.gguf', sha+'.part'
            try:
                fd = _regular(directory, final, os.O_RDONLY)
            except FileNotFoundError:
                fd = None
            if fd is not None:
                with os.fdopen(fd, 'rb') as existing:
                    if os.fstat(existing.fileno()).st_size != total or _digest(existing).hexdigest() != sha:
                        raise AcquisitionError('existing_artifact_conflict')
                return {'state':'verified', 'sha256':sha, 'bytes':total, 'path':str(Path(cache)/final), 'network_used':False}
            with os.fdopen(_regular(directory, part, os.O_RDWR | os.O_CREAT), 'r+b') as output:
                size = os.fstat(output.fileno()).st_size
                if size > total:
                    raise AcquisitionError('partial_size_conflict')
                digest = _digest(output)  # Never trust a stored offset/hash as authority.
                if shutil.disk_usage(cache).free < total-size+reserve_bytes:
                    raise AcquisitionError('insufficient_space')
                if canceled():
                    return {'state':'canceled', 'bytes':size, 'sha256':sha}
                used = False
                if size < total:
                    headers = {'User-Agent':'Toddy-Artifact/1'}
                    if size:
                        headers['Range'] = f'bytes={size}-'
                    request = urllib.request.Request(record['url'], headers=headers)
                    try:
                        with _transport(request) as incoming:
                            used = True
                            status = incoming.status
                            if status == 200:
                                # Server ignored Range: replace this owned partial only.
                                output.seek(0);output.truncate();size=0;digest=hashlib.sha256()
                            elif status != 206 or incoming.headers.get('Content-Range') != f'bytes {size}-{total-1}/{total}':
                                raise AcquisitionError('invalid_resume_response')
                            length = incoming.headers.get('Content-Length')
                            if length is not None and length != str(total-size):
                                raise AcquisitionError('artifact_length_mismatch')
                            if incoming.headers.get('Content-Encoding', 'identity') != 'identity':
                                raise AcquisitionError('artifact_encoding_blocked')
                            while True:
                                if canceled():
                                    output.flush();os.fsync(output.fileno())
                                    return {'state':'canceled', 'bytes':size, 'sha256':sha}
                                chunk = incoming.read(min(1024*1024, total-size+1))
                                if not chunk:
                                    break
                                if len(chunk)+size > total:
                                    raise AcquisitionError('artifact_size_exceeded')
                                output.write(chunk);digest.update(chunk);size+=len(chunk)
                                progress(size,total)
                    except AcquisitionError:
                        raise
                    except (OSError, urllib.error.URLError, http.client.HTTPException, ValueError):
                        output.flush();os.fsync(output.fileno())
                        raise AcquisitionError('artifact_transport_failed') from None
                output.flush();os.fsync(output.fileno())
                if size != total:
                    raise AcquisitionError('artifact_incomplete')
                if digest.hexdigest() != sha:
                    # Preserve the failed bytes for explicit inspect/remove, never activate.
                    raise AcquisitionError('artifact_integrity_failed')
                # Hard link publishes atomically without replacing a conflicting file.
                os.link(part, final, src_dir_fd=directory, dst_dir_fd=directory, follow_symlinks=False)
                os.unlink(part, dir_fd=directory);os.fsync(directory)
                return {'state':'verified', 'sha256':sha, 'bytes':total, 'path':str(Path(cache)/final), 'network_used':used}
