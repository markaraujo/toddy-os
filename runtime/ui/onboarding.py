"""Guided backend setup; explicit activation, protected API and pinned local model."""
from concurrent.futures import ThreadPoolExecutor
import threading

from ..setup.onboarding import Onboarding,LocalModel,activate_agent
from ..setup.pending import SetupError


class OnboardingController:
    def __init__(self,store,changed,*,api=None,local=None,schedule=None):
        if schedule is None:
            from gi.repository import GLib
            schedule=GLib.idle_add
        self.api=api or Onboarding(store);self.local=local or LocalModel()
        self.changed=changed;self.schedule=schedule;self.busy=False;self.closed=False
        self.status='idle';self.result=None;self.operation=None;self.cancel=threading.Event()
        self.pool=ThreadPoolExecutor(max_workers=1,thread_name_prefix='toddy-onboarding')
        self.progress=None;self._progress_pending=False
    def start(self,operation,work):
        if self.busy or self.closed:raise SetupError('onboarding_busy')
        self.busy=True;self.operation=operation;self.status='working';self.cancel.clear();self.changed()
        def run():
            try:value=work()
            except Exception:value={'state':'unavailable'}
            self.schedule(done,value)
        def done(value):
            if not self.closed:
                self.busy=False;self.operation=None;self.result=value;self.status=value.get('state','unavailable');self.changed()
            return False
        self.pool.submit(run)
    def downloading(self,done,total):
        self.progress=(done,total)
        if not self._progress_pending:
            self._progress_pending=True;self.schedule(self._show_progress)
    def _show_progress(self):
        self._progress_pending=False
        if not self.closed:self.changed()
        return False
    def stop(self):
        if not self.busy or self.operation!='download':raise SetupError('onboarding_not_download')
        self.cancel.set()
    def close(self):
        if self.busy:return False
        self.closed=True;self.pool.shutdown(wait=False,cancel_futures=True);return True


