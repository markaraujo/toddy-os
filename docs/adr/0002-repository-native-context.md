# ADR-0002: Repository-native development context

Date: 2026-11-05
Status: Accepted — explicit owner instruction

## Context

The initial workstation instructions suggested documentary RAG integration. The owner explicitly declined that integration for Toddy OS.

## Decision

Use Git-tracked PRD, stories, journal, errors, evidence and ADRs as durable development context. Remove the newly created workstation RAG project manifest and registration. Do not register or synchronize this project with workstation RAG.

## Consequences

A clean checkout is sufficient for the development handoff. The future OS agent's memory remains a product requirement to be evaluated during Phase 2; this decision does not select its implementation. No RAG service is required to develop or check this repository.
