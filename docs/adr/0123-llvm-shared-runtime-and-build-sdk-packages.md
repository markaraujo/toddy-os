# ADR-0123: Separate LLVM shared runtime from the build SDK

- Date: 2026-11-08
- Status: Accepted packaging rule; native package qualification pending

The approved root recipe and critical-path contract exclude new compiler SDKs
from the offline base/live image, while retaining actual runtime dependencies.
LLVM22.1.8 supplies both the Mesa shared-library dependency and the Rust/Clang
build SDK. Shipping its original complete stage as one runtime dependency would
force compiler tools and headers into the base. The accepted foundation is not
refactored by this change.

After the unchanged ADR0121 critical tests pass, partition exactly the measured
libLLVM.so.22.1 and its relative libLLVM.so alias into an owned llvm-runtime
archive. Preserve library bytes, source/archive/patch identities and exact legal
notices. The llvm build SDK owns the remaining stage, including Clang/libclang,
headers, tools and compiler configuration, and depends on the exact runtime
version. Both are installed only in the development target by the existing
full-root native transaction. No maintainer scripts or new installation backend.

The split refuses unexpected ABI names, escaping aliases and an existing output;
interrupted installation must reconcile actual archive/database receipts before
continuing. Fixture checks cover preservation, runtime resolution without SDK
files, bad alias rejection and refusal to overwrite prior evidence. They are not
native ABI acceptance.

Native compiler/JIT/libclang consumers and ownership/dependency checks remain
required after installation. Mesa must depend on llvm-runtime when its actual
linked closure requires it. Final base/live assembly still needs real consumers
and forbidden-SDK inventory checks; no image scope is prequalified by this ADR.
