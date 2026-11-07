> H01-H13 complete; G1 passed in QEMU/KVM. Foundation evidence and the published
> ISO remain unchanged. Current authorized work is Phase 2 replanning, navy brand,
> UI design previews and the public Pages redesign; guest builds have not started.

# Development handoff

For unattended runs follow [the night-execution simulation and bounded decision policy](PHASE-2-NIGHT-EXECUTION.md).
This adds no guest-start authorization.

## Current scope and next work

Phase 2 has been replaced by [PHASE-2-PLAN.md](PHASE-2-PLAN.md),
[PHASE-2-VALIDATION.md](PHASE-2-VALIDATION.md) and revised B01-B13 stories.
[ADR-0105](adr/0105-toddy-assistant-and-owner-preview.md) records the native Toddy
assistant, basic-test owner-preview policy and third-party driver/app choices.
The owner additionally requires user-customizable harness profiles/skills following
Hermes/OpenClaw patterns (docs/PHASE-2-HARNESS.md and ADR-0106), plus humorous realistic GNOME installer scenes,
small traceable commits and a navy public-page redesign preserving the exact logo.

Planning, contract/catalog inputs and brand/UI concepts are prepared in the repository; the public
page includes selectable desktop/assistant/task/installer concepts. See
[brand evidence](evidence/navy-brand-preview.md) and
[Pages evidence](evidence/navy-pages-preview.md). Final review is complete; guest continuation still requires its explicit recorded
authorization. Do not reopen general planning on resume.
B stories remain not_started; repository design preparation does not satisfy
B11 runtime acceptance. G1 is passed, G2 pending, physical hardware unverified.
Do not interpret a screenshot mockup or an optional package candidate as a working
OS feature. Historical implementation/recovery notes below do not override the
new Phase 2 plan or authorize duplicate foundation builds.

## Phase 2 execution review

Read [the closed design choices](PHASE-2-DESIGN-BASELINE.md),
[the findings](PHASE-2-REVIEW.md), [execution/resume playbook](PHASE-2-EXECUTION.md)
and [current continuation card](PHASE-2-CHECKPOINT.md). The preferred eligible
sequence front-loads headless engine/policy/recovery and installer feasibility.
Do not read the historical H-build sequence below as a command to rebuild the
accepted foundation. Source/target checkpoint and one next action survive a new
agent session; private running-job details stay outside Git.

Reusable [prework inputs](PHASE-2-PREWORK.md) now cover native branding, stable
identity/icon roles, bilingual semantic scenarios and accepted dependency reuse.
Read these before creating duplicate assets, strings, packages or build tooling.
The latest [readiness review](PHASE-2-READINESS-REVIEW.md) closes the integrated
planning review and supplies a short reading map. [ADR-0110](adr/0110-isolated-package-builds-and-change-based-validation.md)
selects qualified isolated/staged builds and change-based validation. Offline
base setup works with agent components absent; later acquisition requires no OS
reinstallation. Native dependencies, UI timings and runtime gates remain unproved
until guest implementation. Do not restart plan reviews without a concrete new gap.

Shared app selection, deferred acquisition and on-request recommendations follow
[the software catalog contract](PHASE-2-SOFTWARE-CATALOG.md); candidates are not
installed packages or new mandatory breadth. Reuse existing S19/S20/S21/S26.

## Small delivery loop

Take one user-visible behavior or isolated prerequisite at a time. Record its
inputs/checkpoint, implement a focused diff, run only basic affected checks,
commit/push a working boundary and leave the exact next command/log. Do not wait
for an entire B milestone to commit. If a check becomes unexpectedly long, inspect
its progress/cause and choose a documented narrower meaningful check when safe;
never rerun a long suite blindly or hide a critical failure. Owner use expands
coverage after a labeled experimental preview. No unbounded execution promise.

## Owner implementation boundary

ADR-0063's foundation review remains historical and guest continuation must be
explicitly requested. The current request authorizes the revised plan and
repository brand/UI/Pages work. It does not assert that owner hardware testing
already occurred. Continue routine reversible work within that scope without
asking for milestone confirmation.

## Start a development session

Open this repository in Codex. Give the following instruction:

