# Toddy OS — Current status

Updated: 2026-11-07

Bootstrap: ready_for_development

B01 accepted for architecture/native feasibility (5% Phase2). B03 optional CPU-local runtime implementation started with pinned sources and explicit CPU gates. Provider/model tasks, native GNOME, installed Phase2 ISO, B02/B04–B13/G2 and physical validation remain pending.

Foundation: **100%** · Agentic desktop: **13%**

G1: passed · G2: pending · Next: **B04**

No milestone earns credit without completed acceptance evidence.

## Active story: B04 — Deliver native tools and the revocable privileged executor

The 13% phase total counts completed stories only. B04 is still in progress; its 8 points are not yet counted. Passing this story would raise the phase total to 21%.

Last verified: 2026-11-08T01:51:33.052908+00:00

Verified:

- B01 prerequisite and B03 native provider/local/acquisition evidence accepted; no guest writer active.
- Native policy-core-1 six SQLite/grant/revocation/concurrency/process-loss tests passed; no root IPC or privileged effect claim.
- Native executor-ipc-3 actual root service/UID101 configuration mutation and unrestricted root id0, UID65534/wrong-schema/import escalation/revocation/policy-read denials passed in synthetic root.
- Native executor-ipc-5 active root Stop86ms/process absent and service SIGKILL ->child absent/restart uncertain/no replay passed; policy-core-2 eight storage/migration/cancel/recovery tests passed.

Running: Implementing remaining native tools and administrative backends; no guest writer active.

Remaining:

- Native user tools and structured package/service/network integration.
- Installed systemd cgroup lifecycle plus dedicated owner-authenticated policy surface/logind; all B04 criteria remain pending.

[Acceptance evidence](docs/evidence/B04.md)

| Story | Phase | Weight | Status |
| --- | --- | ---: | --- |
| [H01 — Inspect host and select isolated build environment](stories/H01.md) | foundation | 4 | completed |
| [H02 — Freeze books, sources and integrity manifest](stories/H02.md) | foundation | 4 | completed |
| [H03 — Prepare target, build user and package ownership](stories/H03.md) | foundation | 4 | completed |
| [H04 — Build the cross-toolchain](stories/H04.md) | foundation | 10 | completed |
| [H05 — Build temporary tools](stories/H05.md) | foundation | 8 | completed |
| [H06 — Enter chroot and create recoverable checkpoint](stories/H06.md) | foundation | 8 | completed |
| [H07 — Build and test the final base system](stories/H07.md) | foundation | 24 | completed |
| [H08 — Configure identity, services and basic networking](stories/H08.md) | foundation | 6 | completed |
| [H09 — Build kernel and boot configuration](stories/H09.md) | foundation | 8 | completed |
| [H10 — Assemble the live system](stories/H10.md) | foundation | 8 | completed |
| [H11 — Produce hybrid ISO and artifact manifest](stories/H11.md) | foundation | 6 | completed |
| [H12 — Verify foundation boot matrix and recovery](stories/H12.md) | foundation | 6 | completed |
| [H13 — Deliver and accept foundation gate G1](stories/H13.md) | foundation | 4 | completed |
| [B01 — Freeze the minimal Toddy architecture and delivery slices](stories/B01.md) | agentic | 5 | completed |
| [B02 — Deliver the minimal branded GNOME desktop](stories/B02.md) | agentic | 10 | not_started |
| [B03 — Connect provider adapters and one optional local AI profile](stories/B03.md) | agentic | 8 | completed |
| [B04 — Deliver native tools and the revocable privileged executor](stories/B04.md) | agentic | 8 | in_progress |
| [B05 — Persist tasks and recover interrupted system changes](stories/B05.md) | agentic | 10 | not_started |
| [B06 — Deliver Toddy quick entry, native UI and first-run setup](stories/B06.md) | agentic | 10 | not_started |
| [B07 — Deliver inspectable local memory and portable backup](stories/B07.md) | agentic | 8 | not_started |
| [B08 — Deliver quiet health monitoring and one persistent automation](stories/B08.md) | agentic | 8 | not_started |
| [B09 — Deliver optional push-to-talk and spoken Toddy responses](stories/B09.md) | agentic | 5 | not_started |
| [B10 — Deliver a bounded plugin interface and one MCP integration](stories/B10.md) | agentic | 6 | not_started |
| [B11 — Integrate the navy brand and nerdy Toddy installer scenes](stories/B11.md) | agentic | 8 | not_started |
| [B12 — Deliver guided offline installation and optional software setup](stories/B12.md) | agentic | 9 | not_started |
| [B13 — Deliver the basic-tested experimental owner preview and G2](stories/B13.md) | agentic | 5 | not_started |
