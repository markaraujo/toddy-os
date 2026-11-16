"""Explicit local-use integrity/license binding; no download or redistribution grant."""
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import re
import stat
from urllib.parse import urlsplit

HEX = re.compile(r'[0-9a-f]{64}\Z')


class VoiceError(ValueError):
    """Sanitized bounded state/error code; never include transcripts or raw stderr."""


@dataclass(frozen=True)
class Consent:
    artifact_sha256: str
    license_sha256: str
    purpose: str = 'local-speech-use'


@dataclass(frozen=True)
class Artifact:
    artifact_id: str
    kind: str
    path: Path
    size: int
    sha256: str
    source_url: str
    version: str
    license_id: str
    license_path: Path
    license_sha256: str
    review: str
    languages: tuple

    def validate_metadata(self):
        if self.kind not in {'engine','stt-model','tts-model','tts-config'} or \
                not isinstance(self.artifact_id,str) or not re.fullmatch(r'[a-z][a-z0-9-]{0,63}',self.artifact_id) or \
                type(self.size) is not int or not 0 < self.size <= 4*1024**3 or \
                not isinstance(self.sha256,str) or not HEX.fullmatch(self.sha256) or \
                not isinstance(self.license_sha256,str) or not HEX.fullmatch(self.license_sha256) or \
                not isinstance(self.version,str) or not 0 < len(self.version) <= 128 or \
                not isinstance(self.license_id,str) or not 0 < len(self.license_id) <= 128 or \
                self.review != 'reviewed-local-use' or not isinstance(self.languages,(tuple,list)) or \
                not self.languages or not isinstance(self.source_url,str) or len(self.source_url)>2048 or \
                any(language not in ('en','pt-BR') for language in self.languages):
            raise VoiceError('artifact_metadata')
        source=urlsplit(self.source_url)
        if source.scheme!='https' or not source.hostname or source.username or source.password or source.fragment:
            raise VoiceError('artifact_source')
        return self

    def verify(self, consent):
        self.validate_metadata()
        if consent != Consent(self.sha256,self.license_sha256):
            raise VoiceError('artifact_consent_required')
        self._hash(self.license_path,self.license_sha256,maximum=65536)
        self._hash(self.path,self.sha256,maximum=self.size,expected_size=self.size,
                   executable=self.kind=='engine')
        return str(self.path)

    @staticmethod
    def _hash(path, expected, *, maximum, expected_size=None, executable=False):
        path=Path(path)
        if not path.is_absolute():
            raise VoiceError('artifact_path')
        for component in (path,*path.parents):
            if component.is_symlink():
                raise VoiceError('artifact_path')
        try:
            fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
            try:
                info=os.fstat(fd)
                if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1 or info.st_uid not in (0,os.getuid()) or \
                        info.st_mode & 0o022 or info.st_size>maximum or \
                        (expected_size is not None and info.st_size!=expected_size) or \
                        (executable and not os.access(path,os.X_OK)):
                    raise VoiceError('artifact_file')
                digest=hashlib.sha256()
                total=0
                while chunk:=os.read(fd,1024*1024):
                    total+=len(chunk)
                    if total>maximum:
                        raise VoiceError('artifact_size')
                    digest.update(chunk)
                if digest.hexdigest()!=expected or (expected_size is not None and total!=expected_size):
                    raise VoiceError('artifact_integrity')
            finally:
                os.close(fd)
        except OSError as exc:
            raise VoiceError('artifact_unavailable') from exc