> Read AGENTS.md, STATUS.md/status.json, the current section of docs/DEVELOPMENT.md, docs/OPEN-DECISIONS.md and docs/PHASE-2-CHECKPOINT.md. Follow docs/PHASE-2-EXECUTION.md and the selected eligible story. Inspect actual Git, target/checkpoint, job/log and last verified evidence before resuming its one next action. Do not rebuild accepted H01-H13 or start a duplicate writer. Guest Phase 2 work requires recorded explicit owner continuation; a planning request or next_story=B01 is not approval. Record passing small slices, affected tests, failures and recovery, commit/push through the authorized workflow, and keep the continuation card current. Report concrete missing access/legal/paid/destructive-host dependencies only after authorized alternatives are tried.

Do not paste API keys into the prompt. Do not weaken sandbox/approval configuration globally. A product's full-power profile belongs inside its designated system, not on the author's workstation.

## Commands

Python 3.10+ and Git are enough for the planning tooling. No Node packages or external Python modules are required.

- make check: validate stories, IDs, dependencies, acceptance evidence, source lock and generated files.
- make progress: print phase progress and next task.
- make dashboard: regenerate STATUS.md and dashboard/index.html.
- python3 scripts/project.py set H01 in_progress: start a milestone.
- python3 scripts/project.py set H01 completed --evidence docs/evidence/H01.md: complete after acceptance evidence exists.

Edit the relevant story's execution record, write evidence, update journal/errors/ADRs, and regenerate progress before committing. A done story must not depend on an unfinished one. Use make check from a clean checkout to detect a stale dashboard.

## Development sequence

H01 first inventories tools and resources, then may install/configure the required host tools and provision the selected guest under ADR-0003. Choose VM location/resources and the package-tracking evaluation approach before provisioning. Record measured disk/RAM limits and reserve space; do not assume hardware from previous chats. H02 freezes the downloaded book/source manifest. H03 introduces reproducible recipes and target guards. No actual build command is supplied by bootstrap: recipes must be derived and reviewed against the frozen book during implementation.

## Evidence and artifacts

Commit small sanitized test summaries to docs/evidence/. Large build logs stay outside Git with paths/hashes in summaries. ISOs, disks, root filesystems, model weights and source tarballs stay in ignored storage; release artifacts carry SHA-256 and a component/license manifest. Use environment-specific config outside Git for target paths and secrets.

## Stop and resume

Before stopping, persist current task, exact failed step, checkpoint, command exit status and next action. Never label waiting jobs complete. A resumed session reads the files and inspects actual processes/artifacts rather than trusting an old chat summary. Record any externally running build's PID/session and log path locally, not as portable state.

## Source and visibility policy

Use a feature branch for implementation, focused commits and pull requests where practical. No force push or history rewriting without a reason. The owner authorized a public repository and GitHub Pages dashboard on 2026-11-05. Publish only the dashboard export, not arbitrary runtime/build directories. Preserve secrets and finish the licensing decision before distributing licensed release artifacts. Development context lives in the committed repository files; workstation RAG is excluded by owner decision.

## Historical pre-start audit (2026-11-05)

A read-only snapshot found an x86_64 AMD Ryzen 9 5900XT with 32 logical CPUs, about 30 GiB RAM (20 GiB available), about 758 GiB available on the repository filesystem, and readable/writable /dev/kvm in the current session. This is not a completed H01 or a successful guest boot.

QEMU, qemu-img, virsh and VBoxManage were not available in PATH. GCC, G++, Make, Python and Git were available; bison and gawk were missing. Recheck actual versions and the designated guest environment during H01. Do not assume a host tool list validates the future build guest.

Before compilation: provision the selected VM, satisfy book requirements, verify/freeze sources in H02 and resolve package ownership in H03. The package-manager prototype may run in a disposable staging environment; do not require a final guest rootfs before the toolchain exists. No software was installed by this audit.

The planning CI checks metadata, dependency gates and progress tooling, not an OS image. The native package strategy is the most consequential early design risk. Desktop/harness/voice/installer feasibility and project licensing are scheduled later; none prevents starting H01. The GitHub social-preview image is a separate cosmetic follow-up, not a build prerequisite.

## Autonomous dependency installation and unblocking

Once development is started, the owner explicitly authorizes the development AI to install, update and configure the tools, system packages and build dependencies necessary to develop and test Toddy OS, on the development host as needed and inside the designated VM/chroot. This includes virtualization, compilers, build tools, image/boot utilities, language tooling and test dependencies. The AI may use available administrative privileges, including sudo, for these project-related operations without asking again for each routine installation.

