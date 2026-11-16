# Native candidate generated resources and independent review

The fixed source-only resource recipe fills the missing first-generation
attribution step. It is not a production finalizer, signed qualification report or
image acceptance. The production factory still requires reviewed expected entries,
complete image hash, actual finalizer reports and detached boot evidence.

The coordinator first uses the actual signed archive closure and
`image_assemble.unpack_native` under its existing designated target guard/build
lock. Native Dpkg runs inside the selected target chroot, never using workstation
Dpkg or copying a dirty build root. The fixed first stages are
`/sources/stage/toddy-offline-image-1/root` and
`/sources/stage/toddy-live-image-1/root`. Their exact archive/database receipt and
dev/work/root inode pins must be adopted read-only by the assembler before
continuing. An uncertain stage is preserved, never unpacked or generated again.
The16GiB development reserve and archive/root/compression headroom remain required.

`resource_recipe.qualify(assembly, manifest, policy, LinuxDisk())` accepts the
assembler's pinned root. The assembler owns the fixed `qualify-base`/`qualify-live`
entry points; it supplies the same protected reviewed account/PAM policy and
prepared manifest as finalization. There is no arbitrary command/path/plugin
field. The source recipe preflights complete cache input namespaces, fixed native
argv, selected tool/output hashes and initial ownership/database state before
writing intent. Literal locked service accounts, fresh directories, exact GDM
service links and a source-attributed empty lost+found directory follow. This
ordinary candidate directory is not evidence of a formatted ext4 installation.

Known native cache generators run inside the fresh root. The shared frozen H10
loader helper uses ldconfig-X-i, verifies selected SONAME/search namespace/native
2.44 readback, and omits only its exact fresh inode auxiliary cache. No builder
cache or user/provider credentials are copied. Any changed package-owned output
is a blocker requiring native record/archive requalification, never a generated
entry override. Unknown output, maintainer scripts, unselected Dpkg info entries,
private/runtime state, xattrs, special nodes or cross-device entries are refused
or explicitly retained as blocked candidate output. Cache/tool commands remain
those already allowed by NativeFinalizer.cache_command; no new framework/version.

The first native run emits protected candidate artifacts outside the image:

- resource-intent.json binds manifest/policy/source/root identity before effects.
- candidate-generated-entries.json uses the exact production metadata+origin
  schema. It never reattributes selected package files.
- candidate-clean-image-manifest.json is the complete actual path/metadata/hash
  snapshot, including owned entries. It is a candidate, not a claim of cleanliness.
- candidate-resource-receipt.json binds those files, actual native commands,
  observed cache/tool/namespace digests, loader receipt and explicit blockers.
  production_ready and finalizer_qualified remain false even with no blockers.

Retain actual native stdout/exit/operation logs in the coordinator's private
custody. Independently review every generated path and metadata/origin, literal
account/PAM/service policy, native Dpkg exact configured set, complete cache union,
private-state hygiene and source/tool/namespace pins. A blocked cache output
requires a separately qualified ownership/archive correction and a new reviewed
source generation, not editing the candidate receipt to say passed.

Only after that review may the coordinator place exact reviewed bytes at the
fixed inputs' generated-entries.json and expected-image-manifest.json. Preserve
candidate1 unchanged. Assemble NEW generation2 from the same immutable archives,
then run the real NativeFinalizer with those exact expected maps/hashes; it must
regenerate all resources and independently match the whole image. Never call the
finalizer with a placeholder image hash and reinterpret its eventual failure as
success. A second-root mismatch is a real reproducibility/ownership failure.
The live GNOME account/session transform occurs only after base finalization and
requires its own complete delta/snapshot custody before media compression.
Actual image/installer/firmware/privacy gates remain separate and mandatory.

Source fixture tests exercise closed command plans, complete namespace changes,
literal origin mapping and unknown/owned-drift refusal. They run no native
producer, Dpkg, VM or disk operation and produce no native qualification artifact.
