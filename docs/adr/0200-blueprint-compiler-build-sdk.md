# ADR-0200 — Qualify the pinned Blueprint compiler as a build-only SDK

Status: accepted · Date: 2026-11-10 · Story: B02

Nautilus50.2.2 requires blueprint-compiler>=0.19.0. Use the frozen
BLFS13.1-systemd `general/python-modules.html#blueprint-compiler` version0.22.2,
page SHA256 `eeca0df3449c611069e44d356162b7438e05151c39d225e72c601f049a66a72d`.
Official archive matched frozen MD5; SHA256 frozen before guest extraction:
`231d72efbac931c235ac3e022fe94982095c20d88721d9a8dcf60152f2017e07`.
Existing Python3.14/PyGObject3.56.3/GTK4.22.4/GI dependencies are reused. Build
release/docsfalse, disable installation-time Python bytecode generation, package
architectureall. This UI compiler belongs to the build SDK root, excluded from the
final runtime unless a separately selected consumer needs it.

Initial host invocation redirected output into the helper-owned exclusive log,
so FileExistsError happened before any guest call. Source/work absence verified;
new prepared-2 receipt succeeded once. No uncertain preparation was replayed.
Initial build configured/generated successfully; four original tokenizer/formatter
cases passed. Original linter method produced15PermissionErrors: it opens each
fixture r+ although its code only reads. Preserve that failed original result.
Use a byte-identical private411file test copy for that one unmodified method;
source and private before/after manifests remain identical. All15subcases passed.
Reuse the four approved original cases and generated config/wrapper/pkg-config/
reference JSON; no Ninja, source modification or approved-case replay. The future
recipe uses that private copy; qualifier accepts only this exact test-path delta
from the retained prepared recipe. Full Gtk.Builder/deprecation modules remain
deferred because the book requires a graphical environment. Five selected test
methods and15linter subcases are reported separately, never as a full-suite pass.

Stage75regular files and actual CLI compilation of UTF8 Gtk.Box/Gtk.Label XML,
invalid-property refusal and two recovery cycles passed. Native install/post0/0,
93changedpaths/96owned entries. All installed stage bytes identical; actual
installed UID101 CLI/default Python import/pkg-config/APT closure passed. Existing
qualified pinned Python/GI/GTK dependencies unchanged, no ABI replacement or
service/policy/credentials changed. Generated XML is not proof of actual widgets,
focus, rendering, GTK Builder execution or GNOME acceptance.

[Source/failure/original/native proof](../evidence/B02-blueprint-compiler-install.json).
Archive SHA256 `bb43b77a74b284e2bc7a3159f22c27460c6e70b7a9a379574bfa8bf3e297a696`;
raw evidence SHA256 `304a779c7bbd5c765acd5875cc2135ce76d4d7f8eaa9d680b61f0132839ff8b0`.
Never replay accepted build/finish2/install1. Next minimal Nautilus profile uses
its supported optional-extension/cloud/SELinux-off switches and selected tests;
real LocalSearch runtime is still required for launch and Gvfs for device flows.
Do not remove those runtime gates merely because the compile SDK is complete.
