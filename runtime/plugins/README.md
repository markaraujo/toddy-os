# Local plugin and skill source preparation

This bounded component uses the [MCP 2025-06-18 stdio transport](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports),
[initialization lifecycle](https://modelcontextprotocol.io/specification/2025-06-18/basic/lifecycle)
and [tools protocol](https://modelcontextprotocol.io/specification/2025-06-18/server/tools).
It supports a deliberate local text-tool subset, not every MCP protocol revision
or optional feature. No external connector, provider key, HTTP transport, client
sampling, roots, hooks or code-backed skill is enabled by this source slice.

`Plugin` receives a reviewed version-1 manifest, an owned bundle path and an
independent owner authorization callback. Discovery is disabled; enable and every
call independently check current authorization. The broker must bind each object
to the authenticated user/profile and stop/revoke it on profile removal. This
Python object is not a durable owner-policy store or a replacement executor.

Manifest fields are exactly `plugin_version`, `id`, `entry`, `files`,
`capabilities` and `tools`. `files` maps every declared relative payload path to
its SHA-256; undeclared files never enter the private execution snapshot.
`capabilities` is exactly `["mcp.tools.read"]`. `tools` maps approved tool names
to their required string argument names. Imported code or metadata cannot expand
these capabilities or activate itself. Replacing a plugin requires a new disabled
registration and owner review; remove revokes the registration without deleting
the owner's original directory. There is no automatic update execution.

Each call verifies actual bytes into a private snapshot and uses installed
Bubblewrap with mandatory user/mount/PID/network/IPC separation. `/usr` and its
loader are read-only, `/plugin` is the exact pinned snapshot, `/tmp` is private,
and `/home`, `/run`, the host `/etc`, session/system buses and original workspaces
are absent. The environment is cleared and unrelated descriptors are closed.
The trusted entry sets memory/CPU/file-size/process/descriptor/core limits before
executing the reviewed Python entry. Further user namespaces are disabled.
Failure to create this boundary leaves code unavailable; there is no unconfined
fallback. A namespace alone does not establish support on another kernel.

Calls are serialized, bounded by wall timeout and text/frame limits, and use a
new MCP connection. Stop or revocation kills the private process namespace;
read-only plugins have no authorized persistent writes to roll back. Results
carry `untrusted: true`; server instructions, descriptions and tool text never
become credentials or administrative authority. The broker must not place a
secret into tool arguments. Stderr is discarded, never exported as a secret log.

`Skill.metadata()` reads only the exact two-field plain front matter. `load`
requires explicit relevance selection; reviewed resources are separate bounded
reads below `references/`. This loader executes nothing and grants no tools.
Instruction text remains subordinate to current executor/credential policy.
The broker's validated profile staging controls editing/import/activation; this
loader does not copy executable hooks or automatically adopt untrusted files.

Host checks are `python3 -m unittest discover -s tests -p test_plugins.py -v`.
Native filesystem/secret-service/egress denial and the B10 integrated broker and
browser flows remain separate acceptance work; a host pass is not that evidence.
