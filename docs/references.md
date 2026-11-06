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
