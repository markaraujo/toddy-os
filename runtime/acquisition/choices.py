"""Backend setup planning only: no credential read, download, activation or spend."""
from pathlib import Path
import shutil

from download import AcquisitionError


def choose(mode, *, model=None, cpu_flags=(), memory_bytes=0, available_memory_bytes=None, cache=None,
           adapter_id=None, model_id=None, connection_ref=None, remote_consent=False):
    if mode == 'deferred':
        return {'state':'deferred', 'base_desktop_available':True, 'network_required':False,
                'remote_fallback':False}
    if mode == 'api':
        if adapter_id not in ('openai-compatible','openai','anthropic','openrouter') or \
           not all(isinstance(x,str) and 0 < len(x) <= 128 for x in (model_id,connection_ref)):
            raise AcquisitionError('invalid_api_choice')
        # References only. Secret storage and atomic profile activation are B05.
        return {'state':'ready_for_credentials' if remote_consent else 'consent_required',
                'adapter_id':adapter_id,'model_id':model_id,'connection_ref':connection_ref,
                'support':'fixture-only-live-unverified','cost_estimate':None,
                'remote_fallback':False,'network_required':True}
    if mode != 'local' or not isinstance(model,dict):
        raise AcquisitionError('invalid_backend_choice')
    runtime=model['runtime'];artifact=model['model']
    if not set(runtime['required_cpu_flags']).issubset(cpu_flags):
        return {'state':'unsupported_cpu','remote_fallback':False}
    if memory_bytes < 8*1024**3 or (available_memory_bytes is not None and available_memory_bytes < 4*1024**3):
        return {'state':'insufficient_memory','remote_fallback':False}
    if cache is None or not Path(cache).is_dir():
        raise AcquisitionError('cache_unavailable')
    if shutil.disk_usage(cache).free < artifact['bytes']+1024**3:
        return {'state':'insufficient_space','remote_fallback':False}
    return {'state':'acquisition_consent_required','sha256':artifact['sha256'],
            'bytes':artifact['bytes'],'license':artifact['license'],
            'network_required':True,'remote_fallback':False}


def hardware():
    """Actual Linux available resources for the pinned x86_64 CPU-only profile."""
    flags=set()
    for line in Path('/proc/cpuinfo').read_text().splitlines():
        if line.startswith('flags'):
            flags.update(line.split(':',1)[1].split())
    memory={line.split(':',1)[0]:int(line.split()[1])*1024 for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith(('MemTotal:','MemAvailable:'))}
    return {'cpu_flags':flags,'memory_bytes':memory['MemTotal'],'available_memory_bytes':memory['MemAvailable']}
