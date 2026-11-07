# ADR-0072: Compose fresh root assembly with independent native payload checks

- Date: 2026-11-07
- Status: Orchestrator prepared; native payload audit and readiness refusals verified
- Scope: H10 intermediate root and H11 refreshed release root; full assembly/boot pending

## Decision and sequence

Compose the previously measured components in h10/assemble_root.py. Its default
profile requires H09 completed and H10 in progress; --release instead requires
H10 completed and H11 in progress. The release profile removes optional Python
QA through the verified native operation after the actual ownership transfer.
Neither profile may infer milestone acceptance from private component probes.

The standalone CLI owns build.lock exclusively, refuses unfinished build/sync
markers and requires native Squashfs tooling recipe/postcheck success. Do not
invoke it beneath run_step.py, which already holds that lock. One outer native
Dpkg read transaction covers selection through final verification; its nested
database stage shares ADR-0059's descriptor registry. Require unchanged source
database, own records and account baseline throughout the operation.

Image/evidence destinations must be new, disjoint and inside designated guest
staging, with protected physical root-owned parents. Preserve partial attempts.
Reserve space for the fresh tree, retained Tar evidence and 2 GiB extra; the
estimate deliberately overcounts hardlinked/sparse data. The sequence is:

1. Verify source package inventory and archives; copy explicit payload with native Tar.
2. Recreate runtime/cache directories and stage validated native Dpkg metadata.
3. For H11 only, remove optional QA through native package operations.
4. Generate fresh accounts/identity, live fstab/time/resolver settings,
   offline service enablement and the live-console profile.
5. Generate loader cache and Info index; capture the final ACL sidecar.
6. Independently audit native ownership/payload; H11 also retains and passes
   the narrow marker review.
7. Save the complete physical image manifest and recheck source stability.

Each action records durable intent and a separate hashed report. Failure leaves
assembled=false; no stage is merged, emptied or automatically replayed. Native
failure output is preserved when available. Even assembled=true only describes
an uncompressed root. Generated/unowned state, dependency/credential/identity/
license audits, compression/initramfs and actual boot remain acceptance gates.

## Independent owned-payload audit

h10/image_payload.py reads the image's configured native identities and complete
file/checksum namespaces, verifies each own archive SHA-256 and record, then
checks every owned path's physical location, type, mode, UID/GID, file SHA-256
or link target. Shared directory metadata must agree; duplicate non-directory
ownership is refused. Actual package bytes must also match native stored MD5
values. MD5 here checks native metadata consistency, not authentication.
Database/provenance changes during inspection are refused.

Ordinary modified conffiles fail. The live profile permits only the exact
previously reviewed fstab text and fresh runtime/APT directory metadata. It
retains fstab's native conffile identity and original MD5, verified against the
matching owned builder file. Every transformation reports original/final data.
Positive full live-profile reconciliation awaits actual H08/H10; the measured
private positive check uses unchanged native package payload. Unowned/generated
state and dependency closure remain explicitly unverified in the report.

## Native evidence

```sh
python3 scripts/host/probe_image_key_marker_review.py --payload
python3 scripts/host/probe_root_assembly_preflight.py
```

A configured eleven-package disposable native root passed: 19,170 unique owned
entries, including 18,578 files/links, 19,371 file-list rows, 11,954 MD5 values
and four conffiles. All eleven own archives were verified. Ten real corruption/
refusal cases passed: executable bytes, ordinary conffile bytes, missing file,
link target, numeric owner, directory mode, native MD5 value, extra ownership
path, own archive identity and a live transformation without owned base config.
The restored root passed again. The same invocation also passed all nine
ADR-0071 marker-review negative cases. Installed builder state was unchanged.

Raw .local/logs/h11-image-key-marker-review-<sha256>.log SHA-256:
9005fba5a5a09bcc023d1958e910f268f484397eeec9b54c724c6fee54e9e929.
Payload component SHA-256:
3a7da48f2daa5cbbf1557d2ec18ed1403b04c945a97ecaca6291a78b4e29afd5.

The orchestrator probe rejected both premature production profiles and six
unsafe output layouts. Its actual read-only source-inventory action reached
the known unfinished H07 Info-index discrepancy, durably recorded failure and
created no image. This proves readiness refusal, not successful full assembly.
Full positive execution and boot remain pending after prerequisites pass.

Raw .local/logs/h10-root-assembly-preflight-<sha256>.log SHA-256:
1ef87e141cbb5f0420935cb9d7d5b75a209384ae13ce22c1354433d96a109cee.
Assembler SHA-256:
19f4c65e955055406bfd3e5bf19669d2000eff066902c86345828ae5da4916bb.
All 154 local checks pass. Unexpected probe failures retain their fixture;
successful fixtures are removed only after native logs/reports are captured.

## Alternatives, consequences and sources

Whole-builder copying imports mutable/private state. Reinstalling every unchanged
package adds unnecessary maintainer-action semantics. Accepting all changed
conffiles or only checking package counts misses real corruption. Explicit copy/
generation and independent native payload verification preserve attribution.
Retained Tar evidence and full manifests cost disk space but aid recovery.

This composes ADR-0048, ADR-0055 through ADR-0066 and ADR-0071 without changing
frozen package versions or acceptance gates. Re-inspected primary sources:
LFS 13.1-systemd 7.5 Creating Directories, SHA-256
88ba0fe23f1c8b0c9560375ffb427aa9bbc99602f05c4f94f6726756daf0882f;
10.2 Creating /etc/fstab, SHA-256
5b89121d3b583e801464d4bc5052405499c66ad15f8406d9452d6c83f4b15614;
and frozen Dpkg 1.22.22 man/deb-md5sums.pod, archive SHA-256
d5ea9f132deec8030b50ab2a02ade2b49f0c7a195805a302c8301156fe833a57.
The Dpkg manual distinguishes metadata integrity from security purposes.
The live fstab/root-home changes remain the previously documented extensions;
no physical disk or installed-host configuration is touched.


ADR-0073 subsequently adds explicit generated-state attribution and full physical
namespace comparison inside this prepared orchestrator. Its partial native
component checks pass; complete positive foundation assembly remains pending.
