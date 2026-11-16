"""Native deferred setup. No model, secret store or task submission is loaded."""
import argparse
from pathlib import Path
import os
import sys

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Adw, Gio, Gtk

from runtime.setup.pending import SetupError
from runtime.ui.model import SetupModel, state_directory
from runtime.ui.bridge import TaskClient
from runtime.ui.task_state import TERMINAL

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
        self._setup()
        self._software()
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
        entry_group = Adw.PreferencesGroup(title=text('setup.assistant_unavailable'),
                                           description=text('setup.tasks_unavailable'))
        self.entry = Adw.EntryRow(title=text('assistant.welcome'))
        self.entry.set_sensitive(False)
        entry_group.add(self.entry)
        page.append(entry_group)
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
        self.client.close()
        return False

    def _task_changed(self):
        client = self.client
        state = client.state
        snapshot = state.snapshot
        text = self.model.text
        active = state.task_id is not None and (snapshot is None or snapshot['state'] not in TERMINAL)
        self.run_button.set_sensitive(client.phase == 'ready' and not active and
                                      not state.submitting and not state.acceptance_uncertain and
                                      not (snapshot is not None and snapshot['result_uncertain']))
        self.stop_button.set_sensitive(client.phase == 'ready' and active and snapshot is not None and
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
    parser.add_argument('--data-root', type=Path, default=Path(__file__).resolve().parents[2])
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
