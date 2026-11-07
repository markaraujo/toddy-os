# Primary references

Consulted 2026-11-05. Freeze sources during H02; these links are documentation, not an executable setup script.

| Source | Version/context | Use |
| --- | --- | --- |
| [LFS](https://www.linuxfromscratch.org/lfs/view/13.1-systemd/) | 13.1-systemd | Proposed source-build baseline |
| [BLFS](https://www.linuxfromscratch.org/blfs/view/13.1-systemd/) | 13.1 systemd | Desktop, networking and additional components |
| [LFS package management](https://www.linuxfromscratch.org/lfs/view/stable-systemd/chapter08/pkgmgt.html) | Consulted stable systemd page; re-resolve to frozen book | Ownership and upgrade planning; LFS does not choose a manager |
| [Debian package metadata](https://www.debian.org/doc/manuals/debian-handbook/sect.package-meta-information.en.html) | Online handbook | Dependencies and maintainer scripts explain why .deb format alone is not binary compatibility |
| [Sagui Linux](https://github.com/erigobeli/saguilinux) | Published project, LFS/BLFS 12.4 | Process inspiration; not Toddy OS build source or independently audited evidence |
| [Codex AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md) | Online official documentation | Durable repository instructions |
| [SQLite FTS5](https://www.sqlite.org/fts5.html) | Online documentation | Proposed local full-text search |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | Pin exact release/commit at integration | Optional local inference, not an agent harness |
| [whisper.cpp](https://github.com/ggml-org/whisper.cpp) | Pin at integration | Candidate offline speech recognition |
| [Calamares](https://calamares.io/about/) | Installer framework, evaluation pending | Distribution-independent installer candidate |
| [Docker containers](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-a-container/) | Online documentation | Containers share a host kernel; VM tests remain required |

Source versions observed in documentation are not proof that packages have been downloaded, built, tested or licensed for a release. Verify errata/advisories and transitive licenses during implementation.


## Phase 2 replanning references

Reviewed 2026-11-07. Moving upstream documentation; exact versions and licenses
must be frozen in B01 before implementation. No source download or build implied.

| Source | Version/context | Use |
| --- | --- | --- |
| [Pi toolkit](https://github.com/earendil-works/pi) | Current upstream, former badlogic/pi-mono; unpinned | Preferred MIT agent/provider components; namespace must be resolved from frozen source |
| [Pi agent core](https://raw.githubusercontent.com/earendil-works/pi/main/packages/agent/README.md) | Moving main README | Tool loop/events, not a privilege or durable execution guarantee |
| [Pi providers](https://raw.githubusercontent.com/earendil-works/pi/main/packages/ai/README.md) | Moving main README | Provider abstraction and local compatible endpoints |
| [GNOME HIG](https://developer.gnome.org/hig/) | GTK4/Libadwaita guidance | Native UI and accessibility |
| [GNOME shortcuts](https://help.gnome.org/gnome-help/keyboard-shortcuts-set.html) | Current help | Configurable quick-entry launch |
| [GNOME styling](https://developer.gnome.org/hig/guidelines/ui-styling.html) | Current HIG | Minimal supported customization, light/dark/focus |
| [Ubuntu installation](https://ubuntu.com/desktop/docs/en/latest/tutorial/install-ubuntu-desktop/) | Experience reference only | Optional third-party driver/firmware selections, not a repository dependency |
| [NVIDIA kernel modules](https://docs.nvidia.com/datacenter/tesla/driver-installation-guide/kernel-modules.html) | Current vendor guide; exact driver unselected | Kernel/module compatibility and license review candidate |
