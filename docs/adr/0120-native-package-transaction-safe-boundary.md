# ADR-0120: Native package mutation waits for its safe boundary

Date: 2026-11-08 UTC. Status: accepted; final installed-source/recovery remains B12.

The structured executor package operation uses accepted native APT3.0.4/Dpkg1.22.22,
fixed arguments, qualified signed metadata/cache and no model-supplied URL, source,
trust override or option. Package names/versions are bounded. Native mutation is
--no-download; separate verified acquisition must populate the archive cache first.
Install/upgrade forbids incidental removals; upgrade only affects already installed
packages. Explicit remove preserves conffiles; no purge/autoremove/force-overwrite.

Audit Dpkg state before/after, verify actual requested statuses/versions, preserve
owner-modified conffiles with force-confold/confdef, and leave failures uncertain
for reconciliation. A new package transaction never bypasses broken native state.
The executor records only allowlisted failure codes, never arbitrary exception text.

Cancellation before mutation blocks it. Once APT/Dpkg/maintainer scripts write,
keep the request durable and wait for a safe completed transaction. No fixed timer
or output limit may kill a healthy package write. Stream/hash output while retaining
at most64KiB internally; use no PTY in the headless service. Root-command general
output/time bounds remain distinct. A blocked package write requires diagnosis/
recovery, not automatic replay. Service upgrade must quiesce dispatch before
stopping/replacing the executor; B12 must prove that installed lifecycle. Forced
service loss/power loss can still interrupt writes and requires reconciliation.

Frozen apt_3.0.4.tar.xz doc/apt-get.8.xml was read directly for no-download,
no-remove and only-upgrade. Existing H07 signed-repository fixture supplied the
native disposable repository approach; its unchanged broad signature/HTTPS matrix
was not rerun. Native executor-ipc-13 proves new wrapper install1/upgrade2/remove,
conffile preservation and Stop during a real one-second maintainer script, reaching
a verified commit with cancellation_requested=true. This is a real native fixture,
not the final installed repository or arbitrary maintainer-script rollback proof.

Test signing keys stay private in synthetic work; probes/debug launchers/keys must
not enter a product package/image. The private test observer is separately guarded
to one fixed file: toy source and never used by production service entry. The root
service now owns its small strict argument decoder and imports no optional broker,
model, plugin or GTK module. Packaging path follows the frozen /usr/lib/toddy/executor
blueprint. No core package version or accepted foundation was changed.
