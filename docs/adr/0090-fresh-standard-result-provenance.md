# ADR-0090: Bind complete standard results to fresh native provenance

- Date: 2026-11-07
- Status: Prepared; actual provenance/refusal checks passed, complete positive pending
- Extends: ADR-0069, ADR-0087 and ADR-0089

## Decision

Factor the common complete-command, native report, immutable input, reviewed
harness and namespace checks in db_standard_result.py. Preserve the historical
interface's mandatory 460-file recovery seed, measured helper binary and native
C-suite profile. A common metadata shape alone cannot satisfy that interface.
Existing failed-summary qualification and production handoff retain their gates.

Add an explicit --native-build path for a freshly compiled generation. It must
first verify ADR-0089's actual native build receipt, exact reviewed recipes,
source inputs and prepared-byte binding. The standard fixture and input digest
must be exactly those bound by that receipt. Its C-suite and helper binary
hashes come from the verified compilation, not a caller-provided replacement
for the historical recovery seed. Repeat native provenance verification after
checking complete execution evidence to detect changes during review.

Strict fresh success still requires actual zero driver/test exits, the protected
complete producer result, unchanged inputs and raw reports, the upstream success
summary and final strict sentinel. Additionally require all 35 ordered outer
headers from the frozen test.tcl/db_config.h profile. Missing, reordered or
repeated dispatch is an error. Frozen source/configuration must match that plan.
No failed exit is converted to success and no header count estimates duration.

This follows the frozen maintained two-build/full-run pattern in ADR-0032 and
the actual dispatcher/source hashes recorded in ADR-0069. Alternatives rejected:
relaxing the old seed gate would weaken the only measured recovery profile;
accepting a generic manifest without actual compile evidence would lose native
provenance; duplicating every low-level check would risk inconsistent behavior.
Share common checks while keeping distinct mandatory provenance entry points.

## Actual verification and limits

The private native probe reverified the completed fresh compilation and all
10,207 native inputs/483 Tcl files, then refused five inappropriate transitions:
prepared fresh source as a completed suite, historical active source as complete,
active full source through the fresh interface, prepared source through the
historical interface, and a different compiled-generation/input binding.
Actual full driver 1107192 remained live. Full/fresh source ownership and modes
were unchanged; no full-source custody or qualification record was created.

The already sealed historical coverage witness also reverified with the same
receipt 0a2b9b17cf57a0de76dc20ce426f784c4e92aa401d44a1d3f43817726e6dccb2.
Native gate report:
99fbb0ba8e2878c6a090b35d1ac2748786865d94ce4c581da0943877714af9be.
Result-verifier module:
3344855183598384e308d6e95a60f928acc45a8d4d0c97c332f29b1f9d60d692.

Two additional local methods check retained recovery-seed enforcement, C-result
binding, complete ordered dispatch and generation/manifest/acceptance-flag binding.
The isolated test initially lacked its module import path; setting that explicit
path fixed the test harness. All four focused tests and all 173 local tests pass.
These parser checks are not a fabricated native full-suite positive result.

Neither complete strict fresh success nor complete historical qualification has
been available to verify positively. The normal fresh recipe still needs private
full dispatch plus portable failed-summary coverage/qualification integration.
Production nomination is unchanged, APT remains gated, and H07 stays 124/126.
Do not launch another complete suite from the fresh prepared copy to test this
refusal path or substitute its manifest into the already running execution.
