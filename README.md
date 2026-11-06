<div align="center">

<img src="assets/brand/toddy-os-logo.png" alt="Toddy OS — a Shih-tzu wearing glasses" width="320">

# Toddy OS

**An independent Linux distribution built from source, with an open agentic desktop for development and automation.**

Planning baseline · No OS image built yet · Public development repository

</div>

## Start here

- [Product requirements](PRD.md)
- [Live progress dashboard](https://markaraujo.github.io/toddy-os/)
- [Current status](STATUS.md)
- [Development handoff](docs/DEVELOPMENT.md)
- [Milestone stories](stories/README.md)
- [Architecture decisions](docs/adr/README.md)
- [Visual identity](assets/brand/README.md)

The project follows two product phases: a verified Linux From Scratch foundation, then the desktop and agentic experience. Read `AGENTS.md` before implementation.

```sh
make check
make progress
```

The static dashboard in `dashboard/index.html` opens directly in a browser; it requires no service or external assets. Progress means verified acceptance criteria, not time elapsed.

This repository contains build recipes, configuration, documentation, tests and approved brand assets. Source archives, model weights, disk images, ISO files, secrets and runtime memory do not belong in Git. Release artifacts will be distributed separately.

## Project identity

Toddy OS is named after the founder’s Shih-tzu, Toddy. Its illustrated mascot is a proposal approved by the founder; current assets are PNG artwork, not vector masters.

## Licensing

The open-source licensing policy is tracked in [LICENSING.md](LICENSING.md). Do not treat one repository license as a replacement for the licenses of Linux, GNU tools, libraries, models, firmware or third-party artwork.
