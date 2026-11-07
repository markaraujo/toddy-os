# Rebuild the foundation from frozen sources

This procedure rebuilds the command-line H01–H13 foundation. It does not start
Phase 2. The accepted artifact and actual verification are linked from
[evidence/H11.md](evidence/H11.md) and status.json. A rebuild must establish its
own acceptance; this is command/source reproducibility, not a claim that a second
complete build or byte-identical ISO has already been demonstrated.

## Separate execution state and target

Use a separate clone/branch and a fresh .local directory. Do not reset the
published release's status or reuse an active VM's disks. The current scripts
use the fixed Docker name toddy-builder and loopback SSH port 2222: only one
builder may run at a time. At a quiescent boundary, stop the original builder
with its own `python3 scripts/host/vm.py stop`; keep its disks/checkpoints intact.
Never copy a live disk. See [RECOVERY.md](RECOVERY.md).

```sh
git clone --no-hardlinks /path/to/toddy-os /path/to/toddy-os-rebuild
cd /path/to/toddy-os-rebuild
git switch -c rebuild/local-execution
python3 - <<'PY'
import json
from pathlib import Path
p = Path('status.json')
s = json.loads(p.read_text())
for row in s['milestones']:
    row['status'] = 'not_started'
    row['evidence'] = []
s.pop('active_work', None)
s.update(next_story='H01', gates={'G1': 'pending', 'G2': 'pending'},
         current_scope='Independent foundation rebuild; no local acceptance yet.')
p.write_text(json.dumps(s, indent=2) + '\n')
PY
make dashboard
git commit -am 'Initialize independent rebuild execution state'
```

Do not push this local execution-state reset to the release branch. Mark each
story in_progress before work, collect new evidence, run make check and complete
it only after its criteria pass. Use `scripts/project.py set STORY STATUS
--evidence docs/evidence/rebuild/STORY.md` for the independently written evidence.
Commit progress before boot harnesses, which deliberately refuse dirty inputs.
The old release evidence files remain historical records, not new-run results.

## Host, sources and H01–H06

Follow the measured host/VM preparation and H03–H06 commands in [BUILD.md](BUILD.md).
Use Linux x86_64, Docker, KVM access, Python 3.12+, SSH, curl, tar and Git. The
measured builder uses 12 vCPUs, 12 GiB RAM and 8 GiB swap; ordinary builds use
8 jobs and compression 2. Preserve at least 100 GiB workstation free space,
plus expected new checkpoint/image allocations. A full build plus retained
paired checkpoints can occupy hundreds of GiB. Inspect actual resources first.

Run the complete input acquisition before sync; none of these commands installs
an upstream archive directly into the workstation:

```sh
python3 scripts/host/fetch_image.py
python3 scripts/fetch_books.py
python3 scripts/fetch_sources.py
python3 scripts/fetch_security_overlay.py
python3 scripts/fetch_security_overlay.py --supplemental
python3 scripts/fetch_compiler_reference.py
python3 scripts/fetch_bash_reference.py
```

The source and supplemental locks contain exact versions, URLs and SHA-256;
book archives are pinned in config/books.lock.json. Source mismatches stop
extraction. Fetching may record a different successful mirror URL; review that
metadata difference without changing the frozen source hash. Preserve upstream
and original-component license notices. The guest provisioning distro is build
infrastructure; none of its binary packages becomes the Toddy target base.

Only prepare-target.sh --apply inside the serial-checked disposable target may
partition its blank virtual disk. Never supply a physical host disk. Complete
H03 package ownership/conflict/runner probes before H04. H04, H05 and H06 have
ordered drivers. Demonstrate the H06 controlled checkpoint restore, not just
save a checkpoint. Capture driver exit and every postcheck; a process without
an exit record is unfinished work.

## H07 exact fresh recipe order

The following is the canonical fresh sequence, not the list of historical
partial-build recovery attempts. All paths are inside the designated builder.
After H06 acceptance, set H07 in_progress, commit and sync public inputs with
`python3 scripts/host/sync_build.py`. Run one dispatcher at a time.

Use this helper inside `/opt/toddy-build/scripts/build`:

```sh
set -euo pipefail
step() {
    local name=$1 recipe=${2:-$1}
    if test -f "/var/log/toddy/build/h07-$name.success.json"; then
        return
    fi
    python3 run_step.py "h07-$name" "h07/$recipe.sh" \
        "h07/$name-check.sh" --user root
}
```

For a resumed build first inspect actual marker contents (recipe and postcheck
exits zero), packages and partial stages. Do not use that presence shortcut to
bless a hand-created or damaged marker. The runner refuses existing successful
steps, records source/recipe/install manifests and preserves failed attempts.
Use durable detached launch logs and captured exit codes as in BUILD.md.

Execute the groups below in order, using `for name in ...; do step "$name"; done`:

```text
man-pages iana-etc glibc-build glibc-install glibc-locales tzdata zlib bzip2 xz
lz4 zstd file readline pcre2 m4 bc flex tcl expect dejagnu ninja pkgconf
binutils-build binutils-install gmp mpfr mpc attr acl libcap libxcrypt
shadow gawk gcc-build gcc-install
ncurses sed psmisc gettext bison grep glibc-test-locales bash
libtool gdbm gperf expat inetutils less perl autoconf automake openssl
libelf libffi sqlite mpdecimal build-resolver python
flit-core packaging wheel setuptools meson
kmod coreutils diffutils findutils groff grub gzip iproute2 kbd libpipeline
make patch tar texinfo markupsafe jinja2 systemd dbus man-db procps-ng
util-linux e2fsprogs
ca-certificates nghttp2 curl libuv libarchive cmake libmd time xxhash googletest
libgpg-error libgcrypt libassuan libksba npth gnupg vim-glvs-inputs vim dpkg
```

