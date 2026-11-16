"""Explicit native package review/transaction UI independent of optional broker."""
from concurrent.futures import ThreadPoolExecutor

from ..setup.acquisition import AcquisitionClient
from ..setup.pending import SetupError


class AcquisitionController:
    """At most one primary job and one explicitly requested Stop authorization."""
    def __init__(self,store,changed,*,client=None,schedule=None):
        if schedule is None:
            from gi.repository import GLib
            schedule=GLib.idle_add
        self.schedule=schedule;self.changed=changed;self.closed=False
        self.busy=False;self.stopping=False;self.operation=None;self.review=None
        self.status='idle';self.phase=None;self.cancel_status=None
        self.pool=ThreadPoolExecutor(max_workers=1,thread_name_prefix='toddy-acquisition')
        self.cancel_pool=ThreadPoolExecutor(max_workers=1,thread_name_prefix='toddy-acquisition-stop')
        self.client=client or AcquisitionClient(store,progress=self._progress)
        self._latest_progress=None;self._progress_pending=False

    def _progress(self,value):
        # One scheduled update regardless of producer speed. No raw diagnostics.
        self._latest_progress=value.get('phase')
        if not self._progress_pending:
            self._progress_pending=True;self.schedule(self._show_progress)

    def _show_progress(self):
        self._progress_pending=False
        if not self.closed:
            self.phase=self._latest_progress;self.changed()
        return False

    def _start(self,operation,work):
        if self.busy or self.closed:raise SetupError('acquisition_busy')
        self.busy=True;self.operation=operation;self.status='working';self.phase=None
        self.changed()
        def run():
            try:value=work()
            except Exception:value={'state':'outcome_unknown' if operation!='review' else 'unavailable','ok':False}
            self.schedule(done,value)
        def done(value):
            if not self.closed:
                self.busy=False;self.operation=None
                if operation=='review':
                    self.review=value;self.status=value.get('state','unavailable')
                else:
                    self.review=None
                    self.status=value.get('state','outcome_unknown' if value.get('ok') is not True else 'unavailable')
                    if value.get('code')=='owner_authorization_canceled':self.status='authorization_canceled'
                self.changed()
            return False
        self.pool.submit(run)

    def inspect(self,release_id):
        self.review=None
        self._start('review',lambda:self.client.review(release_id))

    def install(self,*,accepted_terms):
        review=self.review
        if not review or accepted_terms is not True:raise SetupError('acquisition_review_required')
        self._start('install',lambda:self.client.install(review,accepted_terms=True))

    def action(self,action):
        if action not in ('status','reconcile'):raise SetupError('acquisition_action')
        self._start(action,lambda:self.client.action(action))

    def stop(self):
        if self.closed or self.stopping:raise SetupError('acquisition_busy')
        if not self.busy or self.operation!='install':raise SetupError('acquisition_unknown')
        self.stopping=True;self.cancel_status='working';self.changed()
        def run():
            try:
                value=self.client.request_cancel()
                status='stop_requested' if value.get('ok') is True else 'authorization_canceled'
            except Exception:status='outcome_unknown'
            self.schedule(done,status)
        def done(status):
            if not self.closed:
                self.stopping=False;self.cancel_status=status;self.changed()
            return False
        self.cancel_pool.submit(run)

    def close(self):
        # The owner window keeps the private store alive until the safe boundary.
        if self.busy or self.stopping:return False
        self.closed=True
        self.pool.shutdown(wait=False,cancel_futures=True)
        self.cancel_pool.shutdown(wait=False,cancel_futures=True)
        return True


def panel(window,page):
    """Build a native GTK panel; importing the controller needs no GUI runtime."""
    from gi.repository import Adw,Gtk
    text=window.model.text
    group=Adw.PreferencesGroup(title=text('acquire.title'),description=text('acquire.notice'))
    page.append(group)
    selector=Gtk.DropDown.new_from_strings([text('acquire.agent'),text('acquire.local'),text('acquire.combined')])
    group.add(selector)
    detail=Gtk.Label(wrap=True,xalign=0,selectable=True)
    group.add(detail)
    terms=Gtk.TextView(editable=False,cursor_visible=False,wrap_mode=Gtk.WrapMode.WORD_CHAR)
    scroll=Gtk.ScrolledWindow(min_content_height=90,max_content_height=180)
    scroll.set_child(terms);group.add(scroll)
    consent=Gtk.CheckButton(label=text('acquire.consent'));group.add(consent)
    status=Gtk.Label(wrap=True,xalign=0);status.set_accessible_role(Gtk.AccessibleRole.STATUS);group.add(status)
    controls=Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE,max_children_per_line=3,min_children_per_line=1,column_spacing=8,row_spacing=8);group.add(controls)
    buttons={}
    def changed():
        row=controller.review or {}
        status_key='working' if controller.busy else controller.status
        known={'idle','working','review_required','packages_present','reconciliation_required','unavailable','installed','deferred','canceled','failed','needs_reconciliation','outcome_unknown','authorization_canceled'}
        status.set_text(text('acquire.'+(status_key if status_key in known else 'working')))
        if controller.phase in ('prepared','downloading','installing'):status.set_text(status.get_text()+'\n'+text('acquire.phase_'+controller.phase))
        if controller.cancel_status:status.set_text(status.get_text()+'\n'+text('acquire.'+controller.cancel_status))
        selector.set_sensitive(not controller.busy and not controller.stopping)
        consent.set_sensitive(not controller.busy and row.get('can_install') is True)
        buttons['review'].set_sensitive(not controller.busy and not controller.stopping)
        buttons['install'].set_sensitive(not controller.busy and not controller.stopping and row.get('can_install') is True and consent.get_active())
        buttons['stop'].set_sensitive(controller.busy and controller.operation=='install' and not controller.stopping)
        for key in ('status','reconcile'):buttons[key].set_sensitive(not controller.busy and not controller.stopping)
        if row.get('packages'):
            packages='\n'.join(p['name']+' '+p['version']+' ('+p['architecture']+')' for p in row['packages'])
            preview='\n'+text('acquire.preview') if row.get('preview_only') else ''
            detail.set_text(packages+'\n'+text('acquire.sizes').format(download=row['download_bytes'],installed=row['installed_bytes'])+'\n'+row['repository_origin']+preview)
            terms.get_buffer().set_text(row.get('terms_text',''))
        else:detail.set_text(text('acquire.empty'));terms.get_buffer().set_text('')
    controller=AcquisitionController(window.model.store,changed)
    def invoke(action):
        try:
            if action=='review':
                consent.set_active(False);controller.cancel_status=None
                controller.inspect(('agent-backend','local-runtime','agent-local')[selector.get_selected()])
            elif action=='install':controller.install(accepted_terms=consent.get_active());consent.set_active(False)
            elif action=='stop':controller.stop()
            else:controller.action(action)
        except SetupError:status.set_text(text('acquire.unavailable'))
    for key in ('review','install','stop','status','reconcile'):
        button=Gtk.Button(label=text('acquire.button_'+key))
        button.connect('clicked',lambda _,action=key:invoke(action));controls.insert(button,-1);buttons[key]=button
    selector.connect('notify::selected',lambda *_: (consent.set_active(False),setattr(controller,'review',None),changed()))
    consent.connect('toggled',lambda *_:changed())
    changed()
    return controller
