# Installed native bootstrap qualification procedure

This is a coordinator-only procedure for a disposable installed Toddy QEMU/KVM
VM. It changes that VM's optional packages. Do not run it on the workstation,
accepted foundation images, live ISO or the sole recovery image. Only the
coordinator is the guest writer. Package generation, repository signing and
actual owner authentication are separate operations; this driver implements none
of those by pretending success. No native result has been produced by source tests.

## Independently prepared inputs

Build/stage the real assistant base, helper/policy, exact optional archives and
signed APT repository using the qualified native package pipeline. The initial
VM must have an actual active unlocked local installed owner and no agent or
executor (for local-runtime, no llama-cpp). Retain its backing/recovery identity.
The public keyring must contain no private packets. Install the exact base
source-manifest, fixed trusted source list and public trust/terms inputs described
in [the bootstrap contract](native-agent-acquisition.md). Signing private keys
stay outside the guest and release root. These inputs must be byte-identical to
the code under test, not a more recent source tree.

As root, create the private 0700 directory
`/var/lib/toddy/native-acquisition-qualification-1`. Place protected 0600
`candidates.json` and its real detached `candidates.json.asc` there. The candidate
has exact fields `version:1`, monotonic integer `generation`, `repository` (the
normal fixed repository pins), and `release` (the normal curated release declaration
without qualification_sha256). Its exact package/terms/postcondition/runtime
fields are validated by the same production declaration validator. It is not a
production catalog. No production releases.json is needed to qualify components.

Create root-owned nonwritable
`/etc/toddy/native-acquisition-qualification.json` with exact fields:
`version:1`, `scope:'native-acquisition-components'`, `disposable:true`, numeric
`owner_uid`, and the actual installed `/` filesystem UUID as `root_uuid`.
This marker only prevents accidental target selection. It cannot enable a
production catalog, authorize an owner or make a qualification report pass.
The driver also requires actual ID=toddy, non-live OS, QEMU/KVM, actual logind
owner state, unchanged input hashes and 16 GiB development reserve plus bounded
archive/stage headroom. Preserve all failed contexts; do not replay an uncertain
writer by deleting its journal or changing the marker.

Invoke the fixed trusted source script with `/usr/bin/python3 -I`:
`scripts/qualification/native_acquisition_component.py inspect`.
The source script and installed code must match; generated package __init__.py
is checked by installed pins and does not require a source counterpart.

## Cases and actual owner transport

Run these actions in order against the same unchanged closure:

1. `prepare-stop`; from the actual owner's native graphical session execute the
   exact printed pkexec cancel command, then `run-stop` as root. A canceled
   prepared operation must leave Dpkg/inventory unchanged.
2. `prepare-offline`, then `run-offline`. The script isolates network/mounts in a
   child namespace and hides only the fixed offline repository there when used.
   Real APT failure must defer before native write; no global network/repository
   settings are changed.
3. `prepare-write`; from the actual owner session execute the printed pkexec
   install command. Because this operation is already canonically prepared,
   production deduplication observes it without dispatching a second writer.
   Then run `run-write-crash` as root. Exit **73 is intentional only after the
   actual no-download APT writer returned zero**, before canonical terminal
   persistence. Never kill Dpkg to manufacture this case. Require the retained
   native-write-returned.json and inspect actual operation/package state before
   continuing after any interruption.
4. From the actual owner session explicitly invoke the normal fixed helper's
   `reconcile OPERATION_ID`, then repeat the original `install` identity. Capture
   another installed UID attempting `status OPERATION_ID`, which must be refused.
   Do not substitute runuser/fake PKEXEC_UID for actual Polkit authorization.
5. `observe-reconcile` checks exact native versions, hashes, custody, Dpkg audit,
   inactive services/no local engine, unchanged private user-tree metadata and
   no second package write. Then `report` performs actual gpgv tamper rejection
   and assembles immutable component evidence only if every case passed.

The coordinator captures each real helper call's **terminal result frame only**
from bounded NDJSON, exit status and actual launching UID. Store protected files
`owner-cancel.json`, `owner-install.json`, `owner-reconcile.json`,
`owner-duplicate.json` and `other-uid.json` under the private context. Exact fields:
`version:1`, `exec_path:'/usr/lib/toddy/setup/native_acquire.py'`,
`program_sha256` (actual installed helper hash), `action`, numeric `requested_uid`,
numeric `exit`, `stdout` (parsed terminal result; null is allowed for a denied
Polkit call). Successful owner results must contain the helper's authenticated_uid
and exact original operation/review identity. Never capture PAM passwords,
keyring values or raw package diagnostics. These receipts are evidence inputs,
not authorization consumed by the production helper.

Local-runtime/agent-local additionally require retained
`native-cpu-denial.json` from a genuinely masked-CPU native VM that denied before
APT, with `native_result:'denied_before_apt'`, matching `code_pins`, `trust_pins`
and `package_set_sha256`. Parser fixtures cannot provide this acceptance. Preserve
actual masked CPU/transport logs beside the report; no generic verified callback
is accepted. Existing B03 runtime evidence supports compatibility, not this new
acquisition transport.

## Preview sealing, full flow and publication

Retain the actual component logs, source/guest/backing identities and every case
receipt. Copy component-evidence.json byte-for-byte to
`qualifications/<its SHA256>.evidence.json` and component-qualification.json to
`qualifications/<its SHA256>.json` in the trusted metadata directory. A separate
trusted publisher may now add qualification_sha256 to that exact declaration and
sign an expiring releases.json with `qualification_level:'native-components'` in
the referenced report. No driver signs, downloads keys or installs this metadata.
This creates a preview-only path for the second native test, not final acceptance.

On another clean installed overlay, use the unchanged actual helper/UI and signed
preview catalog to complete every REQUIRED_CHECKS item in releases.py, including
absent-agent setup, exact reviewed closure, owner Polkit, tamper/offline, safe
upgrade/remove/recovery, no automatic service/model/key/grant, reconnect with no
replay, and local CPU/profile checks when applicable. Retain actual runner and
postcondition exit results and package/code/trust pins. Produce independently
reviewed native-full-flow report/evidence with those actual results; changing the
component report's level/check names is not a full-flow test. Any code/archive or
trust pin change invalidates the earlier matching qualification.

Before final publication, bind the actual release root read-only under a
root-owned path and run:

```sh
python3 -I scripts/qualification/native_acquisition_release_guard.py \
  --root /run/toddy-publication-root \
  --expected-key-sha256 PUBLIC_KEYRING_SHA256 \
  --expected-fingerprint INDEPENDENT_PUBLIC_FINGERPRINT
```

Obtain those public pins from the independent publisher lock, not from the
inspected root. The guard re-verifies signatures, expiry/custody, code/trust pins,
all advertised full-flow entries and agent+local coverage. It refuses component
preview reports. Its successful scope is native-bootstrap only; it cannot replace
remaining boot/install/G2 release gates or physical-owner testing.
