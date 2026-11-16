"""Native setup/conversation; optional broker and protected store fail closed."""
import argparse
import json
import uuid
from pathlib import Path
import os
import sys

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Adw, Gio, Gtk

from ..setup.pending import SetupError
from .model import SetupModel, state_directory
from .bridge import TaskClient
from .credentials import CredentialsClient
from ..connections.secret_store import CredentialError
from ..shared.json import strict_json
from .task_state import TERMINAL

APP_ID = 'io.github.markaraujo.Toddy'


class SetupWindow(Adw.ApplicationWindow):
    def __init__(self, application, model):
        super().__init__(application=application, title='Toddy', default_width=680, default_height=640)
        self.model = model
        self.set_icon_name(APP_ID)
        self.set_size_request(360, 360)
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        header = Adw.HeaderBar()
        outer.append(header)
        self.stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE)
        switcher = Gtk.StackSwitcher(stack=self.stack)
        header.set_title_widget(switcher)
        self.toast = Adw.ToastOverlay()
        self.toast.set_child(self.stack)
        outer.append(self.toast)
        self.stack.set_vexpand(True)
        self.set_content(outer)
        self._profile_rendered_revision=None
        self._profile_dirty=False
        self._setting_profile=False
        self._profile_force_reload=True
        self._setup()
        self._conversation()
        self._software()
        self._profiles()
        self.credentials=CredentialsClient(self._credential_changed)
        self.client = TaskClient(self._task_changed)
        self.connect('close-request', self._close)

    def _page(self, name, title):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20,
                      margin_top=20, margin_bottom=24, margin_start=20, margin_end=20)
        clamp = Adw.Clamp(maximum_size=640)
        clamp.set_child(box)
        scroll = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER)
        scroll.set_child(clamp)
        self.stack.add_titled(scroll, name, title)
        return box

    def _label(self, text):
        label = Gtk.Label(label=text, wrap=True, xalign=0)
        label.set_selectable(True)
        return label

    def _setup(self):
        text = self.model.text
        page = self._page('setup', text('setup.title'))
        title = self._label(text('setup.title'))
        title.add_css_class('title-1')
        page.append(title)
        page.append(self._label(text('setup.deferred')))
        backend = Adw.PreferencesGroup(title=text('setup.backend_heading'),
                                       description=text('setup.intent_only'))
        row = Adw.ActionRow(title=text('setup.backend_heading'))
        labels = [text('setup.later_choice'), text('setup.api_choice'), text('setup.local_choice')]
        self.backend = Gtk.DropDown.new_from_strings(labels)
        self.backend.set_valign(Gtk.Align.CENTER)
        self.backend.set_selected(('later', 'api', 'local').index(self.model.manifest['ai_choice']))
        row.add_suffix(self.backend)
        row.set_activatable_widget(self.backend)
        backend.add(row)
        page.append(backend)
        self.save = Gtk.Button(label=text('setup.save_intent'))
        self.save.set_halign(Gtk.Align.START)
        self.save.connect('clicked', self._save)
        page.append(self.save)
        native = Adw.PreferencesGroup(title=text('task.native_heading'),
                                     description=text('task.native_description'))
        self.task_note = Gtk.Entry(placeholder_text=text('task.note'), max_length=4096)
        native.add(self.task_note)
        controls = Gtk.Box(spacing=12, margin_top=8, margin_bottom=8)
        self.run_button = Gtk.Button(label=text('task.inspect_system'))
        self.run_button.set_sensitive(False)
        self.run_button.connect('clicked', self._run_native)
        self.stop_button = Gtk.Button(label=text('task.stop_action'))
        self.stop_button.set_sensitive(False)
        self.stop_button.connect('clicked', self._stop_native)
        controls.append(self.run_button)
        controls.append(self.stop_button)
        refresh = Gtk.Button(label=text('task.refresh_service'))
        refresh.connect('clicked', lambda *_: self.client.recheck())
        controls.append(refresh)
        native.add(controls)
        self.task_status = self._label(text('task.service_absent'))
        self.task_status.set_accessible_role(Gtk.AccessibleRole.STATUS)
        native.add(self.task_status)
        page.append(native)
        self.defer_button = Gtk.Button(label=text('setup.later_choice'))
        self.defer_button.add_css_class('suggested-action')
        self.defer_button.connect('clicked', self._defer)
        page.append(self.defer_button)
        self.status = self._label(text('setup.intent_saved') if
                                  self.model.manifest['invitation_dismissed'] else text('setup.intent_only'))
        self.status.set_accessible_role(Gtk.AccessibleRole.STATUS)
        page.append(self.status)
        self._credential_form(page)

    def _conversation(self):
        text=self.model.text
        page=self._page('conversation',text('conversation.title'))
        self.conversation_status=self._label(text('setup.tasks_unavailable'))
        self.conversation_status.set_accessible_role(Gtk.AccessibleRole.STATUS)
        page.append(self.conversation_status)
        self.history_status=self._label(text('conversation.window_history'))
        page.append(self.history_status)
        self.conversation_view=Gtk.TextView(editable=False,cursor_visible=False,
                                            wrap_mode=Gtk.WrapMode.WORD_CHAR)
        self.conversation_buffer=self.conversation_view.get_buffer()
        output=Gtk.ScrolledWindow(min_content_height=200,max_content_height=420)
        output.set_child(self.conversation_view)
        page.append(output)
        self.entry=Gtk.Entry(placeholder_text=text('assistant.welcome'),max_length=4096)
        self.entry.set_sensitive(False)
        self.entry.connect('activate',self._send_conversation)
        page.append(self.entry)
        self.remote_consent=Gtk.CheckButton(label=text('conversation.remote_consent'))
        self.remote_consent.set_active(False)
        self.remote_consent.set_visible(False)
        self.remote_consent.connect('toggled',lambda *_:self._task_changed())
        page.append(self.remote_consent)
        controls=Gtk.Box(spacing=12)
        self.send_button=Gtk.Button(label=text('conversation.send'))
        self.send_button.add_css_class('suggested-action')
        self.send_button.set_sensitive(False)
        self.send_button.connect('clicked',self._send_conversation)
        self.conversation_stop=Gtk.Button(label=text('task.stop_action'))
        self.conversation_stop.set_sensitive(False)
        self.conversation_stop.connect('clicked',self._stop_native)
        controls.append(self.send_button)
        controls.append(self.conversation_stop)
        page.append(controls)

    def _send_conversation(self,*_):
        try:
            self.client.submit_text(self.entry.get_text().strip(),
                                    remote_consent=self.remote_consent.get_active())
            self.entry.set_text('')
            self.remote_consent.set_active(False)
        except ValueError:
            self.conversation_status.set_text(self.model.text('conversation.unavailable'))

    def _profiles(self):
        text=self.model.text
        page=self._page('profile',text('profile.settings_title'))
        page.append(self._label(text('profile.settings_notice')))
        self.profile_status=self._label(text('profile.settings_unavailable'))
        page.append(self.profile_status)
        self.profile_editor=Gtk.TextView(editable=False,monospace=True,
                                        wrap_mode=Gtk.WrapMode.WORD_CHAR)
        self.profile_buffer=self.profile_editor.get_buffer()
        self.profile_buffer.connect('changed',self._profile_edited)
        scroll=Gtk.ScrolledWindow(min_content_height=240,max_content_height=460)
        scroll.set_child(self.profile_editor)
        page.append(scroll)
        controls=Gtk.Box(spacing=12)
        self.profile_validate=Gtk.Button(label=text('profile.validate'))
        self.profile_validate.set_sensitive(False)
        self.profile_validate.connect('clicked',self._validate_profile)
        self.profile_apply=Gtk.Button(label=text('profile.apply'))
        self.profile_apply.set_sensitive(False)
        self.profile_apply.connect('clicked',self._apply_profile)
        reload=Gtk.Button(label=text('setup.reload'))
        reload.connect('clicked',self._reload_profile)
        for widget in (self.profile_validate,self.profile_apply,reload): controls.append(widget)
        page.append(controls)
        self.previous_revisions=[]
        self.restore_choices=Gtk.DropDown.new_from_strings([])
        page.append(self.restore_choices)
        self.profile_restore=Gtk.Button(label=text('profile.restore'))
        self.profile_restore.set_sensitive(False)
        self.profile_restore.connect('clicked',self._restore_profile)
        page.append(self.profile_restore)

    def _profile_edited(self,*_):
        if not self._setting_profile and hasattr(self,'client'):
            self._profile_dirty=True
            self.client.invalidate_profile_stage()
            self._task_changed()

    def _reload_profile(self,*_):
        self._profile_force_reload=True
        self._profile_dirty=False
        self.client.refresh_profile()

    def _validate_profile(self,*_):
        try:
            if self.client.profile is None or self._profile_rendered_revision!=self.client.profile['profile_revision']:
                raise ValueError('stale_profile')
            start,end=self.profile_buffer.get_bounds()
            encoded=self.profile_buffer.get_text(start,end,True)
            strict_json(encoded.encode())
            self.client.validate_profile(encoded)
        except (ValueError,UnicodeError):
            self.profile_status.set_text(self.model.text('profile.invalid_revision'))

    def _apply_profile(self,*_):
        try:
            self._profile_force_reload=True
            self._profile_dirty=False
            self.client.apply_profile()
        except ValueError:
            self.profile_status.set_text(self.model.text('profile.invalid_revision'))

    def _restore_profile(self,*_):
        try:
            index=self.restore_choices.get_selected()
            if index>=len(self.previous_revisions): raise ValueError('no_revision')
            self._profile_force_reload=True
            self._profile_dirty=False
            self.client.restore_profile(self.previous_revisions[index])
        except ValueError:
            self.profile_status.set_text(self.model.text('profile.invalid_revision'))

    def _credential_form(self,page):
        text=self.model.text
        group=Adw.PreferencesGroup(title=text('credentials.title'),
                                  description=text('credentials.notice'))
        self.credential_adapter=Gtk.DropDown.new_from_strings(['OpenAI','Anthropic','OpenRouter','OpenAI-compatible'])
        group.add(self.credential_adapter)
        self.credential_ref=Gtk.Entry(placeholder_text=text('credentials.reference'),max_length=80)
        self.credential_ref.set_text('connection-'+uuid.uuid4().hex)
        group.add(self.credential_ref)
        self.password=Gtk.PasswordEntry(show_peek_icon=True)
        self.password.get_delegate().set_max_length(4096)
        self.password.get_delegate().set_enable_undo(False)
        self.password.set_hexpand(True)
        group.add(self.password)
        controls=Gtk.Box(spacing=12,margin_top=8,margin_bottom=8)
        self.credential_save=Gtk.Button(label=text('credentials.save'))
        self.credential_save.connect('clicked',self._save_credential)
        self.credential_remove=Gtk.Button(label=text('credentials.remove'))
        self.credential_remove.connect('clicked',self._remove_credential)
        controls.append(self.credential_save)
        controls.append(self.credential_remove)
        group.add(controls)
        self.credential_status=self._label(text('credentials.notice'))
        group.add(self.credential_status)
        page.append(group)

    def _credential_arguments(self):
        profile=self.client.capabilities['profile_id'] if self.client.capabilities else 'toddy-default'
        adapter=('openai','anthropic','openrouter','openai-compatible')[self.credential_adapter.get_selected()]
        return profile,self.credential_ref.get_text(),adapter

    def _save_credential(self,*_):
        secret=self.password.get_text()
        self.password.set_text('')
        try:
            self.credentials.save(*self._credential_arguments(),secret)
            self.credential_save.set_sensitive(False)
            self.credential_remove.set_sensitive(False)
            self.credential_status.set_text(self.model.text('credentials.working'))
        except CredentialError:
            self.credential_status.set_text(self.model.text('credentials.failed'))

    def _remove_credential(self,*_):
        self.password.set_text('')
        try:
            self.credentials.remove(*self._credential_arguments())
            self.credential_save.set_sensitive(False)
            self.credential_remove.set_sensitive(False)
            self.credential_status.set_text(self.model.text('credentials.working'))
        except CredentialError:
            self.credential_status.set_text(self.model.text('credentials.failed'))

    def _credential_changed(self,status,reference):
        self.credential_save.set_sensitive(True)
        self.credential_remove.set_sensitive(True)
        if status=='credential_saved':
            message=self.model.text('credentials.saved').format(reference=reference)
        elif status=='credential_removed':
            message=self.model.text('credentials.removed')
        elif status=='credential_store_locked':
            message=self.model.text('setup.keyring_locked').format(provider=self.model.text('setup.api_choice'))
        elif status=='credential_store_unavailable':
            message=self.model.text('setup.keyring_unavailable')
        else:
            message=self.model.text('credentials.failed')
        self.credential_status.set_text(message)

    def _software(self):
        text = self.model.text
        page = self._page('software', text('software.title'))
        page.append(self._label(text('software.review')))
        page.append(self._label(text('software.catalog_unavailable')))
        group = Adw.PreferencesGroup()
        for candidate in self.model.software():
            subtitle = candidate['description'] + '\n' + candidate['status']
            if candidate['pending']:
                subtitle += '\n' + text('software.retained_pending')
            row = Adw.ActionRow(title=candidate['name'], subtitle=subtitle)
            row.set_use_markup(False)
            # No checkbox, Install action or click-through to an untrusted origin.
            group.add(row)
        page.append(group)

    def _close(self, *_):
        self.password.set_text('')
        self.credentials.close()
        self.client.close()
        return False

    def _task_changed(self):
        client = self.client
        state = client.state
        snapshot = state.snapshot
        text = self.model.text
        active = state.task_id is not None and (snapshot is None or snapshot['state'] not in TERMINAL)
        self.run_button.set_sensitive(client.phase == 'ready' and client.capabilities is not None and
                                      'system-info' in client.capabilities['tools'] and not active and
                                      not state.submitting and not state.acceptance_uncertain and
                                      not (snapshot is not None and snapshot['result_uncertain']))
        self.stop_button.set_sensitive(client.phase in ('ready','error') and active and snapshot is not None and
                                       not snapshot['cancel_requested'])
        if state.acceptance_uncertain:
            message = text('task.acceptance_uncertain')
        elif client.phase != 'ready':
            message = text('task.service_' + client.phase)
        elif snapshot is not None:
            if snapshot['result_uncertain']:
                message = text('task.outcome_uncertain')
            elif snapshot['cancel_requested'] and active:
                message = text('task.stop_pending_commit')
            elif snapshot['state'] == 'waiting':
                message = text('task.native_waiting')
            else:
                message = text('task.' + snapshot['state'])
            message += '\n' + text('task.identifier').format(task=state.task_id)
        elif state.submitting:
            message = text('task.accepting')
        else:
            message = text('task.native_ready')
        self.task_status.set_text(message)
        self._render_conversation(active,message)
        self._render_profile()

    def _render_conversation(self,active,status):
        client=self.client
        caps=client.capabilities or {}
        text=self.model.text
        ready=client.phase=='ready' and client.text_status!='failed' and caps.get('agent_backend') is True and \
              'agent-text-v1' in caps.get('features',[]) and caps.get('provider_mode') in ('local','remote')
        uncertain=client.state.acceptance_uncertain or (client.state.snapshot is not None and
                                                       client.state.snapshot['result_uncertain'])
        can_send=ready and not active and not client.state.submitting and not uncertain
        remote=caps.get('provider_mode')=='remote'
        self.entry.set_sensitive(can_send)
        self.remote_consent.set_visible(ready and remote)
        self.send_button.set_sensitive(can_send and (not remote or self.remote_consent.get_active()))
        self.conversation_stop.set_sensitive(self.stop_button.get_sensitive())
        self.conversation_status.set_text(status if client.state.task_id or client.state.submitting
                                          else text('conversation.ready' if ready else 'conversation.unavailable'))
        self.history_status.set_text(text('conversation.saved_history') if client.text and client.text.history_enabled
                                     else text('conversation.window_history'))
        rendered=[]
        for item in client.history:
            rendered.append(text('conversation.you')+'\n'+item['prompt'])
            if item['text']: rendered.append('Toddy\n'+item['text'])
        if client.current_prompt:
            rendered.append(text('conversation.you')+'\n'+client.current_prompt)
        if client.text and client.text.text:
            rendered.append('Toddy\n'+client.text.text)
        output='\n\n'.join(rendered)
        start,end=self.conversation_buffer.get_bounds()
        if self.conversation_buffer.get_text(start,end,True)!=output:
            self.conversation_buffer.set_text(output)

    def _render_profile(self):
        client=self.client
        available=client.phase=='ready' and client.profile is not None and \
                  'profile-settings-v1' in (client.capabilities or {}).get('features',[])
        self.profile_editor.set_editable(available)
        if not available:
            self.profile_validate.set_sensitive(False)
            self.profile_apply.set_sensitive(False)
            self.profile_restore.set_sensitive(False)
            self.profile_status.set_text(self.model.text('profile.settings_unavailable'))
            return
        revision=client.profile['profile_revision']
        mismatch=self._profile_rendered_revision is not None and self._profile_rendered_revision!=revision
        if self._profile_force_reload or self._profile_rendered_revision is None or (mismatch and not self._profile_dirty):
            self._setting_profile=True
            self.profile_buffer.set_text(json.dumps(client.profile['config'],ensure_ascii=False,indent=2))
            self._setting_profile=False
            self._profile_rendered_revision=revision
            self._profile_dirty=False
            self._profile_force_reload=False
        conflict=self._profile_rendered_revision!=revision
        self.profile_validate.set_sensitive(not conflict)
        self.profile_apply.set_sensitive(client.profile_stage is not None and not conflict)
        revisions=client.profile['previous_revisions']
        if revisions!=self.previous_revisions:
            self.previous_revisions=list(revisions)
            self.restore_choices.set_model(Gtk.StringList.new([value[:12] for value in revisions]))
        self.profile_restore.set_sensitive(bool(revisions))
        key='profile.concurrent_edit' if conflict else {
            'failed':'profile.invalid_revision','validated':'profile.validated',
            'editing':'profile.edited','loaded':'profile.loaded'}.get(client.profile_status,'profile.loaded')
        self.profile_status.set_text(self.model.text(key))

    def _run_native(self, *_):
        try:
            note = self.task_note.get_text().strip() or self.model.text('task.inspect_system')
            self.client.submit_system_info(note)
        except ValueError:
            self.task_status.set_text(self.model.text('task.service_error'))

    def _stop_native(self, *_):
        try:
            self.client.stop()
        except ValueError:
            self.task_status.set_text(self.model.text('task.service_error'))

    def _failure(self):
        # Reload is explicit: never retry an uncertain/stale save automatically.
        self.status.set_text(self.model.text('setup.state_error'))
        self.save.set_sensitive(False)
        self.defer_button.set_sensitive(False)
        reload_button = Gtk.Button(label=self.model.text('setup.reload'))
        reload_button.connect('clicked', self._reload)
        self.toast.add_toast(Adw.Toast.new(self.model.text('setup.state_error')))
        if not hasattr(self, 'reload_button'):
            self.reload_button = reload_button
            self.status.get_parent().append(reload_button)

    def _reload(self, *_):
        try:
            self.model.reload()
            self.backend.set_selected(('later', 'api', 'local').index(self.model.manifest['ai_choice']))
            self.save.set_sensitive(True)
            self.defer_button.set_sensitive(True)
            self.status.set_text(self.model.text('setup.intent_only'))
        except (SetupError, OSError, ValueError):
            self._failure()

    def _save(self, *_):
        try:
            self.model.choose_backend(('later', 'api', 'local')[self.backend.get_selected()])
            self.status.set_text(self.model.text('setup.intent_saved'))
        except (SetupError, OSError, ValueError):
            self._failure()

    def _defer(self, *_):
        try:
            self.model.defer()
            self.backend.set_selected(0)
            self.status.set_text(self.model.text('setup.deferred'))
        except (SetupError, OSError, ValueError):
            self._failure()


