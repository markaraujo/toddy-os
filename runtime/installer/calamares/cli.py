#!/usr/bin/env python3
"""Fixed root-only Calamares backend entry; integer FDs, no script/command input."""
import argparse
import json
import os
from pathlib import Path
import signal
import resource
import sys

# Fixed source/installed namespace bootstrap. -I ignores caller Python paths;
# the production launcher uses this root-owned installed file only.
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
if Path(__file__).resolve().parents[2].name == 'toddy':
    from toddy.installer.backend import Journal
    from toddy.installer.disk_plan import InstallError
    from toddy.installer.live_bindings import create
    from toddy.installer.calamares.adapter import CalamaresAdapter, sealed_json, SealedConfirmation, PipeCancellation, encoded
else:
    from runtime.installer.backend import Journal
    from runtime.installer.disk_plan import InstallError
    from runtime.installer.live_bindings import create
    from runtime.installer.calamares.adapter import CalamaresAdapter, sealed_json, SealedConfirmation, PipeCancellation, encoded

JOURNAL = Path('/var/lib/toddy/installer')
SAFE_CODES = {'installer_root_required', 'installer_composed_closure_unavailable',
    'installer_native_closure_not_qualified', 'installer_live_binding_incomplete',
    'installer_current_destructive_authorization_required', 'installer_human_confirmation_invalid',
    'installer_canceled_at_safe_boundary_rescue_required', 'installer_target_changed_since_review',
    'installer_composed_payload_not_verified', 'installer_previous_outcome_requires_reconciliation',
    'installer_operation_identity_conflict', 'installer_writer_busy', 'installer_cli_arguments',
    'installer_sealed_descriptor_required', 'installer_private_descriptor_required',
    'installer_private_pipe_required', 'installer_plan_changed', 'installer_plan_schema',
    'installer_login_password_bounds', 'installer_pending_handoff_not_verified',
    'installer_live_payload_identity_changed', 'installer_firmware_not_qualified',
    'installer_target_not_blank_unmounted_writable', 'installer_qualification_target'}


class Parser(argparse.ArgumentParser):
    def error(self, _message):
        # Never reflect a caller's accidental password/value from invalid argv.
        raise InstallError('installer_cli_arguments')


def targets(adapter):
    adapter.readiness()
    raw = json.loads(adapter.system.run(['/usr/bin/lsblk', '--json', '--bytes', '--paths', '--nodeps', '--output', 'PATH,TYPE']))
    result = []
    for row in raw.get('blockdevices', [])[:64]:
        if row.get('type') != 'disk':
            continue
        try:
            disk = adapter.system.probe(row['path'])
            adapter.bindings.policy.check(disk)
            result.append(disk)
        except (InstallError, OSError, ValueError, KeyError):
            continue
    return {'version': 1, 'state': 'available', 'targets': sorted(result, key=lambda row: row['path'])}


def main(argv=None):
    journal = None
    cancellation = None
    output_open = True
    def emit(value):
        nonlocal output_open
        if not output_open:
            return
        try:
            sys.stdout.buffer.write(encoded(value) + b'\n'); sys.stdout.buffer.flush()
        except (BrokenPipeError, OSError):
            # A vanished UI is a safe-boundary Stop request, never grounds to
            # SIGKILL a package/filesystem/boot command that may be committing.
            output_open = False
            if cancellation is not None:
                cancellation.request()
    try:
        if os.getuid() != 0 or os.geteuid() != 0:
            raise InstallError('installer_root_required')
        os.umask(0o077)
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        parser = Parser(description=__doc__, add_help=False)
        parser.add_argument('action', choices=['capabilities', 'targets', 'review', 'execute'])
        parser.add_argument('--options-fd', type=int)
        parser.add_argument('--plan-fd', type=int)
        parser.add_argument('--confirmation-fd', type=int)
        parser.add_argument('--credential-fd', type=int)
        parser.add_argument('--cancel-fd', type=int)
        args = parser.parse_args(argv)
        needed = {'capabilities': set(), 'targets': set(), 'review': {'options_fd'},
                  'execute': {'plan_fd', 'confirmation_fd', 'credential_fd', 'cancel_fd'}}[args.action]
        supplied = {key for key in ('options_fd', 'plan_fd', 'confirmation_fd', 'credential_fd', 'cancel_fd') if getattr(args, key) is not None}
        if supplied != needed or len({getattr(args, key) for key in supplied}) != len(supplied):
            raise InstallError('installer_cli_arguments')
        # No module/path/function can be chosen through arguments or environment.
        adapter = CalamaresAdapter(create())
        readiness = adapter.readiness()
        if args.action == 'capabilities':
            emit({'version': 1, 'state': 'available', 'calamares': '3.4.3',
                  'firmware': readiness['supported_firmware'], 'credentials_in_plan': False})
        elif args.action == 'targets':
            emit(targets(adapter))
        elif args.action == 'review':
            options = sealed_json(args.options_fd)
            if not isinstance(options, dict) or set(options) != {'device', 'options'}:
                raise InstallError('installer_cli_arguments')
            emit(adapter.review(options['device'], options['options']))
        else:
            plan = sealed_json(args.plan_fd)
            confirmation = SealedConfirmation(args.confirmation_fd)
            cancellation = PipeCancellation(args.cancel_fd)
            for number in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
                signal.signal(number, lambda *_: cancellation.request())
            # Readiness is already proven before any persistent journal or native
            # disk operation; actual payload verification repeats before sfdisk.
            journal = Journal(JOURNAL)
            result = adapter.execute(plan, journal, confirmation=confirmation,
                credential_fd=args.credential_fd, cancel=cancellation, observer=emit)
            emit({'version': 1, 'kind': 'result', **result})
        return 0
    except Exception as error:
        code = str(error) if isinstance(error, InstallError) and str(error) in SAFE_CODES else 'installer_step_unverified'
        emit({'version': 1, 'kind': 'result', 'state': 'unavailable' if code == 'installer_composed_closure_unavailable' else 'failed',
              'code': code, 'installed_boot_validation': 'not-run'})
        return 2
    finally:
        if journal is not None:
            journal.close()


if __name__ == '__main__':
    raise SystemExit(main())
