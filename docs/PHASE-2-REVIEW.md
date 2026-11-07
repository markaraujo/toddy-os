# Phase 2 planning and execution review

Date: 2026-11-07. Scope: PRD, B01-B13/status graph, plan, harness, smoke matrix,
development/release handoff and planning tooling. This is a review of plans and
controls, not a guest implementation, hardware test or security certification.
Owner priorities remain performance, security, small commits and focused basic
tests. "Perfect" is a quality target, not evidence that unbuilt software is safe.

## Findings and corrections

| ID | Priority | Gap and original surface | Correction / acceptance owner |
| --- | --- | --- | --- |
| R01 | Critical | G1/next_story suggested B01 while project.py did not enforce the documented owner-review boundary | Validator rejects active B state without true recorded approval plus evidence and G1; approval is still false |
| R02 | High | Resume instructions depended on broad historical prose without one current slice/job/checkpoint | New execution playbook, short continuation card and private runtime record; inspect real Git/VM/log/postconditions before resuming |
| R03 | High | Numeric order delayed headless risk feedback; 8-GiB runtime guest could be mistaken for a build budget | Risk-first priority with active-story preservation; separate build/runtime resource measurements in B01 |
| R04 | High | Pi/JS and GTK-native UI were chosen without a pinned binding/IPC integration contract | B01 freezes both runtimes, async transport/schema/limits/reconnect/cancel; B06 reconnects to the same task |
| R05 | High | Engine scheduling and authority changes could race system writes | Sequential mutating calls plus executor resource locks and grant-generation recheck; S06/S09 |
| R06 | Critical | A separate plugin process and same-UID profile folders were described too loosely as isolation | Explicit logical-profile limit; sandbox denies file/secret-service/network access with dummy fixtures, or unknown code stays disabled; B10/S16/S24-C |
| R07 | Critical | Crash-after-effect and safe package-commit cancellation lacked sufficiently explicit ordering | Persist prepared operation before dispatch, reconcile postconditions, hold unknown effects; Stop prevents later dispatch without unsafe SIGKILL; B05/S08-S10 |
| R08 | High | S01 demanded absent metrics; S17 actual installer created an implicit B11/B12 cycle; S24 mixed future features | Stage S01-A/B/C/D, S17-A/B and S24-A/B/C; no runtime pass during schema-only B01 |
| R09 | High | Installer/dependency feasibility appeared only near B12 | B01 current-upstream/no-write module/target-plan spike and live-to-installed recipe; actual installation remains B12 |
| R10 | Critical | Generic disk confirmation did not explicitly close source/mounted targets, pre-write identity races or installed firmware coverage | S18 immutable target recheck and source/root rejection; BIOS+UEFI by default, safe blank disks, explicit boot narrowing only |
| R11 | High | An early installed snapshot could omit later memory/voice/plugin packages yet be reused as final | B13 reassembles all accepted components, checks installed manifest/config/source closure and tests exact candidate hashes |
| R12 | Critical | Missing keyring and inherited live-image state lacked explicit failure/hygiene acceptance | No plaintext fallback; S12 locked/missing store; S26 removes live autologin/accounts/secrets and regenerates identity |
| R13 | High | B07 could duplicate B05 storage; deletion could be undone by USER.md replay or broken migration | Extend canonical store; transactional migration/consistent backup; explicit deletion and derived-cache checks; S13/S24-B |
| R14 | Medium | Overdue schedules and profile imports could enable unexpected automation | Freeze skip/run-once catch-up policy; imports/clones copy neither active workflows nor standing grants; S14 |
| R15 | High | FR-10 browser integration lacked a named story acceptance and desktop dependency | Narrow isolated local-page navigation/read fixture in B10/S25; B10 now also depends on B02 |
| R16 | High | Optional-to-enable voice/plugins could be confused with optional G2 acceptance; B06 customization could imply later skills/memory | Explicit interim text scope, staged customization and unchanged required G2 components; disabled required work earns no completion |
| R17 | Medium | Story prerequisites/criteria could drift from status.json without make check noticing | Validator compares B-story criteria/dependencies with canonical status, with regression checks; synchronized all revised stories |

