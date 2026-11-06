# ADR-0003: Autonomous installation of development dependencies

Date: 2026-11-05
Status: Accepted — explicit owner instruction

## Context

The pre-start audit found missing virtualization and compilation tools. The owner explicitly requested that the development AI have full access to install what it needs to unblock itself instead of repeatedly stopping for routine setup approval.

## Decision

Once development starts, authorize the AI to install/update/configure necessary project-related tools and dependencies on the development host and isolated target, using available administrative privileges. Diagnose, fix, validate, document and continue autonomously. Keep host setup distinct from the source-built target and preserve frozen package versions.

## Boundaries

This is authorization, not a mechanism that creates credentials or overrides runtime permissions. A missing sudo credential, account login, mandatory legal acceptance or purchase remains a concrete external dependency. Preserve personal data, unrelated services and physical disks. Do not format the workstation or weaken global security as a shortcut. This request changes the plan; it does not launch provisioning or compilation.

## Validation

H01 records the before/after tool inventory and verified provisioning outcomes. Every installation used to remove a blocker records its source, selected version, result and any required rollback. No host or guest installation was performed while writing this decision.
