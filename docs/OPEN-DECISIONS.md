# Open technical decisions

Current Phase 2 choices follow [the replanned execution contract](PHASE-2-PLAN.md) and [ADR-0105](adr/0105-toddy-assistant-and-owner-preview.md). Resolve routine technical choices with evidence; exact implementation versions remain pending. Historical foundation notes below preserve accepted evidence, not obsolete Phase 2 instructions.

| ID | Topic | Working recommendation | Resolve by | Evidence required |
| --- | --- | --- | --- | --- |
| D01 | Build environment | Resolved: container-packaged QEMU/KVM, ADR-0006 | H01 | Real guest boot, requirements and restart passed; VirtualBox untested |
| D02 | Book variant and freeze | Resolved: LFS/BLFS 13.1-systemd, ADR-0007 | H02 | Archives pinned; 94 sources verified; release security fixes remain mandatory |
| D03 | Package ownership and distribution | Resolved: native source-built .deb/dpkg/APT, ADR-0008 | H03 | Native Dpkg/APT, signed repository, ownership/dependency/credential/source closure passed H07/H11; installed-system updates remain Phase 2 |
| D04 | Desktop | GNOME/Wayland selected direction; native GTK4/Libadwaita Toddy UI; pin versions | B02 | Source build dependency plan and VM usability |
| D05 | Harness reuse versus custom core | Pi Agent Core/Pi AI preferred behind replaceable Toddy interface; exact versions pending | B01 | License/dependency audit and one minimal tool spike; compare alternative only on a concrete blocker |
| D06 | Canonical memory and semantic index | SQLite/FTS for preview; semantic search deferred until measured need | B07 | Search quality, deletion/backup test, resource measurements |
| D07 | Speech synthesis | Evaluate open TTS engines and separately licensed voices | B09 | Portuguese/English quality, latency and redistribution terms |
| D08 | Installer | Evaluate Calamares | B12 | Dependency footprint, blank-disk install and recovery tests |
| D09 | Proprietary firmware/driver policy | Installer choice for compatible separate third-party firmware/GPU packs; no Ubuntu repositories | B01 | Hardware IDs, source/license/redistribution review, exact kernel ABI and rollback; actual hardware result separate |
| D10 | Project licensing | Resolved: owner approved MIT for original code and CC BY 4.0 for original docs/art; ADR-0104 | Before public release | LICENSE, LICENSES/CC-BY-4.0.txt, separate component/source notices |
| D11 | Performance budgets | Establish measured acceptance budgets on the chosen target | B01 | Idle RAM/CPU, boot, agent/tool/search workload baselines |
| D12 | Production artwork | Navy environment palette; exact logo/mascot unchanged; realistic GNOME installer scenes and nerdy dog copy | B11 | Asset provenance, real versus concept labels, readable light/dark/focus states and actual guest captures |

| D13 | User-customizable harness | Accepted: Hermes/OpenClaw-inspired profiles/persona/skills; own validated schema and independent policy, ADR-0106 | B01/B06/B10 | Pin contract; atomic revision/restore, secret-free import/export, profile isolation and S24 |

The whole-system license is a collection of component licenses, not the repository's proposed custom-code license. APIs can be optional without making the open local path dependent on them. This planning baseline deliberately does not claim universal Ubuntu binary compatibility.

Release security obligation: assess and freeze tested fixes for baseline advisories before final release (ADR-0007); H02 integrity success is not security approval.

Expat security exposure remains open (ADR-0013): source 2.10.0 is selected,
but upstream still reports unresolved issues. Audit XML consumers and verify
bounded unprivileged untrusted-input handling before release; no blanket
all-vulnerabilities-fixed claim is allowed.


Foundation follow-ups now verified: H08/H12 runtime DHCP/resolved replaced the
build-only resolver; actual final-ISO networking and Kmod load/unload passed.
Final live EN/PT text-consumer checks passed; ADR-0037 Greek limitations remain
explicit (H12-native-locales.json), without claiming a global Glibc regex fix.

H07 final native metadata closure resolved the initial Systemd/Util-linux
provider ordering and established native APT signed repository, exact versioned
dependencies, conffile ownership, API/layout ownership, bootstrap quarantine and
source/license attribution. See [H07 acceptance](evidence/H07.md). These are no
longer outstanding work.

H12's accepted native follow-up passed Systemd test-namespace and the 48 Glibc
namespace-restricted cases plus io/tst-lchmod. The original H07 outcomes remain
unchanged; ADR-0102 records native execution and fixture corrections. The complete 50/50 report and final-image core hash binding passed together;
see [H12 acceptance](evidence/H12.md). E2fsprogs ADR-0027 does not authorize installer
use of assume_storage_prezeroed. Vim's complete suite passed with its frozen
inputs as nonroot (ADR-0028/0031); preserve those checks on future rebuilds.

Measured regex limitations (ADR-0037): default Gawk misses Greek final sigma in
UTF-8 and ISO-8859-7; Bash nocasematch misses it in ISO-8859-7. Grep/Sed and all
measured English/Portuguese cases pass. Gawk's existing explicit GNU matcher
passes both Greek cases. Preserve default-failure evidence and release limitation;
this is not a global Glibc fix or broad locale correctness claim.

Final foundation Expat review repeated ADR-0041 against all 2,626 image ELFs:
nine dynamic consumers remain (H12-xml-consumers.json). Actual final-live DBus
configuration ownership and unprivileged malformed/oversized rejection passed
with measured UID, CPU/address-space limits and wall timeout. Public CLI/library
use is not automatically sandboxed. New desktop/agent/installer consumers and
their actual untrusted-input entry points still require explicit bounds and
tests in Phase 2; no blanket vulnerability-fix claim is made.


### Current Berkeley DB delivery validation (2026-11-07)

The owner explicitly approved focused Berkeley DB validation for this experimental
delivery. ADR-0092 supersedes earlier instructions requiring the complete standard
Tcl suite before production. Preserve the cancelled and failed full runs as such;
require native C tests, production transaction/reopen/rollback/crash recovery,
actual APT cache interruption/rebuild and existing signed-repository/HTTPS/package
checks before H07 acceptance. All other critical suites and H13/G1 gates remain.
See [ADR-0092](adr/0092-focused-berkeley-delivery-validation.md).
