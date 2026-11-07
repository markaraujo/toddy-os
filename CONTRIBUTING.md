# Contributing to Toddy OS

Contributions are welcome through focused pull requests. Marcos Araujo
([@markaraujo](https://github.com/markaraujo)) owns the project and has final review,
scope and merge authority. Anyone may propose a change; no contribution grants
repository write access, approval authority or a commitment to include it.

## Before you start

Read [the project requirements](PRD.md), [current status](STATUS.md) and
[development instructions](AGENTS.md). For a larger feature or architectural
change, open a proposal first so it can be aligned with the active phase.
Foundation acceptance is preserved; Phase 2 guest implementation still requires
the owner's recorded continuation. Do not start an OS build just to fix a document.

## Pull request workflow

1. Fork the repository, create a descriptive branch and make one coherent change.
2. Use English for canonical documentation, code comments and commit messages.
   Existing public locale catalogs have their own translated strings. Preserve
   approved artwork and third-party license notices.
3. Describe the concrete problem and resulting behavior. Link the issue/story,
   explain validation, and note recovery steps and remaining limitations.
4. Run `make dashboard` when changing generated progress inputs and `make check`.
   Run only focused behavioral tests affected by the change; ordinary CI does not
   build the OS or download model weights. See [Phase 2 validation](docs/PHASE-2-VALIDATION.md).
5. Open a PR against `main`. The owner reviews it; resolve review conversations
   and rerun affected checks after changes. New reviewable commits dismiss earlier
   approvals. Squash merge is the repository's community merge method.

The protected branch requires an owner/code-owner review and passing checks for
community contributions. The exact owner account retains an explicit bypass for
maintainer recovery and the existing authorized development workflow. Review
comments or approvals from other people are welcome feedback but do not replace
the owner's approval. GitHub does not allow an author to approve their own PR;
the maintainer bypass exists for owner-authored work, not for contributors to
self-approve. Auto-merge and workflow-created PR approvals are disabled.

## Safe public contributions

Never commit API keys, passwords, private signing keys, personal prompts, donor
contact/payment details, account cookies, disk images, models, private logs or
local environment files. `.gitignore` does not remove a secret already committed.
Use clearly fictional fixtures and scrub commands/screenshots before sharing.
Only approved public supporter display names belong in `config/community.json`.

GitHub secret scanning and push protection cover supported patterns. The separate
`public-content` check scans Git history with a pinned Gitleaks release. Neither
is a guarantee that arbitrary sensitive information will be detected. Reviewed
false-positive fingerprints in `.gitleaksignore` identify old test UUIDs/checksums,
not permission to add real credentials. Changes to security exceptions require
owner review; do not add ignore comments to hide a finding.

Fork workflows use read-only credentials and require owner approval to run for
external contributors. Approval to run a workflow is not approval to merge.
There is no `pull_request_target` execution of untrusted code and no deployment
credential in a PR job. Security findings should follow [SECURITY.md](SECURITY.md),
not a public issue containing an exploit or secret.

## License and evidence

Contributed original code is under [MIT](LICENSE), and original documentation/art
under [CC BY 4.0](LICENSES/CC-BY-4.0.txt), consistent with the repository policy.
Only contribute material you have the right to share; retain upstream licenses
and corresponding-source obligations. Hardware support needs actual identified
hardware evidence, and a design concept is not a working-system screenshot.
