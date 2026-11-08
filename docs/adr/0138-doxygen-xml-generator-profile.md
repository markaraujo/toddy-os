# ADR-0138: Doxygen as the native XML generator, with bibliography unqualified

- Date: 2026-11-08
- Status: Accepted; native stage and installed XML/XSD generator qualified
- Sources: frozen Doxygen1.18.0, libxml2-2.15.3 doc/meson.build and doc/Doxyfile

The optional libxml2 Python binding needs Doxygen XML metadata even when HTML
documentation installation is disabled. Build the frozen1.18.0 CLI natively with
system SQLite; GUI/manual/external search and Clang parsing disabled. Libxml2's
actual Doxyfile requires XML and disables Graphviz, with no Clang parsing request.
Keep corresponding bundled fmt/spdlog/per-file notices. This is a build tool, not
a new mandatory desktop app or qualified software-catalog candidate.

Actual native compilation succeeded. All122 upstream CTest cases executed:
121passed and012_cite failed. Source cite.cpp runs embedded bib2xhtml.pl; that
script invokes external bibtex. Native Perl5.44 works, but BibTeX is absent. The
original failed bibliography output/reference diff remains evidence, not a skip
or a pass. No test/golden/source/tolerance changes and no complete-suite claim.

Do not install a TeX distribution merely for an unused bibliography feature of
the C/API generator. Limit this profile to ordinary native source/XML generation.
Require all other121 original cases to remain passed, preserve existing compiled
ELF hashes, stage without recompilation and prove a real C function/parameter XML
output plus native XSD validation. Later actual libxml2 Python binding tests are
still required. Record unavailable bibliography/citation integration explicitly;
that feature needs its dependency and affected requalification if requested.

The tool compiles in a bounded1536MiB regular-file volume inside the disposable
builder VM, using the existing UID101/caps0/NoNewPrivs/RO-input/offline sandbox.
Host100GiB+full volume+256MiB preflight passed. Native package promotion still
requires the unchanged full-root runner and an installed XML/XSD consumer. No
physical disk/target partition changes or core XML rebuild are authorized by this
profile decision.
