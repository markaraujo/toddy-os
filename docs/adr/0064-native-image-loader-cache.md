# ADR-0064: Generate the image loader cache from native library payload

- Date: 2026-11-07
- Status: Native component verified in private roots; full image integration pending

Generate /etc/ld.so.cache inside the fresh image with its own source-built
Glibc ldconfig, using -X to preserve package-owned SONAME links and -i to ignore
auxiliary lookup state. Do not copy either installed cache from the builder.
The caller supplies the accepted package inventory after H07 metadata closure.
The component does not bypass H09/H10 acceptance or provide a production CLI.

Verify the generator, frozen loader configuration, actual library-tree inputs
and their ownership/bytes/links before generation. Require physical image/cache
parents on the same filesystem and no existing or interrupted cache. The current
foundation policy supports the LFS /usr/lib, /usr/local/lib and optional /opt/lib
search configuration, empty ld.so.conf.d and no tunables.conf. Additional search
configuration needs explicit review rather than silent inheritance. Keep /lib
as its owned usr/lib link and /lib64 as the physical directory with owned loader
links used by the actual full LFS target.

Read back the cache through native ldconfig -p, resolve every cached path inside
the image to verified package bytes, and check input metadata/bytes/link targets
and the library namespace are unchanged. Glibc still writes a new auxiliary
cache when -i is used. Validate and omit that newly generated inode-based file;
retain the fresh empty 0700 cache directory. The runtime loader uses the main
cache; the auxiliary data exists to accelerate later ldconfig executions.

Alternatives: copying installed caches carries builder-derived state; ordinary
ldconfig without -X can modify owned links; assuming -i suppresses auxiliary
output contradicts the frozen implementation. The final image must retain a
separate package/ELF dependency audit: a valid cache does not prove that every
application dependency is present.

## Sources, correction and evidence

Inspected frozen LFS 13.1-systemd sections 5.5 and 8.5, actual own filesystem-layout
records, and Glibc 2.44 elf/ldconfig.c and elf/cache.c. LFS chapter05/glibc.html
SHA-256 c7814d20e0896d36572220732853951c0d7418e85edf0c5bf7c796dd81ae40df;
chapter08/glibc.html SHA-256
463fea4974020e9b3f70effb0c7dfd2d8a42d51997b269695a0c786158ad87f2.
Glibc source archive SHA-256:
37f600f2bef3c5e8300147059568b2a2e40a7ad6ccc65ce942556d49429cc667.
The actual native Glibc package includes the already frozen upstream fixes;
this preparation does not rebuild or change it.

The first private probe refused before cache generation because the helper
incorrectly assumed the minimal initramfs's lib64 -> usr/lib alias also described
the full system. Actual LFS and the native filesystem-layout package instead use
a physical /lib64 with two loader links. Corrected the helper and private input
selection to preserve the real full-system layout, not modify it to fit the
test. Original failure report SHA-256:
069f6c9c48e7098305065271644f84efbf12123f5735bed61de0c89c184fa871.
Preserved fixture: /mnt/lfs/tmp/toddy-loader-cache-hq68ba74.

python3 scripts/host/probe_loader_cache.py builds private roots from actual
source-owned program/configuration/library inputs. The tested subset contains
16 verified generator/configuration/library entries and yields five native
cache entries. Two fresh roots generate identical 367-byte main caches, SHA-256
e3eb17ac118f9faf74fc7a11a527c995c59c7bed17a218f5a4fceeaaf7df4842.
Native Bash runs successfully and its LD_DEBUG trace explicitly uses the image
cache and native libc/readline/history/ncurses libraries. Debugging is enabled
only after entering the private image, separating this trace from the builder's
chroot executable. All selected input metadata/bytes/link targets remain unchanged.

Twelve negative cases preserve the previous cache or its absence: existing main
cache, interrupted cache output, inherited auxiliary cache, redirected auxiliary
directory, changed library, changed generator, unowned library, changed config,
additional config, tunables, redirected library directory and incorrect /lib
alias. Installed main/auxiliary caches and Dpkg status remain unchanged.

Final report .local/logs/h10-loader-cache-probe.json SHA-256:
2fb5dbf63cd833f96660546dfd971aa3277e0db396b4f810fa9881207807ca9e.
Tested helper SHA-256:
4d80f0f4a9d2d07464d497c78c7af37074727eac565778ab0516a49e9084a692.

These five entries are a real native component fixture, not the complete release
library set. Full accepted-root assembly, cache generation for all selected
packages, dependency closure and actual native boot remain required. A failed
generation preserves its stage for diagnosis; reconstruct a fresh stage from
accepted inputs instead of overwriting an unknown existing cache.
