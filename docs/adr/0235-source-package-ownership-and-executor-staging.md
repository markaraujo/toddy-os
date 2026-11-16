# ADR-0235: Resolve original runtime package ownership for native staging

Date: 2026-11-16. Status: source generators tested; native installation pending.

The B01 ownership blueprint contained provisional executor wrappers/state paths
and software-helper directories. Resolve them to the actual reviewed source
layout without changing offline/later-acquisition scope. The lightweight
assistant alone owns the installed toddy namespace root, UI/setup/shared parser/
protected connection client. Optional agent owns broker/worker/tools/local and
acquisition; voice and integrations own their separate children. Branding owns
artwork; no package duplicates another package's files. Module presence is not
runtime acceptance or permission to start a dependent story.

The executor remains independent of GTK, model, plugin and user-state modules.
Its source generator installs exact Python/XML bytes, fixed Polkit owner helper,
system-bus policy, native unit and systemd-only activation. Exec=false prevents
a bus fallback from starting the root process outside its qualified cgroup. No
policy database, grant, credential or mutable runtime state enters the payload.
StateDirectory creates /var/lib/toddy/executor only when the service actually runs.
The fixed root helper needs fresh administrator authentication; ordinary imports
cannot grant authority. A native first-install/check recipe uses the existing
full target guard/ownership/package backend and never starts a daemon in chroot.
It refuses old state/payload conflicts, verifies native dependency closure and
retains source/legal hashes. No new maintainer-script capability is introduced.
Runtime activation/removal/restart are reviewed native transaction postconditions,
not arbitrary imported package scripts.

Dependencies use accepted native B02 names/versions (Python3.14.10, PyGObject3.56.3,
GLib2.88.3, DBus1.16.2, Polkit127, Systemd261.2, NetworkManager1.58.1 and native APT/
Dpkg), not a parent distribution's binary repository. Source-only stage tests
verify deterministic bytes/modes/epoch, exact ownership layout, safe activation
and no bundled policy data. This does not prove a signed package, target install,
UI launch or final image closure. Those gates remain actual native work.
