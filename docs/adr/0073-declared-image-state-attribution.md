# ADR-0073: Attribute generated image state to explicit declarations

- Date: 2026-11-07
- Status: Native component checks passed; full foundation image integration pending
- Extends: ADR-0072 assembly and independent package-payload verification

## Decision

An installed-package audit cannot identify unexpected unowned files or verify
generated account/database/cache state. Add h10/image_attribution.py and require
its separate result in the prepared root assembler. Compare the entire physical
image namespace with declared origins and expected bytes/metadata; do not accept
whatever happens to exist merely by recording its hash after assembly.

The native Tar copier now preserves its already verified input manifest in the
private evidence directory and returns its SHA-256. This retains source xattr
hashes and hardlink groups without trusting a later source read. Package records
provide owned path/content/type/mode/UID/GID expectations; the verified copy
provides their extended metadata. Root metadata is attributable to that same
copy. Remaining native packages after optional QA removal define the owned set.

Generated declarations cover only the reviewed producers:

- Fresh runtime/APT directories use the established numeric metadata policy.
- Native Dpkg metadata is captured after the last image package operation,
  restricted to its reviewed physical file/directory schema and native modes.
- Account files are derived again from the source baseline, including locked
  credentials, empty subordinate allocations and empty machine-id.
- The live fstab/time/resolver and console profile use their exact reviewed
  text/link definitions. The service profile declares fifteen exact native
  enablement/alias/mask links, with owned unit targets.
- Loader cache, Info index and ACL sidecar use fixed output paths and the hashes
  from their separately verified native generation reports.

Every entry records its package/generator origin. Missing, extra or changed
paths fail. Generated metadata requires expected modes, UID/GID and no inherited
xattrs. Source package xattrs must remain equal to the verified copy, and the
remaining native hardlink groups must match exactly. Physical traversal refuses
special nodes, redirected parents and filesystem crossings. No external symlink
target is followed to import data. All reports remain outside the image.

The assembler preserves the declaration plan and a separate comparison result
before recording an assembled root. This extends attribution rather than
replacing native package, dependency, full credential, license or boot checks.
The comparator explicitly does not claim that it recognizes arbitrary secret
contents. A source change needs a reviewed declaration; an unexpected file is
not authorized by merely adding its observed bytes to the plan.

## Measured native evidence

```sh
python3 scripts/host/probe_image_key_marker_review.py --attribution
python3 scripts/host/probe_selected_root_copy.py
python3 scripts/host/probe_offline_services.py
python3 scripts/host/probe_root_assembly_preflight.py
```

The first probe repeats the real eleven-package native root and existing payload/
marker checks, then creates fresh account state with the actual account component.
All 19,214 entries are declared; no missing/extra/changed path remains, and all
686 native hardlink groups match. Ten new cases fail as intended: extra build
data, an outside symlink, altered root lock state, account mode, account xattr,
nonempty machine identity, changed native database bytes, a split native hardlink
group, a special node and a traversal declaration. Restoring the fixture yields
a passing comparison again. No installed builder state changes.

Raw .local/logs/h11-image-key-marker-review-<sha256>.log SHA-256:
fba7ad96845c469dcec2df0b90db1df78851e031271a6bef78021c15143d05ea.
Attribution component SHA-256:
3097eef9b4d20c2736d8a1b6d4c7d4bf0e0e5e9c8c3d37770313dfc8a9d1e1df.
This fixture verifies native packages, database and accounts; it is not the full
foundation profile, an ISO or a native-kernel boot.

The native copy probe verifies preserved input-manifest contents/hash alongside
its existing exact ACL/capability/xattr/hardlink/sparse-copy and refusal checks.
Raw .local/logs/h10-selected-root-copy-probe.json SHA-256:
305a53868c457a2ae8ada35539dad9faa7313ef61c72624536cd6eb2ab733281.
Copy helper SHA-256:
4c9e675a968f5547a7d07091073f1ae7ca5a8815559120269b8297da3bb270ed.

The fifteen declared service links match actual source-built Systemd offline
enablement exactly. Existing repeat/check-only/preset tests and eleven negative
boundaries pass. Raw .local/logs/h08-offline-services-probe.json SHA-256:
51fa1afe3e0f50c92dff4076f21b46bbdeddaa215f9b35cdb8e81b3be7781d4e.

Both production gates, six unsafe destinations and the known actual H07 Info-
index readiness refusal still pass with the composed modules. No full image
is created. Raw .local/logs/h10-root-assembly-preflight-<sha256>.log SHA-256:
a25e6dc4e4007f8ebbdb9168bcadd4db856d6036fb59407b1f4d6e5b8f187a29.
Assembler SHA-256:
03f68f8369dabaa945bb6f85e744dc8494a6a36295c758e46d33176745567c7a.
All 154 local checks pass; positive full-profile assembly remains pending.

## Sources and consequences

Re-inspected LFS 13.1-systemd 7.6 account blocks from chapter07/createfiles.html,
SHA-256 f042fcc6b3389673a39fbc7c99eaca8b2589fce453d87c5b01366408af3d0867.
ADR-0055 and ADR-0065 define the fresh identity and additional APT account policy.
Service declarations match the actual hash-verified Systemd 261.2/DBus 1.16.2
units and operations preserved in the native report; frozen Systemd source
archive SHA-256 ed1059ff964f5df35b6056434cc17cc83f86dc913f10489948a0b19b6081c5ec.
Native Dpkg metadata/ownership and source-copy mechanics retain ADR-0059/0072
semantics. No source versions, package acceptance or boot gates change.

Compared with a broad pathname allowlist, exact declarations detect unexpected
contents and identities inside otherwise legitimate directories. Compared with
recording the completed tree as its own specification, they can detect missing
or accidental generator output. This costs another manifest/comparison pass and
requires explicit review when source recipes or service profiles legitimately
change. Full credentials, dependency closure, compression and actual boot remain
separate required evidence.
