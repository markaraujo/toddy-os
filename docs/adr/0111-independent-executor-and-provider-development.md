# ADR-0111: Independent executor and provider development

- Date: 2026-11-07 America/Sao_Paulo
- Status: Accepted planning refinement; no guest implementation started

Per-story strategy review found B04 unnecessarily waited for all of B03, including
actual local-model proof. B04 uses native deterministic tool/caller/policy fixtures
and B01 contracts; it does not require the model. Change B04 prerequisite to B01.
Require B05 to depend on both B03 and B04, preserving the integrated durable-task
acceptance boundary. Native executor operations still require independent policy,
audit, safe guest recovery and no unprivileged caller-supplied authorization.

Preserve default story priority, single guest writer, full required acceptance and
ADR-0063 approval. This is independence of implementation prerequisites, not an
instruction to run simultaneous mutating guest jobs. B03 failure can no longer
starve executor development; final integration still waits for its real proof.
See [the per-story review](../PHASE-2-STORY-STRATEGY.md).
