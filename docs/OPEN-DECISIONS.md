# Open technical decisions

These are planned feasibility decisions, not missing permission to begin H01. Resolve routine choices with evidence and an ADR; escalate only a material change to the user's requirements.

| ID | Topic | Working recommendation | Resolve by | Evidence required |
| --- | --- | --- | --- | --- |
| D01 | Build environment | Resolved: container-packaged QEMU/KVM, ADR-0006 | H01 | Real guest boot, requirements and restart passed; VirtualBox untested |
| D02 | Book variant and freeze | Resolved: LFS/BLFS 13.1-systemd, ADR-0007 | H02 | Archives pinned; 94 sources verified; release security fixes remain mandatory |
| D03 | Package ownership and distribution | Evaluate dpkg/APT with our own packages/repository; no foreign core repos | H03, before final package recipes | Install/remove/upgrade prototype and manifest/rollback strategy |
| D04 | Desktop | GNOME/Wayland; evaluate fallback | B02 | Source build dependency plan and VM usability |
| D05 | Harness reuse versus custom core | Small open provider-independent core or replaceable existing OSS harness | B01 | License/dependency audit and end-to-end comparison |
| D06 | Canonical memory and semantic index | SQLite/FTS, optional vector adapter such as Qdrant | B07 | Search quality, deletion/backup test, resource measurements |
| D07 | Speech synthesis | Evaluate open TTS engines and separately licensed voices | B09 | Portuguese/English quality, latency and redistribution terms |
| D08 | Installer | Evaluate Calamares | B12 | Dependency footprint, blank-disk install and recovery tests |
| D09 | Proprietary firmware/driver policy | Open core with clearly separate optional hardware packs | B01 | Target hardware requirements and license inventory |
| D10 | Project licensing | Proposed MIT for original code, CC BY 4.0 for original docs/art where applicable | Before public release | Owner decision and component/source notices |
| D11 | Performance budgets | Establish measured acceptance budgets on the chosen target | B01 | Idle RAM/CPU, boot, agent/tool/search workload baselines |
| D12 | Production artwork | Preserve approved PNGs; create reviewed scalable/small-size masters | B11 | Render checks and legibility at actual UI sizes |

The whole-system license is a collection of component licenses, not the repository's proposed custom-code license. APIs can be optional without making the open local path dependent on them. This planning baseline deliberately does not claim universal Ubuntu binary compatibility.

Release security obligation: assess and freeze tested fixes for baseline advisories before final release (ADR-0007); H02 integrity success is not security approval.
