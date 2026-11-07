# Phase 2 — Per-story implementation strategy review

Date: 2026-11-07. Reviewed actual story prerequisites, slices and acceptance,
status graph, prepared contracts and graphical/offline delivery requirements.
This is execution design and structural simulation, not runtime acceptance.

## Strategy by stage

| Stage | First useful slice and handoff | Strategy assessment / guard |
| --- | --- | --- |
| B01 | Verified clone/resources, then pinned shared contracts and minimal native probes | Necessary common entry. Commit each probe; do not require final UI/installer/model quality before freezing the contract |
| B02 | First graphical login checkpoint, then one browser/files/network/audio pass | Independent of agent/model. Prioritize this eligible branch when measured compilation dominates; no optional IDE blocks desktop acceptance |
| B03 | Provider fixture and minimal config validation, then actual CPU-local tool proof | Keep model acquisition/resource failures local to this branch; no dependency on final profile UI or B05 task store |
| B04 | Deterministic native tool/executor call with real caller policy/revocation checks | Now depends on B01, not the completed model branch. Executor-local durable audit/safe recovery is required; no model needed to test permissions |
| B05 | Integrate B03 provider and B04 tools into one durable canonical task lifecycle | Explicitly depends on both branches. Crash-after-effect, Stop and revisions must work before UI dispatch is accepted |
| B06 | Native setup opens with backend absent, then real task/Stop/profile interaction | Integrate after desktop and durable tasks. Backend-free setup cannot depend on the missing executor to install it; use ordinary native authorization |
| B07 | Extend B05 store and expose memory through existing backend/CLI | No second database or mandatory UI rewrite. Profile deletion/import provenance and consistent backups precede search polish |
| B08 | One deterministic authorized persisted schedule, quiet unchanged monitoring | Reuse canonical state and standing policy. No periodic LLM planning; skip missed runs by default |
| B09 | On-demand EN/PT sample path through existing text task interface | Audio remains optional use, scoped proof still required. Choose documented TTS fallback on a concrete blocker; no speech-specific tool authority |
| B10 | One confined local MCP call, then isolated local-page browser bridge | Reuse task/policy paths; existing desktop prerequisite is appropriate for final browser interaction. Do not implement a marketplace or broad browser agent |
| B11 | Actual GNOME/Toddy assets, supported settings and staged installer scenes | Preserve approved master; no toolkit fork. Installer runtime validation belongs to B12, avoiding a B11/B12 cycle |
| B12 | Deterministic no-AI offline base install, then later optional acquisition | Reuse B01 installer feasibility and B11 assets; disk safety first. No model/key/network requirement for base installation |
| B13 | Freeze exact base/catalog, prove acquired full experience and combined gates | Corrected stale wording that implied all optional components must be in default root. No repurposed earlier ISO, no waived required feature proof |

## Four corrections made by this review

1. Remove B03 -> B04 dependency. Executor/tool development consumes B01's stable
   contract and deterministic fixtures, not a model output. This permits actual
   security work while model acquisition/compatibility is blocked.
2. Make B05 depend on both B03 and B04. The integration gate still requires real
   provider/tool components; graph independence does not allow a fake integrated
   task service or omission of provider acceptance.
3. Scope B01 setup proof to dependency/interface contracts. Actual native setup
   behavior belongs to B06. B03 needs minimal config validation but not atomic
   profile activation/settings, whose owning stage is B05/B06.
4. Align B13's slice instructions with the offline-base/acquisition policy, keeping
   required full-experience runtime proof separate from default package selection.

Status/story prerequisites and generated dashboard are synchronized. Default
risk-first order remains stable; an active eligible branch is preserved, and
blocked work does not starve another eligible branch. All B stories remain
not_started and explicit guest approval is still false.

## Structural simulation and performance judgment

The read-only simulator replays the actual graph with each B story blocked. With
B03 blocked, B04 and B02 are now reachable after B01; B05 remains blocked.
With desktop blocked, headless provider/security/task/memory/scheduler work can
progress. B01 remains a true common prerequisite, not a gate to bypass. Recorded
results in evidence/phase2-dependency-simulation.json include the status input hash.

This improves independence and reduces one avoidable model-related stall. It does
not prove a shorter measured duration: one guest writer, build resources and actual
package compilation still determine the critical path. Do not split every story
or remove dependencies merely to expose more parallel work. Keep the accepted
architecture stable, reuse qualified probe packages and affected test evidence.

The selected approach is coherent for the experimental release: native desktop,
headless core before live UI dispatch, installer feasibility early, real graphical
checks on affected screens, and exact final-image verification. Main remaining
uncertainties are native dependency compatibility, compile durations, graphics/
audio availability and installed recovery. These need B01+ measurements, not
further speculative interface changes. Reopen only the affected decision on evidence.
