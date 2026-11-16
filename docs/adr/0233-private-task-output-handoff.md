# ADR-0233 — Separate temporary task output from optional conversation history

Status: accepted implementation policy; native qualification pending.
Date: 2026-11-16.

## Context

The v1 session interface keeps task status free of prompts, transcripts, raw tool
traces and credentials. The native conversation needs bounded streamed text,
reconnect and final-response retrieval. History is disabled by default with zero
retention. Keeping all output for a day would silently contradict that default;
erasing the final response before the UI can fetch it would break the conversation.

The repository contracts are the 2026-11-07 profile/IPC and operational prework,
plus the pinned Pi1.5 runtime and current B05/B06 scope. This decision does not
change administrative authority, turn history on, authorize paid calls or earn
native acceptance.

## Decision

Keep assistant text in a separate private task-output spool in the canonical
per-profile SQLite database. It is not part of indispensable operation metadata
or memory exports. Never store prompts, raw tool traces or connection credentials
there. Credentials remain protected lookup/private worker-FD inputs; known current
credential reflection is blocked before model context or text persistence.

Negotiate agent-text-v1 paging and a cursor-only TaskTextChanged signal. Pages are
at most32768encoded UTF-8 bytes, with1024byte chunks, an independent contiguous
text sequence, latest_sequence and an explicit complete flag. Each task is bounded
to256KiB; profile output is bounded to16MiB within the canonical journal's overall
capacity guard. Stop before new dispatch when safe preparation cannot fit. Text
never substitutes for independent operation postconditions or current root grants.

When history is disabled **or retention is zero**, output is only a current-response
handoff artifact. Finalized data expires after at most five minutes. With negotiated
agent-text-ack-v1 the owner UI acknowledges the fully drained final cursor and the
broker immediately removes those text rows. Acknowledgement is idempotent, never
submits a task or erases required effect/reconciliation records. The UI keeps the
current response only in RAM, labels it temporary and does not present saved history.
A missing acknowledgement reply is not proof of deletion; the bounded expiry still
applies. Clean shutdown removes terminal transient spools. Startup finalizes
interrupted output and removes transient data without resuming inference/effects.

If history is explicitly enabled with positive retention, use the selected days.
An output acknowledgement does not erase that explicit retained history. Expiry
and cleanup remove text only; unknown-operation and idempotency metadata remain.
This is logical deletion, not a promise of forensic erasure on SSDs/backups.

GetProfileConfig/RestoreProfile expose the same owner-bound schema/revision/CAS
backend so settings never edit an independent copy. Root grants and credentials
are outside profile JSON. Existing authenticated native tool APIs remain available.

## Consequences and validation

The UI can reconnect to active output without receiving transcripts in status
broadcasts. It can display a final response before promptly clearing the default
transient storage. A broker restart with history off can recover task/effect state
while the old response is deliberately unavailable. No automatic provider/tool
retry is added. Full memory/history export/deletion remains B07 and does not gain
transcript access through this source change.

Actual host SQLite tests cover bounded UTF-8 pages, finalized multi-page draining,
Ack/repeated-Ack removal, zero/default expiry, explicit retained history, interrupted
spool cleanup, capacity refusal and retained task records. A real production-worker/
private-Unix-HTTP synthetic-protocol task writes an actual temporary file through
the broker/journal, streams separate private text, acknowledges its deletion and
returns the same task on duplicate request without another generation/effect.
The protocol server is synthetic; actual native model/UI/keyring integration is
still required and is not claimed by these host checks.
