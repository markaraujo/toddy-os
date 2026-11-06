# Development handoff

## Current scope

The planning repository and approved artwork are prepared. No LFS source packages have been downloaded, no OS build has run and no bootable ISO exists. The next implementation milestone is H01. Repository bootstrap is separate from OS progress.

## Start a development session

Open this repository in Codex. Give the following instruction:

> Read AGENTS.md, PRD.md, STATUS.md, status.json and docs/DEVELOPMENT.md. Start H01, inspect the actual host and choose a disposable build environment. Inspect the versioned candidate in H01 and freeze it in H02, then follow that frozen LFS book through both phases without asking whether to continue, maintain logs, decisions and progress, and validate each milestone. Do not touch physical disks or begin Phase 2 before its gate. Autonomously install and configure required host/guest tools with available administrative privileges, verify fixes and continue; request user action only for concrete unavailable access or actions outside scope. Report concrete blockers and verified results.

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