def panel(window,page):
    from gi.repository import Adw,Gtk
    text=window.model.text
    group=Adw.PreferencesGroup(title=text('onboard.title'),description=text('onboard.notice'));page.append(group)
    profile_note=Gtk.Label(wrap=True,xalign=0);group.add(profile_note)
    selector=Gtk.DropDown.new_from_strings([text('setup.later_choice'),text('setup.api_choice'),text('setup.local_choice')]);group.add(selector)
    activate=Gtk.Button(label=text('onboard.activate'));group.add(activate)
    remote=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=8)
    adapters=Gtk.DropDown.new_from_strings(['OpenAI','Anthropic','OpenRouter','OpenAI-compatible']);remote.append(adapters)
    endpoint=Gtk.Entry(placeholder_text='https://api.example/v1',max_length=2048);remote.append(endpoint)
    model=Gtk.Entry(placeholder_text=text('onboard.model_id'),max_length=128);remote.append(model)
    password=Gtk.PasswordEntry(show_peek_icon=True);password.get_delegate().set_max_length(4096);password.get_delegate().set_enable_undo(False);remote.append(password)
    remote_consent=Gtk.CheckButton(label=text('onboard.remote_consent'));remote.append(remote_consent)
    remote_apply=Gtk.Button(label=text('onboard.bind_api'));remote.append(remote_apply);group.add(remote)
    local=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=8)
    local_note=Gtk.Label(wrap=True,xalign=0,selectable=True,label=text('onboard.local_notice'));local.append(local_note)
    review=Gtk.Button(label=text('onboard.review_model'));local.append(review)
    path=Gtk.Entry(placeholder_text=text('onboard.existing_path'),max_length=4096);local.append(path)
    license_consent=Gtk.CheckButton(label=text('onboard.license_consent'));local.append(license_consent)
    network_consent=Gtk.CheckButton(label=text('onboard.network_consent'));local.append(network_consent)
    download=Gtk.Button(label=text('onboard.download'));local.append(download)
    bind_consent=Gtk.CheckButton(label=text('onboard.local_consent'));local.append(bind_consent)
    local_apply=Gtk.Button(label=text('onboard.bind_local'));local.append(local_apply);group.add(local)
    status=Gtk.Label(wrap=True,xalign=0);status.set_accessible_role(Gtk.AccessibleRole.STATUS);group.add(status)
    controls=Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE,max_children_per_line=2,min_children_per_line=1,column_spacing=8,row_spacing=8);group.add(controls)
    buttons={}
    def changed():
        mode=selector.get_selected();remote.set_visible(mode==1);local.set_visible(mode==2)
        caps=getattr(getattr(window,'client',None),'capabilities',None)
        profile_note.set_text(text('onboard.profile_selected').format(profile=caps['profile_id']) if caps else text('onboard.profile_unavailable'))
        selector.set_sensitive(not controller.busy);activate.set_sensitive(not controller.busy and mode!=0)
        remote_apply.set_sensitive(not controller.busy and bool(caps) and remote_consent.get_active())
        for widget in (adapters,endpoint,model,password,remote_consent,path,license_consent,network_consent,bind_consent,review):widget.set_sensitive(not controller.busy)
        download.set_sensitive(not controller.busy and controller.result is not None and controller.result.get('model') is not None and license_consent.get_active() and network_consent.get_active())
        local_apply.set_sensitive(not controller.busy and bool(caps) and license_consent.get_active() and bind_consent.get_active() and bool(path.get_text()))
        for action,button in buttons.items():button.set_sensitive(not controller.busy if action!='stop' else controller.busy and controller.operation=='download')
        known={'idle','working','activation_requested','configured','unknown','cleanup_required','cleaned','unavailable','acquisition_consent_required','verified_existing','verified','canceled','deferred'}
        state=controller.status if controller.status in known else 'unavailable'
        status.set_text(text('onboard.'+state))
        if controller.busy and controller.operation=='download' and controller.progress:
            status.set_text(status.get_text()+'\n'+text('onboard.progress').format(done=controller.progress[0],total=controller.progress[1]))
        result=controller.result or {}
        if 'model' in result:
            artifact=result['model'];local_note.set_text(text('onboard.local_detail').format(size=artifact['bytes'],license=artifact['license'],url=artifact['license_url'],sha=artifact['sha256']))
            if path.get_text()!=result['path']:path.set_text(result['path'])
        elif result.get('state')=='verified' and result.get('path') and path.get_text()!=result['path']:path.set_text(result['path'])
    controller=OnboardingController(window.model.store,changed)
    def perform(action):
        try:
            if action=='activate':controller.start(action,activate_agent)
            elif action=='remote':
                caps=getattr(getattr(window,'client',None),'capabilities',None)
                if not caps:raise SetupError('onboarding_profile_unavailable')
                expected_profile=caps['profile_id'];expected_revision=caps['profile_revision']
                settings={'version':1,'adapter_id':('openai','anthropic','openrouter','openai-compatible')[adapters.get_selected()],
                    'model_id':model.get_text().strip(),'base_url':endpoint.get_text().strip(),'context_tokens':4096,'max_output_tokens':1024}
                secret=password.get_text();password.set_text('')
                accepted=remote_consent.get_active();remote_consent.set_active(False)
                controller.start(action,lambda:controller.api.bind('remote',settings,credential=secret,accepted=accepted,expected_profile=expected_profile,expected_revision=expected_revision))
            elif action=='review':
                license_consent.set_active(False);network_consent.set_active(False);bind_consent.set_active(False)
                controller.start(action,controller.local.review)
            elif action=='download':
                accepted=license_consent.get_active();network=network_consent.get_active()
                controller.start(action,lambda:controller.local.download(license_accepted=accepted,network_approved=network,canceled=controller.cancel.is_set,progress=controller.downloading))
                network_consent.set_active(False)
            elif action=='local':
                caps=getattr(getattr(window,'client',None),'capabilities',None)
                if not caps:raise SetupError('onboarding_profile_unavailable')
                expected_profile=caps['profile_id'];expected_revision=caps['profile_revision']
                target=path.get_text();license_ok=license_consent.get_active();accepted=bind_consent.get_active();bind_consent.set_active(False)
                def bind():
                    settings=controller.local.existing(target,license_accepted=license_ok)
                    return controller.api.bind('local',settings,accepted=accepted,expected_profile=expected_profile,expected_revision=expected_revision)
                controller.start(action,bind)
            elif action=='stop':controller.stop()
            elif action=='later':
                # Deferral saves only the existing harmless invitation intent.
                # It does not silently alter an already configured profile.
                window.model.defer();controller.status='deferred';changed()
            else:controller.start(action,getattr(controller.api,action))
        except (SetupError,ValueError,OSError):status.set_text(text('onboard.unavailable'))
    activate.connect('clicked',lambda *_:perform('activate'))
    remote_apply.connect('clicked',lambda *_:perform('remote'))
    review.connect('clicked',lambda *_:perform('review'))
    download.connect('clicked',lambda *_:perform('download'))
    local_apply.connect('clicked',lambda *_:perform('local'))
    for action in ('stop','reconcile','cleanup','later'):
        button=Gtk.Button(label=text('onboard.button_'+action));button.connect('clicked',lambda _,action=action:perform(action));controls.insert(button,-1);buttons[action]=button
    for check in (remote_consent,license_consent,network_consent,bind_consent):check.connect('toggled',lambda *_:changed())
    path.connect('changed',lambda *_:changed())
    def selected(*_):
        password.set_text('');remote_consent.set_active(False);license_consent.set_active(False);network_consent.set_active(False);bind_consent.set_active(False);changed()
    selector.connect('notify::selected',selected)
    changed()
    controller.sync=changed
    controller.clear_password=lambda:password.set_text('')
    return controller
