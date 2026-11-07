# Toddy OS — Current status

Updated: 2026-11-06

Bootstrap: ready_for_development

Implementation: H01-H06 validated in KVM. H07 has 124 accepted source-built packages and a verified cold pair. Corrected Berkeley DB C/focused tests and 483-file source comparison passed; complete standard suite running. Perl packlist metadata correction is prepared, not installed; APT/final closure and G1/G2 remain pending. No Toddy ISO. Owner review boundary: deliver H13/G1 for testing and wait for explicit approval before B01-B13.

Foundation: **38%** · Agentic desktop: **0%**

G1: pending · G2: pending · Next: **H07**

No milestone earns credit without completed acceptance evidence.

## Active story: H07 — Build and test the final base system

The 38% phase total counts completed stories only. H07 is still in progress; its 24 points are not yet counted. Passing this story would raise the phase total to 62%.

Last verified: 2026-11-07 01:01 UTC

Verified:

- 124 of 126 currently planned H07 packages installed, configured and accepted; 2 pending (Berkeley DB and APT). All 124 have own-build/source provenance.
- Compiler/libc/binutils suites classified with preserved evidence; required native-kernel follow-ups remain open.
- Full ACL retest, API/layout ownership and native configuration correction passed.
- Verified paired cold checkpoint at the 124-package boundary.

Running: Berkeley DB standard suite continues in replication (block 23, Rep026), retaining two diagnosed FAIL entries. All eleven multi-process cases passed separately with the real native helper, plus five negative checks. The repmgr007 bounded-wait correction passed three native repetitions; its complete twenty-case group is still running (Repmgr029). Corrected fresh/recovery inputs are prepared and frozen, but not synchronized into the active attempt. Full-suite/package acceptance remains pending.

Remaining:

- Finish the complete database suite, then production install and transaction/reopen postchecks; later access-method matrix plans 135 x 9 dispatch entries, including inapplicable skips.
- Build/test APT with signed-repository and HTTPS failure/recovery checks; apply the owned Python command alias.
- Quarantine 931 reviewed bootstrap paths, close metadata for all 126 planned packages and pass seven final audits plus Dpkg/APT consistency checks.
- Save final H07 evidence and a verified paired cold checkpoint of both VM disks before accepting the story.

[Acceptance evidence](docs/evidence/H07-progress.md)

| Story | Phase | Weight | Status |
| --- | --- | ---: | --- |
| [H01 — Inspect host and select isolated build environment](stories/H01.md) | foundation | 4 | completed |
| [H02 — Freeze books, sources and integrity manifest](stories/H02.md) | foundation | 4 | completed |
| [H03 — Prepare target, build user and package ownership](stories/H03.md) | foundation | 4 | completed |
| [H04 — Build the cross-toolchain](stories/H04.md) | foundation | 10 | completed |
| [H05 — Build temporary tools](stories/H05.md) | foundation | 8 | completed |
| [H06 — Enter chroot and create recoverable checkpoint](stories/H06.md) | foundation | 8 | completed |
| [H07 — Build and test the final base system](stories/H07.md) | foundation | 24 | in_progress |
| [H08 — Configure identity, services and basic networking](stories/H08.md) | foundation | 6 | not_started |
| [H09 — Build kernel and boot configuration](stories/H09.md) | foundation | 8 | not_started |
| [H10 — Assemble the live system](stories/H10.md) | foundation | 8 | not_started |
| [H11 — Produce hybrid ISO and artifact manifest](stories/H11.md) | foundation | 6 | not_started |
| [H12 — Verify foundation boot matrix and recovery](stories/H12.md) | foundation | 6 | not_started |
| [H13 — Deliver and accept foundation gate G1](stories/H13.md) | foundation | 4 | not_started |
| [B01 — Evaluate desktop, harness, licensing and resource budgets](stories/B01.md) | agentic | 5 | not_started |
| [B02 — Build the graphical desktop and essential applications](stories/B02.md) | agentic | 10 | not_started |
| [B03 — Integrate provider adapters and local inference](stories/B03.md) | agentic | 8 | not_started |
| [B04 — Implement native tools and privileged execution](stories/B04.md) | agentic | 8 | not_started |
| [B05 — Implement durable agent tasks and configuration reconciliation](stories/B05.md) | agentic | 10 | not_started |
| [B06 — Provide terminal, desktop and first-run experience](stories/B06.md) | agentic | 10 | not_started |
| [B07 — Implement memory, retrieval and portable backup](stories/B07.md) | agentic | 8 | not_started |
| [B08 — Implement proactive health monitoring and automation](stories/B08.md) | agentic | 8 | not_started |
| [B09 — Add text-to-speech and speech-to-text](stories/B09.md) | agentic | 5 | not_started |
| [B10 — Add versioned plugin and MCP interfaces](stories/B10.md) | agentic | 6 | not_started |
| [B11 — Integrate approved branding and production asset variants](stories/B11.md) | agentic | 8 | not_started |
| [B12 — Build and test the graphical installer](stories/B12.md) | agentic | 9 | not_started |
| [B13 — Verify installed daily-use release and gate G2](stories/B13.md) | agentic | 5 | not_started |
