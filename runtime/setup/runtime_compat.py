"""Frozen optional CPU runtime compatibility; no model/download/activation."""
import os
from pathlib import Path

from .pending import SetupError,_encode

CPU_FLAGS = ['sse4_2','avx','avx2','fma','f16c','bmi2']
RUNTIME_VERSION = '0.9.0-1+toddy1'
RUNTIME_ARCHIVE_SHA256 = 'c528b72c8a9c8a6182fabf82317e71129fed3d63516b25a02c451a5ed15c9287'
RUNTIME_PROFILE = {'id':'llama-cpu-avx2-v090','architecture':'x86_64','package':'llama-cpp',
    'version':RUNTIME_VERSION,'source_commit':'cd959bae99ff4bed22bef2604f45241c09bbb8c8',
    'source_sha256':'fbe74146a3cdc00f706773eb233bc4aedb7d8c3c7e2122440e492a99c1ec5a76',
    'cpu_flags':CPU_FLAGS,'gpu':False,'native_cpu_optimization':False,'subprocess_tools':False,
    'https_client':False,'weights_in_package':False,'automatic_cloud_fallback':False}
INSTALLED_PROFILE = {'schema_version':1,'cpu_flags':CPU_FLAGS,
    'source_commit':RUNTIME_PROFILE['source_commit'],'gpu':False,'native_cpu_optimization':False,
    'subprocess_tools':False,'https_client':False,'weights_in_package':False}


def cpu_features():
    sets=[set(line.split(':',1)[1].split()) for line in Path('/proc/cpuinfo').read_text().splitlines()
          if line.startswith('flags') and ':' in line]
    return os.uname().machine,set.intersection(*sets) if sets else set()


def compatible(*,hardware=cpu_features):
    architecture,flags=hardware()
    if architecture!='x86_64' or not set(CPU_FLAGS)<=set(flags):
        raise SetupError('native_runtime_cpu_unsupported')
    return {'runtime_compatible':True,'runtime_activated':False,'model_required':True,
            'model_installed':False,'automatic_cloud_fallback':False}


def validate_installed(value):
    if not isinstance(value,dict) or _encode(value)!=_encode(INSTALLED_PROFILE):
        raise SetupError('native_runtime_profile_changed')
