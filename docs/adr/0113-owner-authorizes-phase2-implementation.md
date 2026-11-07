# ADR-0113: Owner authorizes isolated Phase 2 implementation

- Date: 2026-11-07 America/Sao_Paulo
- Status: Accepted — explicit owner instruction in this development session
- Supersedes: ADR-0063 continuation hold only; foundation evidence is unchanged

The owner explicitly instructed: “Autorizo explicitamente iniciar agora a implementação da fase 2 no ambiente isolado e continuar autonomamente até a entrega.” The same instruction approves the existing plan and requests functional B01–B13/G2 delivery, native graphical validation, installable ISO/checksums, reproducible inputs, recovery evidence and synchronized release/portal publication.

Record this instruction before B01 starts. Continue small verified slices without routine milestone approval. Preserve one guest writer, bounded failure diagnosis, qualified isolated package builds and change-based checks. Do not use subagents or change models automatically. Do not rebuild the accepted foundation or reopen general planning without a concrete blocker.

This authorization does **not** assert that physical foundation testing occurred. Physical hardware remains pending; QEMU evidence stays labeled VM-only. It does not authorize physical disk changes, paid resources, credential disclosure or global security weakening. Missing actual access/legal acceptance remains a concrete user dependency after useful authorized alternatives.

The next action is B01 accepted-foundation clone inventory, followed by pinned dependency/native bridge/engine/no-write installer spikes. Story acceptance requires actual postconditions; approval and planning checks alone do not earn completion credit.
