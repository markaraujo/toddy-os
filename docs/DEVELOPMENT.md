# Development handoff

## Current scope

The planning repository and approved artwork are prepared. Implementation started by the owner on 2026-11-05. H01 provisions a real KVM build guest using container-packaged QEMU; see docs/evidence/H01.md and docs/RECOVERY.md. Source freeze is H02. H01–H06 passed; H07 final base has 124 accepted packages, including native support, independent ownership and corrected native capability detection; corrected Berkeley DB full retest and APT/final closure remain pending. See docs/BUILD.md and the current driver section below. No bootable Toddy ISO exists yet. status.json is authoritative for completed milestones.

## Owner review boundary

The owner requested on 2026-11-06 (America/Sao_Paulo) that development continue
through H13, then pause for their foundation testing. Deliver the verified ISO,
checksum and test/build/recovery evidence after G1. Do not start B01 or later
B stories until explicit owner approval is received. Foundation work remains
authorized now. This supersedes automatic progression in ADR-0004; see
[ADR-0063](adr/0063-owner-review-after-h13.md). The full release remains planned
and must not be marked complete at H13.

## Start a development session

Open this repository in Codex. Give the following instruction:

> Read AGENTS.md, PRD.md, STATUS.md, status.json and docs/DEVELOPMENT.md. Start H01, inspect the actual host and choose a disposable build environment. Inspect the versioned candidate in H01 and freeze it in H02, then follow that frozen LFS book through H13 without routine continuation questions; deliver the foundation for owner testing and wait for explicit approval before B01-B13, maintain logs, decisions and progress, and validate each milestone. Do not touch physical disks or begin Phase 2 before its gate. Autonomously install and configure required host/guest tools with available administrative privileges, verify fixes and continue; request user action only for concrete unavailable access or actions outside scope. Report concrete blockers and verified results.

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

## Pre-start audit (2026-11-05)

A read-only snapshot found an x86_64 AMD Ryzen 9 5900XT with 32 logical CPUs, about 30 GiB RAM (20 GiB available), about 758 GiB available on the repository filesystem, and readable/writable /dev/kvm in the current session. This is not a completed H01 or a successful guest boot.

QEMU, qemu-img, virsh and VBoxManage were not available in PATH. GCC, G++, Make, Python and Git were available; bison and gawk were missing. Recheck actual versions and the designated guest environment during H01. Do not assume a host tool list validates the future build guest.

Before compilation: provision the selected VM, satisfy book requirements, verify/freeze sources in H02 and resolve package ownership in H03. The package-manager prototype may run in a disposable staging environment; do not require a final guest rootfs before the toolchain exists. No software was installed by this audit.

The planning CI checks metadata, dependency gates and progress tooling, not an OS image. The native package strategy is the most consequential early design risk. Desktop/harness/voice/installer feasibility and project licensing are scheduled later; none prevents starting H01. The GitHub social-preview image is a separate cosmetic follow-up, not a build prerequisite.

## Autonomous dependency installation and unblocking

Once development is started, the owner explicitly authorizes the development AI to install, update and configure the tools, system packages and build dependencies necessary to develop and test Toddy OS, on the development host as needed and inside the designated VM/chroot. This includes virtualization, compilers, build tools, image/boot utilities, language tooling and test dependencies. The AI may use available administrative privileges, including sudo, for these project-related operations without asking again for each routine installation.

Diagnose blockers, choose a suitable dependency from an official upstream or trusted package source, install/configure it, verify the result, document the change and continue. Resolve failed downloads, missing tools, compatible dependency versions and reversible project-related configuration issues autonomously. Preserve the frozen target package set; do not silently upgrade it to bypass a build failure. Record host changes separately from guest recipes so the build remains portable.

This authorization does not create credentials or elevate the actual runtime by itself. If an administrator password, account authentication, unavailable permission, mandatory legal acceptance or a paid resource is required, report that concrete dependency and request only the missing user action. Do not request passwords or tokens in chat or bypass enforced security controls. Preserve unrelated applications, user data and existing work. Formatting physical disks, installing Toddy OS onto the host, destructive unrelated changes, weakening global security and purchasing services remain outside routine dependency installation.

The present task updates this plan only; do not start installations or builds until the owner starts development.

## Published dashboard

Live URL: https://markaraujo.github.io/toddy-os/

A single repository is authoritative. Run make dashboard, commit status.json and generated files, then push validated changes to main. The GitHub Pages workflow checks the planning state, exports an allowlisted static site and deploys it automatically. Feature branches do not deploy. The site links story/PRD details to the same GitHub repository, and includes only the dashboard and its mascot asset. No second repository, cross-repository key or provider account is required.

Use make site for a local export into ignored _site/. All site data is public; never include credentials, local logs, personal memory or machine-specific secret configuration in status data. A dashboard reflects the last published commit, not uncommitted filesystem changes or a live process monitor.


## Current H07 driver and audit sequence

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
