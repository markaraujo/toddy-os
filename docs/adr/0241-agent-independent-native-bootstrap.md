# ADR-0241: Agent-independent native package bootstrap

Status: accepted source boundary; installed-user native qualification pending
Date: 2026-11-16

## Decision

Ship the fixed native package acquisition helper and user review/client in the
lightweight base assistant. Installing the absent agent/executor cannot require
either optional component. Reuse signed APT/native Dpkg and per-action Polkit
administrator authentication. This authorization installs the reviewed packages;
it creates no assistant grant, model, provider key, spending consent or automatic
service activation. Full-administration owner policy remains a separate executor
flow, not a permanently limited substitute.

The descriptive candidate catalog and pending.json remain compatible deferred
wishes, with no acquisition authority. A separate fixed root-owned signed native
release catalog supplies the exact curated release, package closure, architecture,
versions, artifact hashes/sizes, source origin, public license/terms and native
qualification receipt. Unsupported apps and unsigned/unqualified releases stay
unavailable. The first release supports agent-backend with only toddy-agent,
toddy-executor and nodejs; local runtime is a separately reviewed extension.
No package, URL, command, callback or path comes from the pending manifest or model.

Root rereads catalog/keyring/source/report custody and verifies detached signatures,
current validity and monotonic generation. It revalidates metadata and the active
unlocked local installed owner immediately before a durable write intent. APT uses
only the fixed pinned source and isolated caches, downloads separately, verifies
exact artifact/control/payload/solver scope, then installs with no download or
removal. Root-only verified copies prevent downloader-owned archive changes.
Activation/maintainer-script/setuid payloads are refused. Existing owner conffiles
are preserved. No healthy installed-package write is killed for Stop or a timer.

A private root journal binds UID, immutable operation/review IDs and phase before
effects. Duplicate requests return the original operation before availability or
busy checks and never redispatch. Interrupted write intent blocks new work until
actual package/ownership/hash/audit reconciliation; nothing replays automatically.
The user cursor preserves the known operation after a lost reply. One Polkit child
streams bounded real phase events and one result; no periodic authentication poll.
Stop is an explicit cancellation request with its normal authorization and safe
boundary; committed effects are retained. Unknown status opens the journal
read-only and never creates a new operation.

## Consequences and evidence

See the [producer, package and API contract](../native-agent-acquisition.md).
Source fixtures use stub signing/native runners, not keys or APT writes. They
include a real child-process crash after one owned-temp effect, durable no-replay,
lost-reply reattachment, solver/activation denial and unchanged pending wishes.
No native bootstrap acceptance is claimed. Actual installed-user Polkit, signed
catalog/APT, ownership/lifecycle/offline/Stop/restart and root helper transport must
pass before a qualified release is published. This source slice changes no guest,
host package, key, model, current story status, UI or package generator.


## Independent native qualification and publication levels

The owner approved separate native-components and native-full-flow levels.
A root-only disposable installed-VM component driver uses signed declarations
without a production qualification field to exercise the same backend/journal,
real signed APT, owner pkexec authentication and observation after a completed
native write whose controller exits before terminal persistence. Its signed
component result authorizes only an explicitly labelled preview catalog for a
second clean-overlay production helper/UI test. The marker is a VM safety guard,
never runtime authority. Missing actual results produce no report.

Production metadata binds exact package, installed assistant code and public
trust pins. Final publication rejects component-only entries and requires actual
native-full-flow retained evidence for the same pins. Source tests use explicit
synthetic signing/OS fixtures and cannot establish either native acceptance level.
The qualification driver is not installed as an end-user bypass or package hook.
