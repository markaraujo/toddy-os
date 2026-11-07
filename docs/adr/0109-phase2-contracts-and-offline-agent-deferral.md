# ADR-0109: Reusable contracts and offline agent deferral

- Date: 2026-11-07 America/Sao_Paulo
- Status: Accepted design; native implementation proof pending
- Preserves: ADR-0063 guest-start boundary and full-administration product scope

The owner requested completion of all five proposed prework items: default harness,
UI/service communication, installation matrix, package lifecycle and a short owner
validation guide. Adopt the linked artifacts in PHASE-2-PREWORK.md and config/phase2
as the selected v1 candidates. B01 proves compatibility and freezes target details;
preparation does not mark its acceptance criteria passed.

The owner clarified that offline installation should install the usable system
without agent functionality, which can be added later. The base includes a small
setup/UI entry that works with broker/Node/Pi/executor/models absent. Acquire the
agent closure later through ordinary native package authorization, not through an
absent executor. Keep user data/desktop intact and require no OS reinstallation.
Online setup and verified optional media packs still require explicit choices.
No API keys are collected in the installer. Required base failures block success;
optional acquisitions can remain pending without falsely showing installed.

Maintain exclusive package ownership, supported native adapters, bounded versioned
IPC and atomic profile revisions. Imported text cannot grant authority; owner full
administration remains an independent revocable policy capability. Reconnect
attaches to a durable task and reconciles uncertainty rather than replaying it.
Offline deferral does not waive the complete G2 development acceptance checks.
