"""Explicit installed-user provider binding; no remote call, root grant or fallback."""
from contextlib import contextmanager
import fcntl
from functools import wraps
import copy
import hashlib
import os
from pathlib import Path
import re
import stat
import uuid

from .pending import SetupError,_encode,_strict
from ..connections.secret_store import ProtectedStore,CredentialError

IDS=re.compile(r'[A-Za-z0-9_-]{1,80}\Z')
REMOTE={'openai','anthropic','openrouter','openai-compatible'}


class BindingState:
    """Private nonsecret handoff; an uncertain profile apply is never replayed."""
    def __init__(self,store):self.store=store
    @contextmanager
    def exclusive(self):
        fd=os.open('.onboarding.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW|os.O_CLOEXEC,0o600,dir_fd=self.store.dirfd)
        try:
            self.store._private_regular(fd)
            try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:raise SetupError('onboarding_busy') from None
            yield
        finally:os.close(fd)
    def read(self):
        try:fd=os.open('onboarding.json',os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=self.store.dirfd)
        except FileNotFoundError:return None
        try:
            self.store._private_regular(fd);value=_strict(os.read(fd,65537))
        finally:os.close(fd)
        if not isinstance(value,dict) or type(value.get('version')) is not int or value.get('version')!=1 or value.get('state') not in {'prepared','applying','unknown','configured','failed','cleanup_required'}:
            raise SetupError('onboarding_state')
        if set(value)!={'version','state','profile_id','expected_revision','reference','adapter_id','mode','settings_sha256'} or not all(isinstance(value[key],str) and IDS.fullmatch(value[key]) for key in ('profile_id','reference')) or value['adapter_id'] not in REMOTE|{'local-llama-cpp'} or value['mode'] not in {'local','remote'} or any(not isinstance(value[key],str) or not re.fullmatch('[a-f0-9]{64}',value[key]) for key in ('expected_revision','settings_sha256')):
            raise SetupError('onboarding_state')
        return value
    def write(self,value):
        with self.store._locked():
            name='.onboarding-'+uuid.uuid4().hex
            fd=os.open(name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600,dir_fd=self.store.dirfd)
            try:
                with os.fdopen(fd,'wb',closefd=False) as stream:stream.write(_encode(value));stream.flush();os.fsync(fd)
                os.replace(name,'onboarding.json',src_dir_fd=self.store.dirfd,dst_dir_fd=self.store.dirfd);os.fsync(self.store.dirfd)
            finally:
                os.close(fd)
                try:os.unlink(name,dir_fd=self.store.dirfd)
                except FileNotFoundError:pass


class ConnectionFiles:
    def __init__(self,directory=None):
        self.directory=Path(directory) if directory else Path(os.environ.get('XDG_CONFIG_HOME') or Path.home()/'.config')/'toddy/connections'
    def open(self):
        if not self.directory.is_absolute():raise SetupError('onboarding_private_directory')
        for path in reversed((self.directory,*self.directory.parents)):
            if path.is_symlink():raise SetupError('onboarding_private_directory')
            if not path.exists():path.mkdir(mode=0o700)
        info=self.directory.stat()
        if self.directory.resolve()!=self.directory or info.st_uid!=os.getuid() or stat.S_IMODE(info.st_mode)!=0o700:
            raise SetupError('onboarding_private_directory')
        return os.open(self.directory,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
    def write(self,reference,settings):
        if not IDS.fullmatch(reference):raise SetupError('onboarding_reference')
        directory=self.open()
        try:
            fd=os.open(reference+'.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600,dir_fd=directory)
            try:
                with os.fdopen(fd,'wb',closefd=False) as stream:stream.write(_encode(settings));stream.flush();os.fsync(fd)
            finally:os.close(fd)
            os.fsync(directory)
        finally:os.close(directory)
    def remove(self,reference,digest):
        if not IDS.fullmatch(reference):raise SetupError('onboarding_reference')
        directory=self.open()
        try:
            try:fd=os.open(reference+'.json',os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=directory)
            except FileNotFoundError:return
            try:
                info=os.fstat(fd)
                if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or info.st_nlink!=1 or stat.S_IMODE(info.st_mode)!=0o600 or info.st_size>16384 or hashlib.sha256(os.read(fd,16385)).hexdigest()!=digest:
                    raise SetupError('onboarding_connection_drift')
            finally:os.close(fd)
            os.unlink(reference+'.json',dir_fd=directory);os.fsync(directory)
        finally:os.close(directory)


class BrokerProfile:
    """Same-UID unique-owner D-Bus transport; never autoactivates the broker."""
    def __init__(self):
        from ..ui.cli import Session
        self.session=Session()
    def selected(self):
        cap=_strict(self.session.call('GetCapabilities'))
        return self.read(cap['profile_id'])
    def read(self,profile_id):return _strict(self.session.call('GetProfileConfig','(s)',(profile_id,)))
    def validate(self,profile_id,revision,config):
        result=_strict(self.session.call('ValidateProfile','(sss)',(profile_id,revision,_encode(config).decode())))
        if result.get('valid') is not True:raise SetupError('onboarding_profile_invalid')
        return result['validated_revision']
    def apply(self,profile_id,revision,token):
        result=_strict(self.session.call('ApplyProfile','(sss)',(profile_id,revision,token)))
        if result.get('applied') is not True:raise SetupError('onboarding_apply_unknown')
        return result


def activate_agent():
    """Separate explicit action: start fixed user unit, never enable or grant root."""
    import gi
    gi.require_version('Gio','2.0')
    from gi.repository import Gio,GLib
    connection=Gio.bus_get_sync(Gio.BusType.SESSION,None)
    def bus(method,signature,values,result):
        return connection.call_sync('org.freedesktop.DBus','/org/freedesktop/DBus','org.freedesktop.DBus',method,
            GLib.Variant(signature,values),GLib.VariantType(result),Gio.DBusCallFlags.NO_AUTO_START,5000,None).unpack()[0]
    owner=bus('GetNameOwner','(s)',('org.freedesktop.systemd1',),'(s)')
    if bus('GetConnectionUnixUser','(s)',(owner,),'(u)')!=os.getuid():raise SetupError('onboarding_wrong_user_manager')
    connection.call_sync(owner,'/org/freedesktop/systemd1','org.freedesktop.systemd1.Manager','StartUnit',
        GLib.Variant('(ss)',('toddy-agent.service','fail')),GLib.VariantType('(o)'),Gio.DBusCallFlags.NO_AUTO_START,5000,None)
    return {'state':'activation_requested','root_grant':False,'model_started':False}


def serialized(method):
    @wraps(method)
    def call(self,*args,**kwargs):
        with self.state.exclusive():return method(self,*args,**kwargs)
    return call


class Onboarding:
    def __init__(self,store,*,connections=None,protected=None,broker=None):
        self.state=BindingState(store);self.connections=connections or ConnectionFiles()
        self.protected=protected or ProtectedStore();self.broker=broker
    def _broker(self):
        if self.broker is None:self.broker=BrokerProfile()
        return self.broker
    @serialized
    def bind(self,mode,settings,*,credential=None,accepted=False,expected_profile=None,expected_revision=None):
        if accepted is not True or mode not in ('local','remote'):raise SetupError('onboarding_consent_required')
        prior=self.state.read()
        if prior and prior['state'] not in {'configured','failed'}:raise SetupError('onboarding_reconciliation_required')
        self.validate_settings(mode,settings)
        if mode=='remote' and not isinstance(credential,str):raise SetupError('onboarding_credential_required')
        broker=self._broker();snapshot=broker.selected();config=copy.deepcopy(snapshot['config'])
        if expected_profile is not None and (config['profile_id']!=expected_profile or snapshot['profile_revision']!=expected_revision):raise SetupError('onboarding_profile_changed')
        reference='connection-'+uuid.uuid4().hex
        row={'version':1,'state':'prepared','profile_id':config['profile_id'],'expected_revision':snapshot['profile_revision'],
            'reference':reference,'adapter_id':settings['adapter_id'],'mode':mode,'settings_sha256':hashlib.sha256(_encode(settings)).hexdigest()}
        self.state.write(row)
        saved=False;written=False
        try:
            self.connections.write(reference,settings);written=True
            if mode=='remote':self.protected.save(row['profile_id'],reference,settings['adapter_id'],credential);saved=True
            config['provider']={'mode':mode,'adapter_id':settings['adapter_id'],'model_id':settings['model_id'],
                                'connection_ref':reference,'allow_remote_fallback':False}
            config['budgets']['remote_spending_enabled']=mode=='remote'
            config['budgets']['max_context_tokens']=min(config['budgets']['max_context_tokens'],settings.get('context_tokens',4096))
            config['budgets']['max_output_tokens']=min(config['budgets']['max_output_tokens'],settings.get('max_output_tokens',1024))
            token=broker.validate(row['profile_id'],row['expected_revision'],config)
        except Exception:
            # No ApplyProfile was issued: remove only our exact new binding.
            # A failed credential save can be unknown; preserve its reference.
            clean=written
            if written:
                try:self.connections.remove(reference,row['settings_sha256'])
                except Exception:clean=False
            if mode=='remote':
                if saved:
                    try:self.protected.remove(row['profile_id'],reference,settings['adapter_id'])
                    except Exception:clean=False
                else:clean=False
            self.state.write({**row,'state':'failed' if clean else 'cleanup_required'})
            raise SetupError('onboarding_binding_failed') from None
        self.state.write({**row,'state':'applying'})
        try:broker.apply(row['profile_id'],row['expected_revision'],token)
        except Exception:
            self.state.write({**row,'state':'unknown'})
            return {'state':'unknown','reference':reference,'no_replay':True}
        self.state.write({**row,'state':'configured'})
        return {'state':'configured','reference':reference,'root_grant':False,'provider_contacted':False,'model_started':False}
    @serialized
    def reconcile(self):
        row=self.state.read()
        if row is None:return {'state':'idle'}
        snapshot=self._broker().read(row['profile_id']);provider=snapshot['config']['provider']
        if provider.get('connection_ref')==row['reference'] and provider.get('mode')==row['mode'] and provider.get('adapter_id')==row['adapter_id']:
            self.state.write({**row,'state':'configured'});return {'state':'configured','reference':row['reference']}
        return {'state':'cleanup_required','reference':row['reference'],'no_replay':True}
    @serialized
    def cleanup(self):
        """Explicit removal only when original profile no longer references it."""
        row=self.state.read()
        if row is None:return {'state':'idle'}
        snapshot=self._broker().read(row['profile_id'])
        if snapshot['config']['provider'].get('connection_ref')==row['reference']:
            raise SetupError('onboarding_binding_in_use')
        self.connections.remove(row['reference'],row['settings_sha256'])
        if row['mode']=='remote':self.protected.remove(row['profile_id'],row['reference'],row['adapter_id'])
        self.state.write({**row,'state':'failed'})
        return {'state':'cleaned','reference':row['reference']}

    @staticmethod
    def validate_settings(mode,settings):
        if not isinstance(settings,dict) or settings.get('version')!=1 or not isinstance(settings.get('model_id'),str) or not 0<len(settings['model_id'])<=128:raise SetupError('onboarding_settings')
        if mode=='local':
            if set(settings)!={'version','adapter_id','model_id','model_path'} or settings['adapter_id']!='local-llama-cpp' or settings['model_id']!='toddy-qwen3-1.7b-q8_0':raise SetupError('onboarding_settings')
            LocalModel.eligibility()
            # The local acquisition API verifies exact private model bytes before
            # supplying this settings object; bind independently verifies again.
            verify_model(Path(settings['model_path']))
        else:
            from urllib.parse import urlsplit
            if set(settings)!={'version','adapter_id','model_id','base_url','context_tokens','max_output_tokens'} or settings['adapter_id'] not in REMOTE:raise SetupError('onboarding_settings')
            endpoint=urlsplit(settings['base_url'])
            if endpoint.scheme!='https' or not endpoint.hostname or endpoint.username or endpoint.password or endpoint.query or endpoint.fragment or len(settings['base_url'])>2048:raise SetupError('onboarding_endpoint')
            if type(settings['context_tokens']) is not int or not 512<=settings['context_tokens']<=1048576 or type(settings['max_output_tokens']) is not int or not 64<=settings['max_output_tokens']<=settings['context_tokens']:raise SetupError('onboarding_budget')


def model_contract():
    source=Path(__file__).resolve().parents[2]/'config/phase2/local-model.lock.json'
    path=source if source.is_file() else Path('/usr/share/toddy/profiles/local-model.lock.json')
    return _strict(path.read_bytes())


def verify_model(path):
    contract=model_contract();artifact=contract['model'];path=Path(path)
    if not path.is_absolute() or path.resolve()!=path:raise SetupError('onboarding_model_path')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        info=os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or info.st_nlink!=1 or stat.S_IMODE(info.st_mode)!=0o600 or info.st_size!=artifact['bytes']:raise SetupError('onboarding_model_custody')
        with os.fdopen(fd,'rb',closefd=False) as stream:
            if hashlib.file_digest(stream,'sha256').hexdigest()!=artifact['sha256']:raise SetupError('onboarding_model_integrity')
    finally:os.close(fd)
    return {'version':1,'adapter_id':'local-llama-cpp','model_id':'toddy-qwen3-1.7b-q8_0','model_path':str(path)}


class LocalModel:
    """Reuse verified user weights or explicitly acquire pinned B03 artifact."""
    def __init__(self,cache=None):
        base=Path(os.environ.get('XDG_CACHE_HOME') or Path.home()/'.cache')
        self.cache=Path(cache) if cache else base/'toddy/models'
    def prepare_cache(self):
        if not self.cache.is_absolute():raise SetupError('onboarding_model_cache')
        for path in reversed((self.cache,*self.cache.parents)):
            if path.is_symlink():raise SetupError('onboarding_model_cache')
            if not path.exists():path.mkdir(mode=0o700)
        info=self.cache.stat()
        if self.cache.resolve()!=self.cache or info.st_uid!=os.getuid() or stat.S_IMODE(info.st_mode)!=0o700:raise SetupError('onboarding_model_cache')
    @staticmethod
    def eligibility():
        from .runtime_compat import compatible,validate_installed,RUNTIME_VERSION,cpu_features
        from .native_backend import NativeBackend
        from .releases import private_metadata
        compatible()
        if NativeBackend(None).query(['llama-cpp'])!={'llama-cpp':RUNTIME_VERSION}:raise SetupError('onboarding_runtime_missing')
        validate_installed(_strict(private_metadata(Path('/usr/share/doc/llama-cpp/cpu-profile.json'))))
        from ..acquisition.choices import choose,hardware
        contract=model_contract();resources=hardware();resources['cpu_flags']=cpu_features()[1]
        needed=(contract['budgets']['proposed_model_peak_rss_mib']+512)*1024**2
        if resources['available_memory_bytes']<needed:raise SetupError('onboarding_memory_insufficient')
        return resources
    def review(self):
        from ..acquisition.choices import choose
        resources=self.eligibility();contract=model_contract()
        self.prepare_cache()
        target=self.cache/(contract['model']['sha256']+'.gguf')
        if target.exists():
            verify_model(target);state='verified_existing'
        else:
            result=choose('local',model=contract,cache=self.cache,**resources)
            if result['state']!='acquisition_consent_required':raise SetupError('onboarding_'+result['state'])
            state='acquisition_consent_required'
        return {'state':state,'model':contract['model'],'path':str(target),'network_required':state!='verified_existing',
                'automatic_cloud_fallback':False,'model_started':False}
    def download(self,*,license_accepted,network_approved,canceled=lambda:False,progress=lambda *_:None):
        review=self.review();artifact=review['model']
        if license_accepted is not True:raise SetupError('onboarding_license_required')
        if review['state']=='verified_existing':return {'state':'verified','path':review['path'],'network_used':False}
        if network_approved is not True:raise SetupError('onboarding_network_required')
        from ..acquisition.download import acquire
        return acquire(artifact,self.cache,consent={'sha256':artifact['sha256'],'license':artifact['license'],'network_approved':True},canceled=canceled,progress=progress)
    def existing(self,path,*,license_accepted):
        # Hardware/runtime eligibility is checked even when weights are reused.
        self.review()
        if license_accepted is not True:raise SetupError('onboarding_license_required')
        return verify_model(Path(path))
