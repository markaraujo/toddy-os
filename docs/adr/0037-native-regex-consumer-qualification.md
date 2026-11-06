# ADR-0037: Measure remaining native regex consumers and retain limitations

- Date: 2026-11-06
- Status: Chroot probes measured; native boot repetition and broader consumer audit pending

ADR-0020 fixed Findutils' exact Greek fastmap failure using its supplied Gnulib
implementation. That did not globally fix Glibc. Read-only native probes now
exercise Grep, Sed, Gawk and Bash with real English ASCII, Portuguese accents,
Greek UTF-8 and the Greek single-byte locale. All eight English/Portuguese cases
pass. Grep/Sed match final sigma in both Greek cases. Bash with nocasematch
passes Greek UTF-8 but misses final sigma in el_GR.iso88597. Gawk default matcher
misses final sigma in both encodings. The report explicitly says all_cases_pass
false; these are measured residual limitations, not reclassified successful tests.

Gawk 5.4.1 source/doc identifies MinRX as its default since 5.4.0 and retains the
older GNU regex/dfa engines behind GAWK_GNU_MATCHERS. Actual explicit use of that
existing mode matches both Greek cases. This demonstrates an available upstream
alternative, not a claim that Gawk's default failure has Glibc's identical cause.
Do not force an unreviewed global engine change, silently upgrade the frozen
package or patch critical libc merely to hide a non-required Greek case. Keep
both default failure and successful alternative evidence for release limitations.
The product's English/Portuguese cases must continue to pass. No tests removed;
any additional or changed outcome makes the audit fail for investigation.

First exploratory Bash probe omitted nocasematch, so its mismatch alone was not
valid case-insensitive evidence. It was discarded as an acceptance result and
repeated with that setting; retained raw diagnostics make the distinction clear.

Evidence: .local/logs/h07-regex-consumer-audit.json SHA-256
3e7546e1ecb70d9616b35b7d54aeb9e905b2016874146c19113f434f4a5efdb4.
Repeat scripts/build/audit_regex_consumers.py in the booted target test context;
these probes do not establish all optional regex consumers, locales or patterns.
Source: frozen Gawk 5.4.1 doc/gawk.texi Choosing Matchers and re.c; original Glibc/
Findutils reproducer in ADR-0020; native executables, unchanged environments.
Primary documentation: https://www.gnu.org/software/gawk/manual/html_node/Choosing-Matchers.html
and https://www.gnu.org/software/gawk/manual/html_node/Case_002dsensitivity.html.

Dynamic-symbol audit inspected all 2551 installed native ELFs and found
49 importing regex consumers across 25 packages. Full file/symbol
list is .local/logs/h07-regex-imports-101.json SHA-256 c47c34fa543b52ba0708b4ece27009723bcffde681956205f7696504ada77825.
This includes optional utilities/libraries as well as direct CLI consumers;
dynamic imports do not prove each program exercises the affected fastmap case.
Gawk's MinRX and other static/bundled engines require separate source review.
The affected locale/pattern remains a release limitation for Glibc consumers,
not a claim that every listed program is individually broken or fully tested.
