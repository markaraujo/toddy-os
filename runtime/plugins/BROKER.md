# Canonical broker integration

The service binds Integrations to each captured profile context. ConfiguredEngine
receives only the fixed broker descriptors; MCP server descriptions cannot add a
tool or capability. Core validation, task-pinned revisions, current unlocked owner
session, tool-call/deadline budgets, canonical operation hashes and MemoryEngine's
admission gate remain authoritative. Task metadata stores no tool arguments,
results, prompt or skill body. Results are explicitly untrusted data, including
skill instructions; they cannot grant root, tools, credentials or provider use.

## Release reference MCP

`release-package-info(package)` is an actual local MCP read operation. Its reviewed
server reads the bundled `release.json` projection of the committed accepted B02
runtime manifest and returns exact component version/source/notices metadata.
Every result says **release baseline reference; installed state not queried**.
It is neither an echo nor a claim about the currently running system. The bundle
contains source, projection, attribution NOTICE and exact SHA256 manifest.

The optional integration is absent by default. The production catalog reads only
these fixed root-owned, non-writable, non-symlink locations:

- `/usr/lib/toddy/plugins/bundled/release-reference/{server.py,release.json,NOTICE,manifest.json}`
- `/usr/share/toddy/plugins/release-reference.receipt.json`

The receipt has exactly receipt_version (integer 1), id (`release-reference`),
qualified (literal true), package_version, package_archive_sha256,
confinement_evidence_sha256 and manifest_sha256. All hashes are exact 64 digit
SHA256. The native package transaction must create this reviewed receipt only
after actual qualified containment/source/legal/package verification. Its archive
hash refers to the installed signed package, so the receipt is a separately
managed generated path, not a circular self-hash embedded in that same archive.
Root ownership is the trust boundary; a self-authored user JSON is insufficient.
No source test supplies or installs a production qualified receipt.

Missing, malformed, unqualified, changed, wrongly owned or writable payloads are
unavailable. There is no environment, JSON or service CLI override for execution
paths or catalog trust. A test-only constructor dependency injects a clearly
labeled source binding to exercise real child containment on the host.

Activation requires all three: native qualified payload, current profile
`extensions.enabled` containing release-reference and `tools.enabled` containing
release-package-info, then separate explicit owner activation of the exact shown
manifest hash. `GetIntegrations(profile_id)` returns bounded availability/pin/
activation metadata and selected skill metadata. `ConfigureIntegration(profile_id,
expected_revision, operation_json)` accepts only version 1, id release-reference,
operation enable/revoke and, only for enable, manifest_sha256. There is no imported
server registration, arbitrary host command, keyring handle, account or egress.

Approvals live in the canonical per-profile SQLite DB, never portable profile
JSON. Clone/import excludes them. Update changes the source pin and needs a new
owner activation. Every call verifies current opt-in/approval/package identity;
revocation and normal broker Stop kill the owned Bubblewrap namespace. Profile
apply/restore reconciles disable and clears its old approval. Removing the native
package also makes later calls unavailable. Restart the broker after installing
new optional native capabilities so profile semantic validation sees the same
qualified capability set. There is no unconfined fallback.

## Skills are versioned data

ProfileStore and the existing FD staging/import/export now accept data paths
`skills/<id>/SKILL.md` and `skills/<id>/references/<relative-name>`. IDs need not be
shipped: owner-created skills with valid bodies resolve their own capability.
The exact two-field plain name/description parser is shared by the existing file
loader and canonical validator. Unknown hooks/paths, traversal, orphan resources,
invalid UTF-8 and bounds fail before activation. The complete bundle is at most
128 entries/8 MiB; body, metadata and reference limits remain 32 KiB, 4 KiB and
256 KiB. Every byte participates in the existing immutable revision hash and task
pin. Normal profile CAS, storage limits and recovery still apply.

Explicit profile import/clone preserves selected skill data while resetting
provider connections, native tools, extensions, schedules, memory and authority.
References are data even when their prose requests commands. Nothing imports a
module or runs a helper from a skill. The shipped explain-system is pinned in new
profiles. Old stores remain in place; only their installed, hash-bound default
may be used as a labeled legacy fallback. A changed default cannot silently
replace that fallback within a service lifetime.

Only bounded selected skill names/descriptions enter initial tool metadata.
`load-skill(skill_id)` loads one selected task-pinned body on actual demand.
`read-skill-resource(skill_id, resource, offset=0)` reads an explicit selected
pinned reference page, returning next_offset/complete and its source hash. It
never scans arbitrary files, automatically includes references, runs code or
grants a tool. Current profile disable blocks another load even when an older
immutable task revision still contains that skill. Edits do not rewrite already
pinned task instructions. Owner Stop remains available for the running task.

Tool result bytes are bounded by the profile context budget and an independent
64 KiB ceiling. Oversized bodies fail clearly rather than silently truncating
instructions. Reference pages are explicitly paged. Provider actual token/context
checks remain independent; byte ceilings do not claim an exact token estimate.
The ordinary native `tools` capability list stays compatible; `integration_tools`
reports these additional model-facing data tools. No hosted/model call happens
for capability inspection or direct owner-selected skill reads.

## Validation and remaining native work

Focused host tests use the actual Bubblewrap child and real initialize/list/call
against the useful release-reference server, including a broker-routed call,
source pin change/missing package/revoke, actual child termination and canonical
operation journal. The model adapter and package receipt binding in that test are
explicitly synthetic; no native package/model acceptance follows. The host private
session-bus fixture imports a custom skill through an actual sealed FD, inspects
metadata without instructions and completes one owner-requested canonical data
read with no workspace effect. Existing containment probes retain dummy secret,
filesystem, bus and egress denial checks.

Parent native integration must stage the optional plugin modules/bundle/notices,
qualify the actual selected Bubblewrap/kernel boundary, use the existing signed
native package/ownership pipeline, generate the root-managed receipt, then test
activation/call/timeout/revoke/Stop/removal through the real user service and
configured agent. Broker packet dependencies now include integrations.py and
skill_documents.py plus changed profiles/profile_registry/core/configured_engine/
service/XML. Optional backend modules are plugins/mcp.py, limits.py and skills.py;
missing optional backend cannot prevent the ordinary broker from starting.
Browser native launch/accessibility is a separate optional integration slice.
No guest, provider account or native acceptance is claimed by this commit.
