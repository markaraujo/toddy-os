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

## Opt-in browser bridge

`BrowserSession` opens one hash-reviewed local HTML fixture in a new native
Firefox process with `--no-remote`, `--new-instance` and an explicit private
profile. HOME/XDG paths are fresh; provider environment variables and owner
browser cookies/logins/profile paths are never imported. The broker must supply
current opt-in `browser.local.read` authorization at launch and read. This is a
trusted native-browser profile boundary, separate from unknown-code confinement.

The read worker uses the selected GNOME
[AT-SPI Accessible API](https://gnome.pages.gitlab.gnome.org/at-spi2-core/libatspi/class.Accessible.html)
and [document URL attribute](https://gnome.pages.gitlab.gnome.org/gtk/atspi2/method.Document.get_document_attribute_value.html).
It selects the launched Firefox PID before traversing content, then selects the
exact fixture document URL. Browser chrome, other application text, other
documents and unmatched frames are excluded. URL is checked again after the
bounded read. The broker bounds worker time/output, marks text untrusted and
provides Stop for its owned browser/reader processes. There is no static-file or
HTTP-fetch fallback when native accessibility is unavailable.

Source tests use explicitly labeled process/accessibility fixtures:
`python3 -m unittest discover -s tests -p test_browser_bridge.py -v`.
They establish lifecycle/scope behavior, not a real Firefox accessibility pass.
Actual guest Firefox153.7.0esr/AT-SPI local-page read and Stop/error remain required
before claiming S25 or B10 acceptance. General website navigation, login,
form filling, driver/debug ports and owner browser profiles are unavailable.
