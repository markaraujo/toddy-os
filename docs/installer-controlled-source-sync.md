# Controlled installer source synchronization

Use the existing candidate helper before any new installer preparation:

```sh
python3 scripts/host/candidate_assistant_inputs_sync.py
```

It transfers the complete `runtime/installer` directory and every file resolved
by current `composition.SOURCES`, including cross-directory setup/shared modules
and scripts. The 34-file current map also covers the C++/Calamares package inputs.
The existing generic input manifest still verifies every other transferred file.
No installed package or old preparation is changed by this source synchronization.

Inside the existing exclusive global build lock, required source bytes are checked
in the incoming stage before commit, and again at their actual `/opt/toddy-build`
locations after commit. Unexpected non-cache files in the installer namespace are
refused, preventing a stale local fallback from overriding a declared script
source. A failure after commit leaves `input-sync.running` in place; native recipe
dispatch remains blocked until a complete controlled resynchronization succeeds.
The host map is rechecked after transfer too.

Success prints the exact immutable root receipt:
`/var/log/toddy/build/input-source-coherence-<MAP_SHA256>.json`. Its shape is:

```json
{"version":1,"state":"required-source-bytes-verified","source_map_sha256":"MAP_SHA256","files":{"PROJECT_RELATIVE_PATH":"FILE_SHA256"}}
```

The map identity is SHA256 of `json.dumps(files, sort_keys=True,
separators=(',', ':')).encode()`. Existing matching receipts are retained;
conflicting ones are refused. The receipt records source coherence only, not
native package/GUI acceptance. Package preparation must bind this actual receipt
and recheck every mapped source; it must not infer new helper availability from an
old installed package's successful postcheck.

For this correction, first run the read-only base/live requirements against the
existing projection/current installed version, confirming imports and all nineteen
mutable bindings without creating image outputs. Aggregate any remaining source
issues before preparing installer6. Then use the fresh installer revision and
fresh projection/export namespaces; retain installer5 and its self-consistent
older source/archive/receipts as historical evidence. No Qt/Calamares rebuild,
provider/model activation or guest operation was run by this source change.
