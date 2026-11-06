# ADR-0011: Classify unavailable Tcl database-driver tests explicitly

Date: 2026-11-06. Status: accepted for the H07 build environment.

## Context and evidence

Frozen LFS 13.1-systemd section 8.17 builds Tcl 8.6.18 with bundled
extensions. The complete native core suite produced 47159 total, 43704 PASS,
3455 skipped and zero failed. Extension summaries likewise have zero failed,
but three driver families cannot load optional database-client libraries:
TDBC MySQL needs libmysql.so.15, ODBC needs libiodbc.so, PostgreSQL needs
libpq.so.5. The raw test harness records these as test-file errors while
make exits zero. They must not be called passing database tests.

Primary sources: verified tcl8.6.18-src.tar.gz, bundled TDBC 1.1.13
README files, tests/tdbc{mysql,odbc,postgres}.test, and actual retained
h07-tcl log. The driver READMEs identify the separate database APIs and
client-library requirements; these are not core Tcl/Expect dependencies.
Source archive SHA-256 remains pinned in config/sources.lock.json.

## Decision

Preserve the complete original output. Classify only the exact missing
client-library errors as unavailable optional database-driver tests. Reject
any other test-file error, nonzero failed count or missing core summary.
Core Tcl, its test tools and the functioning bundled extensions can proceed
without introducing database servers into the foundation just for these
optional tests. No source test is changed or omitted from the full invocation.
The evaluator records unavailable cases separately from PASS and skipped.

## Alternatives and consequences

Installing all database stacks at this point would violate the selected book
order and add unrelated service/test infrastructure. Treating make's zero exit
as all-pass would hide real errors. Rejecting every optional client absence
would conflate missing optional integrations with failure of core Tcl.

The optional drivers are not claimed functional. Final component/dependency
closure must either package them separately with explicit dependencies or
provide and test their client libraries before advertising those integrations.
Any future requirement for these drivers requires a real integration test;
this classification does not waive release-required functionality.
