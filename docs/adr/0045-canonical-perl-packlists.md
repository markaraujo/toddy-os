# ADR-0045: Canonical native Perl packlist paths

- Date: 2026-11-06
- Status: Correction prepared; native isolated roundtrip passed; installation pending

A read-only native audit finds 17 installed packlists and 3210 entries. The
16 newly source-built MakeMaker modules retain 330 /sources/stage/<package>
entries from DESTDIR installation. All other core entries are canonical. Module
imports and original upstream suites passed, but these install records must be
corrected before H07 ownership/recovery closure. Existing partial acceptance is
not final metadata acceptance. No installed payload changes during this audit.

Use native Perl 5.44 ExtUtils::Packlist (its installed source read method and
actual parser) as the independent format/ownership oracle. A staged normalizer
strips only the exact own-package prefix, verifies canonical /usr files belong
to the same package, and refuses foreign prefixes, escapes, missing/redirected
payload, duplicate entries or unfamiliar record attributes. Prevalidate all
records before writing any. The frozen 16 modules use simple path-only records;
new formats require review instead of silently dropping attributes. Preserve
module-local packlists; removing them would discard useful ExtUtils inventory.

New builds normalize staged data before packaging. Existing installed modules
are corrected only through preserved own archive extraction and a new native
package version in final metadata closure. Refuse modified live packlists;
never edit installed tracked bytes directly. Tagset already has +toddy1 from
shared-journal correction, so allocate +toddy2 rather than overwriting that
archive or appending another identical suffix. Native Dpkg comparison confirms
3.24-1+toddy2 sorts after 3.24-1+toddy1. Other first metadata upgrades retain
+toddy1. Preserve prior per-package progress content in hash-addressed history.
Skip only a complete current-version/current-policy record with no newly
required direct dependencies or packlist correction. Final acceptance requires
matching per-package version/policy evidence, not merely a suffix spelling.

Actual native before-audit has exactly 330 findings; SHA-256
c2b42537f7db0a34178e87f5a0a9ab78ebd6f1fb451e8b2aaafc39bb6ea15ed8,
.local/logs/h07-native-perl-packlist-api-before.json. Read-only own-payload
rewrite preflight passes all 16 modules, SHA-256
876fbe4d9870a351956b5b839b8232fc2933a421f792fdd3b45929ef09020b1b.
Native ExtUtils roundtrip of all 16 corrected private fixtures preserves all
330 canonical owned entries; no installed changes, summary SHA-256
f7cb93db1f5380561b9a6a70b79ad5a41bf92736af93729443373d470e534ac1,
.local/logs/h07-perl-packlist-native-roundtrip.json. Raw probe retains a harmless
Python string-escape warning separately; normalized summary derives its final
JSON line from the captured exit-0 result. Four safety tests pass (86 total).

The final native Perl parser/ownership audit must report zero findings after
real versioned upgrades; this remains pending. Full payload hash/mode/owner,
ELF/shebang and package-manager closure remain separate required checks. The
active complete BDB standard suite is unchanged; do not sync inputs or dispatch
an upgrade while its recipe holds the build lock. After actual BDB result,
quiescent verified sync is mandatory before the final-base driver.
