# Development handoff

## Current scope

The planning repository and approved artwork are prepared. No LFS source packages have been downloaded, no OS build has run and no bootable ISO exists. The next implementation milestone is H01. Repository bootstrap is separate from OS progress.

## Start a development session

Open this repository in Codex. Give the following instruction:

> Read AGENTS.md, PRD.md, STATUS.md, status.json and docs/DEVELOPMENT.md. Start H01, inspect the actual host and choose a disposable build environment. Follow the frozen LFS book, work through eligible Phase 1 stories, maintain logs, decisions and progress, and validate each milestone. Do not touch physical disks or begin Phase 2 before its gate. Report concrete blockers and verified results.

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

H01 may inventory tools without changing them. Choose VM location/resources and package-tracking strategy before provisioning. Record measured disk/RAM limits and reserve space; do not assume hardware from previous chats. H02 freezes the downloaded book/source manifest. H03 introduces reproducible recipes and target guards. No actual build command is supplied by bootstrap: recipes must be derived and reviewed against the frozen book during implementation.

## Evidence and artifacts

Commit small sanitized test summaries to docs/evidence/. Large build logs stay outside Git with paths/hashes in summaries. ISOs, disks, root filesystems, model weights and source tarballs stay in ignored storage; release artifacts carry SHA-256 and a component/license manifest. Use environment-specific config outside Git for target paths and secrets.

## Stop and resume

Before stopping, persist current task, exact failed step, checkpoint, command exit status and next action. Never label waiting jobs complete. A resumed session reads the files and inspects actual processes/artifacts rather than trusting an old chat summary. Record any externally running build's PID/session and log path locally, not as portable state.

## Source and visibility policy

Use a feature branch for implementation, focused commits and pull requests where practical. No force push or history rewriting without a reason. GitHub remains private through the first ISO review; CI uploads must not leak private artifacts. Project licensing must be finalized before public release. Development context lives in the committed repository files; workstation RAG is excluded by owner decision.