Diagnose blockers, choose a suitable dependency from an official upstream or trusted package source, install/configure it, verify the result, document the change and continue. Resolve failed downloads, missing tools, compatible dependency versions and reversible project-related configuration issues autonomously. Preserve the frozen target package set; do not silently upgrade it to bypass a build failure. Record host changes separately from guest recipes so the build remains portable.

This authorization does not create credentials or elevate the actual runtime by itself. If an administrator password, account authentication, unavailable permission, mandatory legal acceptance or a paid resource is required, report that concrete dependency and request only the missing user action. Do not request passwords or tokens in chat or bypass enforced security controls. Preserve unrelated applications, user data and existing work. Formatting physical disks, installing Toddy OS onto the host, destructive unrelated changes, weakening global security and purchasing services remain outside routine dependency installation.

Current Phase 2 work follows the authorization scope at the top of this handoff; historical provisioning notes do not start a guest build.

## Published dashboard

Live URL: https://markaraujo.github.io/toddy-os/

A single repository is authoritative. Run make dashboard, commit status.json and generated files, then push validated changes to main. The GitHub Pages workflow checks the planning state, exports an allowlisted static site and deploys it automatically. Feature branches do not deploy. The site links story/PRD details to the same GitHub repository, and includes the allowlisted portal, supporter page, design previews and their declared assets. No second repository, cross-repository key or provider account is required.

Use make site for a local export into ignored _site/. All site data is public; never include credentials, local logs, personal memory or machine-specific secret configuration in status data. A dashboard reflects the last published commit, not uncommitted filesystem changes or a live process monitor.


## Historical H07 driver and audit sequence

Archive only: H13/G1 are completed. The counts, commands and running-state notes
below describe prior attempts, not the next action. Use the current continuation
card and accepted H13 evidence; do not run these historical drivers on resume.


Use actual runner markers, driver exit files and docs/RECOVERY.md, not a
historical journal count, to select work. Current accepted boundary is 124
source-built packages; the Berkeley DB standard attempt exposed a reproduced fixture isolation failure.
Do not sync build inputs or run another dispatcher while that recipe holds the
exclusive lock. Long Tcl tests update their own ALL.OUT; a quiet tee is not a
stalled test and a partial log is not success.

At the next successful quiescent boundary, sync the current committed inputs,
run h07-perl-test-tools-driver.sh, then success-gated h07-final-base-driver.sh.
Prepared recipes are separate from acceptance. The first new package must prove
source-built native Dpkg routing from actual archive provenance/postcheck. Final
metadata closure preserves original archives, normalizes only build ownership,
retains reviewed privileged helpers, derives ELF/interpreter dependencies and
verifies actual installed payload. Shared/generated state and optional internal
program/data/dlopen requirements remain explicit; no audit is silently treated
as complete release acceptance.

Reproduce legal input inventory with scripts/host/audit_source_notices.py;
content-addressed generations preserve older evidence. Source grant/collection
entries identify actual frozen inputs and original terms, not a whole-OS
relicense. License/source availability, credentials and image inclusion must be
checked against the actual assembled artifact before G1/G2.


H08 configuration preparation is in scripts/build/h08 and ADR-0042. It is not an
alternate route around H07. After complete H07 acceptance/checkpoint, mark H08
in_progress, regenerate/commit progress and sync public status.json with build
inputs before h08-driver.sh. A premature gate probe must refuse. Prepared text,
backup safety tests and offline checks do not establish native boot networking.


Current exception to the earlier driver order: the known-failed BDB attempt was
stopped with zero installed changes after reproducing test142 contamination.
Run independent Perl/Triehash/Which/Libseccomp/Tcsh work after verified quiescent
sync, then corrected full BDB retest/production acceptance; APT remains gated.
See docs/errors.md and the latest RECOVERY section. A partial full-suite log or
focused success sentinel alone does not accept Berkeley DB.

After all native support markers pass, h07-base-ownership-driver.sh may complete
the independent full ACL retest and API/layout/build-support ownership before
the long corrected DB suite. It does not run APT or final metadata closure.
The final-base driver still requires accepted BDB/APT and skips only actual
existing success markers; no acceptance prerequisite is waived.


H09's production kernel recipe remains gated on H08 acceptance and synchronized
H09 in_progress status. ADR-0046's private native configuration passed; ADR-0085
extends preparation to an isolated native compilation with private module
staging, separate from the final package recipe. That build and its diskless
BIOS/UEFI diagnostic boots now passed with actual terminal exits zero; see
docs/evidence/H09-private-kernel.md. Private diagnostic success does not accept
H09; production ownership, complete foundation boot and native regressions remain.