Then run the owner-approved Berkeley delivery profile with its normal package
marker and unchanged postcheck:

```sh
step berkeley-db berkeley-db-focused
bash h07-perl-test-tools-driver.sh
bash h07-base-ownership-driver.sh
bash h07-final-base-driver.sh
```

The Perl driver uses the committed ordered config/native-perl-test-tools.lock.json
and then Triehash/Which/Libseccomp/Tcsh. Final-base builds/tests APT, establishes
the Python alias, repeats ACL checks with final tools, owns API/layout/build
support, quarantines bootstrap files and closes native package metadata.
Its installed APT tests exercise signed repositories, HTTPS, dependencies,
conffiles, tampering and actual Berkeley cache interruption/rebuild/corruption.
ADR-0092 permits the focused database profile; it does not waive compiler/libc
suites, image verification or native follow-ups. Failed full Tcl runs remain
historical failures/cancellations.

Do not use gmp-install.sh as a fresh build: it only resumes an already compiled
historical tree. The fresh math driver selects gmp.sh and recognizes an already
accepted historical gmp-install marker. The package-manager driver accepts
normal GnuPG or its verified historical recovery marker. A recovery recipe is
appropriate only when its exact documented partial-state prerequisites exist.
On any new failure, retain raw output, diagnose the cause, verify the correction
and retry from the relevant checkpoint; never import an old success marker.

## H08–H11 and image assembly

After the eight final H07 audits and native Dpkg/APT checks pass, save/verify a
cold paired checkpoint and validate the restarted target. Advance each gate
only on fresh evidence; sync committed status before its native driver.

| Story | Native execution inside `/opt/toddy-build/scripts/build` |
| --- | --- |
| H08 | `bash h08-driver.sh` |
| H09 | `bash h09-kernel-driver.sh`, inspect kernel/config acceptance, then `python3 run_step.py h09-bootloader h09/bootloader.sh h09/bootloader-check.sh --user root` |
| H10 | `bash h10-tools-driver.sh`, then `bash h10-live-driver.sh` |
| H11 | `bash h11-python-qa-driver.sh`, then `bash h11-release-driver.sh` |

H09 boot-sector writes are allowed only on the validated virtual target. Save
and verify h09-boot-ready while the builder is stopped; run actual BIOS/UEFI cold
overlay tests and restart/remount the builder. H10's validation ISO must pass
its real live console before H11. Media dependencies are source-built once in
H10 under ADR-0096; this does not accept H11 early.

Assemblers own build.lock: do not wrap their CLIs in run_step.py. They refuse
existing generations; preserve failed output before retry. Media-only recovery
uses h10-media-driver.sh or h11-media-driver.sh after verifying retained
compression, without rebuilding accepted packages/root. ADR-0101's explicit
whole-disk probe is required for hybrid USB. Preserve all per-stage reports.

Export the exact release image inventory using:

```sh
python3 -B export_inventory.py --image /mnt/lfs/sources/stage/h11-release-root
```

Independently verify source/component record hashes, runtime/ownership/fresh
identity and credential review against the assembled image. Copy ISO, its native
result.json, components.json and SHA256SUMS outside Git; rehash the actual copy.
The delivered image excludes optional Python QA while builder tests remain.
Project-original licensing D10 remains a separate public redistribution decision.

## H12/H13 verification

Test the newly built ISO, never a previous generation. For each of BIOS/UEFI and
CD/USB, run `scripts/host/live_boot_test.py ISO MANIFEST --firmware MODE --medium
MODE`; include offline boots with --offline. Run `live_recovery_test.py ISO
MANIFEST --case rescue`, --case missing and --case corrupt. Then boot the intact
original again. Additional --probe security and --probe regex profiles retain
final-image XML/locale boundary evidence.

Run `scripts/host/boot_test.py bios --checkpoint h09-boot-ready --timeout 900
--regressions`. It preserves the cold backing, uses a private overlay and executes
upstream native namespace tests with their original runtime and arguments
(ADR-0102). Check all exits, full evidence transport and final-image binary hashes.
Keep remaining source-qualified unsupported/known outcomes distinct from passes.

Audit every G1 criterion against these results. Record physical hardware pending
unless actually tested. Deliver artifact/checksum/component inventory, live and
recovery instructions, exact source commit and limitations. Stop at the explicit
H13 owner-review boundary; technical G1 acceptance does not authorize B01.

After H12 passes and H13 is active, `scripts/host/export_foundation.py ISO MANIFEST
INVENTORY DESTINATION` creates a fresh local release directory, validates the
artifact against its independent review, bundles and reads back every
corresponding source archive, and verifies the copied ISO. Inputs and destination
must be physical project-local files/directories; binaries remain outside Git.
Add the final committed source history with `git bundle create DESTINATION/
toddy-source-history.bundle HEAD` (use a single continuous path in the command).
Keep raw test logs, native component records and checkpoint references with the
handoff. Do not advertise a partial export as accepted G1 or a public release.

After the G1 acceptance commit, run `python3 scripts/host/finalize_foundation.py
DESTINATION` with the same directory. It revalidates exported artifact hashes,
creates/verifies the full Git bundle, writes the final source revision and
checksums, and reads every delivered file through sha256sum. It refuses a dirty
checkout or mismatched previous bundle. Preserve an older bundle before binding
a different revision. Inspect release-summary.json and SHA256SUMS before handing
the export to the owner. Native build and raw test archives must already match
the separately reviewed H13 export record; this command never invents tests.
