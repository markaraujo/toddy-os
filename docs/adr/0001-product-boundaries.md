# ADR-0001: Independent source-built distribution and two-phase delivery

Date: 2026-11-05
Status: Accepted product direction, confirmed by the owner in this chat

## Context

The owner wants an original community Linux distribution inspired by the LFS-based process in the Sagui Linux video, a familiar Ubuntu-like desktop experience, and full-power agentic interaction. A proposal to start from Ubuntu was rejected in favor of building the base from source.

## Decision

Build an independent LFS foundation first and add desktop/agentic capabilities second. Preserve provider independence, optional local inference, text/voice, persistent declarative configuration plus controlled one-off operations, proactive automation and pluggable integration. Target an experimental installable daily-use release, beginning with x86_64 VM validation. Name the product Toddy OS and retain the approved bespectacled Shih-tzu PNG identity. The initial preference was to keep GitHub private through first ISO review; this visibility decision is superseded by ADR-0005. Use English for repository artifacts.

## Alternatives

Ubuntu remaster: easier compatibility, but does not satisfy the chosen source-built foundation. Copy Sagui scripts: helpful reference but tied to a different environment/version. Invent every component: unnecessary; use suitable open-source upstream components with their licenses preserved.

## Consequences

Toddy OS owns package integration, updates, security maintenance, installation and hardware validation. APT/dpkg does not automatically make LFS compatible with Ubuntu's binary repositories. Full administrative agent authority requires revocation and recovery; root-local audit cannot be tamper-proof against root. Broad hardware compatibility is a staged program, not a launch guarantee.

## Sources and validation

User requirements in the planning conversation; [LFS 13.1-systemd](https://www.linuxfromscratch.org/lfs/view/13.1-systemd/) and [BLFS 13.1](https://www.linuxfromscratch.org/blfs/view/13.1-systemd/) consulted on 2026-11-05. These sources inform the proposed baseline; no OS build or hardware validation is claimed by this decision. Working choices remain in OPEN-DECISIONS.md until evaluated.