The optional active_work record in status.json publishes verified facts, current
activity, remaining acceptance and a verification timestamp. It never changes
weighted phase percentages. Update it from actual evidence; project.py set
clears it when that story completes. The dashboard is a published snapshot,
not a live guest-process monitor.


Current DB continuation uses the isolated complete rerun in ADR-0069. The
20/20 other_repmgr and 11/11 multi_repmgr corrections passed. The original suite
continues collecting results but cannot pass with its existing failures. A
separate complete corrected standard run now uses verified native inputs and
private namespaces; it must finish with strict success before production
handoff. The earlier waiting serial-retry supervisor was disarmed. See the last
RECOVERY section for actual driver paths/PIDs; do not start duplicate tests.


The composed fresh-root assembler is prepared at h10/assemble_root.py
(ADR-0072), with distinct H10 and H11 --release gates. Its standalone CLI owns
the build lock, preserves per-stage evidence and refuses existing generations.
Native owned-payload/metadata checks pass in a private eleven-package root;
full source readiness still correctly refuses the unfinished H07 shared Info
index. Complete positive assembly, remaining image audits and boot are pending.

The latest terminal-review components (ADR-0084) separate raw execution outcomes
from diagnostic classification. A review exit zero means the review itself
completed, not that an exit-1 database suite became a passing run. Only exact
source-backed diagnostics with complete native evidence can proceed to later
qualification; unknown assertions still fail. Production nomination retains its
strict current gate until that separate path is implemented and verified.


ADR-0086 protects the already completed native coverage source and records a
separate custody receipt without changing raw test outputs/exits. The full
review now requires its read-only custody verification. The standard suite is
still running; its own source remains untouched and unaccepted. Exact terminal
qualification, full-source custody, production handoff and portable fresh-build
diagnostic handling remain required before closing H07.


ADR-0087 prepares a separate exact diagnostic qualification after complete
native review and full-source custody. It preserves raw 1/1 exits and the failed
upstream summary. Native premature/full-versus-focused refusals passed, but the
complete positive path is still pending. Production nomination remains strict
and must not be changed to consume this decision until actual full positive
verification. Current recovery profiles are not yet portable fresh-build
acceptance; the normal fresh recipe still needs isolated run/diagnostic handling.

ADR-0088 versions private test preparation and verifies it against completed
native inputs: 10,207 copied files, 483 frozen Tcl comparisons, 460 checkpoint
matches and actual private namespace/tmpfs probe passed. This removes the
preparer's session-directory dependency. It is not yet wired into the normal
fresh recipe; portable compile/coverage provenance, full execution and terminal
acceptance integration remain. Do not launch its private generation while the
existing corrected complete suite remains active.

ADR-0089 adds actual fresh native test compilation using the same staged recipe:
all five stages, C tests, helper and private preparation passed. Independent
provenance verification binds frozen sources, reviewed code, native context and
prepared binary bytes without the historical recovery seed. The retained build
is complete; do not restart it or launch its prepared suite. The normal fresh
full runner/coverage/qualification integration remains the next implementation
slice while the existing full corrected producer finishes.

ADR-0090 shares execution checks while retaining distinct mandatory provenance:
historical recovery still requires its measured seed; the fresh standard result
requires the verified native-build/prepared-input binding. Actual unfinished/
wrong-generation refusals and historical coverage custody passed. Complete
positive validation is still pending; portable failed-summary coverage and the
normal private fresh-dispatch/production integration remain required work.

ADR-0091 fixes production evidence preservation before actual handoff: the tested
source is mounted read-only, with separate writable build output. An actual
private production compilation/stage and the unchanged transaction/reopen/
rollback check passed, preserving all 10,606 source entries and bytes. The
nominated production recipe now uses this view; its complete-suite/dispatcher
gate remains mandatory. No package was installed or standard suite accepted.


### Current Berkeley DB delivery validation (2026-11-07)

The owner explicitly approved focused Berkeley DB validation for this experimental
delivery. ADR-0092 supersedes earlier instructions requiring the complete standard
Tcl suite before production. Preserve the cancelled and failed full runs as such;
require native C tests, production transaction/reopen/rollback/crash recovery,
actual APT cache interruption/rebuild and existing signed-repository/HTTPS/package
checks before H07 acceptance. All other critical suites and H13/G1 gates remain.
See [ADR-0092](adr/0092-focused-berkeley-delivery-validation.md).
