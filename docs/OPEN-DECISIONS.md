# Open technical decisions

These are planned feasibility decisions, not missing permission to begin H01. Resolve routine choices with evidence and an ADR; escalate only a material change to the user's requirements.

| ID | Topic | Working recommendation | Resolve by | Evidence required |
| --- | --- | --- | --- | --- |
| D01 | Build environment | Resolved: container-packaged QEMU/KVM, ADR-0006 | H01 | Real guest boot, requirements and restart passed; VirtualBox untested |
| D02 | Book variant and freeze | Resolved: LFS/BLFS 13.1-systemd, ADR-0007 | H02 | Archives pinned; 94 sources verified; release security fixes remain mandatory |
| D03 | Package ownership and distribution | Resolved: native source-built .deb/dpkg/APT, ADR-0008 | H03 | Guest prototype passed; final dpkg/APT source build and signed repository remain release work |
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

Expat security exposure remains open (ADR-0013): source 2.10.0 is selected,
but upstream still reports unresolved issues. Audit XML consumers and verify
bounded unprivileged untrusted-input handling before release; no blanket
all-vulnerabilities-fixed claim is allowed.


H07 implementation obligations before G1: replace the temporary build-only
/etc/resolv.conf (QEMU 10.0.2.3) with H08 runtime DHCP/resolved configuration;
audit remaining GNU regex consumers for the measured Glibc 20381 fastmap issue
(Findutils uses its supplied fixed replacement, ADR-0020); verify actual native
kernel module loading in H09/H12 rather than treating builder module listing as
proof. These obligations do not change the release acceptance criteria.

Systemd's book-order build still links temporary Util-linux libraries. Its
initial package dependency subset must gain the final native Util-linux provider
after that later book package is accepted. Util-linux's optional Systemd linkage
must also be audited from actual ELFs. This is part of mandatory H07 versioned
metadata closure; neither initial archive claims a closed dependency graph.

H12 native namespace obligation: Systemd 261.2 test-namespace's
 test_process_is_owned_by_uid at line 391 is source-qualified EPERM only in
chroot (ADR-0025); require a real booted-target retry before G1. Keep the Glibc
container-dependent retests as well. E2fsprogs prezeroed allocation qualification
(ADR-0027) does not authorize installer use of assume_storage_prezeroed.
Vim full unfiltered suite now passed with all four frozen/verified live plugin
inputs as nonroot (ADR-0028/0031); preserve those checks on future rebuilds.
Native Dpkg acceptance passed. APT signed repository, final versioned dependency/
conffile ownership, Linux API/layout ownership, bootstrap quarantine and license
closure remain required (ADR-0032 through ADR-0036).