All listed corrections are implemented in the planning documents/tooling. Their
runtime acceptance belongs to the named future stories. No deferred runtime test
was marked passed. IDs/weights stay B01-B13/100; G1/H01-H13 evidence is unchanged.

## Recommended delivery strategy

Use [PHASE-2-EXECUTION.md](PHASE-2-EXECUTION.md): one current slice, a small passing
commit, a target checkpoint and one next action. Front-load engine/bridge,
installer feasibility and recovery unknowns. Exercise installation before adding
voice/plugin polish, then reassemble the complete final candidate. A long build
can continue under monitoring while read-only/source preparation progresses;
never let two writers mutate the same guest/package state.

Tests must be necessary and bounded, not merely numerous. Fixture tests protect
protocol/policy edges cheaply; one real local model, actual guest desktop and
blank-disk installation prevent fixture-only success. Reuse stable foundation
results, test affected failures once after fixes and run a compact final-image
integration pass. Owner daily use expands coverage but cannot erase a required
safety failure. The plan now says what to do on timeout, uncertain effects,
missing credentials, compaction, a stale PID and a lost checkpoint.

## Upstream spot-checks

Reviewed official moving sources on 2026-11-07. They are feasibility information,
not a dependency freeze or an instruction to upgrade the accepted foundation.

- [Pi agent README](https://raw.githubusercontent.com/earendil-works/pi/main/packages/agent/README.md)
  and [package metadata](https://raw.githubusercontent.com/earendil-works/pi/main/packages/agent/package.json):
  observed @earendil-works/pi-agent-core 1.5.0; current documentation supports
  parallel tool execution by default. Inference: Toddy must explicitly choose
  sequential mutation and independently enforce serialization/authority.
- [Pi AI package](https://raw.githubusercontent.com/earendil-works/pi/main/packages/ai/package.json):
  observed @earendil-works/pi-ai 1.5.0. B01 must select/pin actual commits, runtime,
  imports and dependency licenses; current main is not a build lock.
- [Calamares official site](https://calamares.io/) points to development on Codeberg.
  The [old GitHub wiki](https://github.com/calamares/calamares/wiki) is historical.
  Inference: check current source/modules early; do not base integration on an
  abandoned mirror or assume a generic framework installs Toddy automatically.
- [XDG GlobalShortcuts interface v2](https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.GlobalShortcuts.html)
  describes session-bound shortcut registration and activation. Inference:
  probe the chosen GNOME/backend and preserve ordinary app activation as fallback;
  documentation existence is not proof of the selected guest's support.
- [systemd execution sandboxing](https://freedesktop.org/software/systemd/man/latest/systemd.exec.html)
  documents kernel/user-service restrictions and limits of filesystem settings.
  Inference: test the actual guest's denial behavior, not just unit-file syntax.
  The frozen guest version and kernel capability review remain B01 inputs.

## Remaining decisions and honest limits

The owner-requested [design closure](PHASE-2-DESIGN-BASELINE.md) fixes the default
choices and fallback rules. B01 still has to prove the selected Pi runtime/GTK bridge, current installer,
model footprint and dependency/ABI closure in the real designated target. B10
must verify its sandbox; B12 must demonstrate installed boot/update recovery.
These are tracked decisions, not defects claimed fixed in code that does not exist.
No performance, GPU/Wi-Fi, physical install or broad language/accessibility quality
claim follows from repository checks. No plan can guarantee absence of all bugs.
The owner's explicit guest-continuation approval is still pending; this review
never starts B01 or changes owner_review.phase_2_approved.

## Verification of the review itself

Planning tests cover owner-start denial, approval evidence requirements, schema/
dependency drift and next-story priority/active checkpoint preservation. Run
make dashboard, make site and make check. The combined repository check records
actual results in the journal; it is not any of S01-S26's guest acceptance.