class ToddyApplication(Adw.Application):
    def __init__(self, model):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.model = model
        self.window = None
        action = Gio.SimpleAction.new('quit', None)
        action.connect('activate', lambda *_: self.quit())
        self.add_action(action)
        self.set_accels_for_action('app.quit', ['<Primary>q'])

    def do_activate(self):
        if self.window is None:
            self.window = SetupWindow(self, self.model)
        self.window.present()


def main():
    parser = argparse.ArgumentParser(description='Toddy native deferred setup')
    source_root=Path(__file__).resolve().parents[2]
    default_data=source_root if (source_root/'config/phase2/software-catalog.json').is_file() else Path('/usr/share/toddy')
    parser.add_argument('--data-root', type=Path, default=default_data)
    parser.add_argument('--state-directory', type=Path)
    parser.add_argument('--locale', choices=('en', 'pt-BR'))
    args = parser.parse_args()
    locale = args.locale or os.environ.get('LANG', 'en')
    model = None
    try:
        model = SetupModel(args.data_root, args.state_directory or state_directory(), locale)
        return ToddyApplication(model).run([sys.argv[0]])
    except (SetupError, OSError, ValueError):
        # No raw exception, private path, credential or provider error in output.
        print('Toddy setup could not open private setup state. Existing state was preserved.', file=sys.stderr)
        return 1
    finally:
        if model is not None:
            model.close()


if __name__ == '__main__':
    raise SystemExit(main())
