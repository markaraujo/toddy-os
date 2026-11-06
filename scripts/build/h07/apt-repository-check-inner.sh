#!/bin/bash
# Actual native signed repository operations; all packages/keys/roots disposable.
set -euo pipefail
mkdir -p /sources/evidence/h07-apt
exec > >(tee /sources/evidence/h07-apt/native-repository.log) 2>&1
fixture=$(mktemp -d /tmp/toddy-apt-native.XXXXXX)
cleanup() {
 GNUPGHOME="$fixture/keys" gpgconf --kill gpg-agent >/dev/null 2>&1 || true
 rm -rf "$fixture"
}
trap cleanup EXIT
chmod 755 "$fixture"
mkdir -m700 "$fixture/keys"
export GNUPGHOME="$fixture/keys"
gpg --batch --pinentry-mode loopback --passphrase '' --quick-generate-key 'Toddy disposable repository <repo@example.invalid>' ed25519 sign 0
fingerprint=$(gpg --batch --with-colons --list-keys | awk -F: '$1=="fpr" {print $10;exit}')
gpg --batch --export "$fingerprint" > "$fixture/repository.gpg"
mkdir -p "$fixture/repo" "$fixture/root/var/lib/dpkg" "$fixture/state/lists/partial" \
 "$fixture/cache/archives/partial" "$fixture/config/parts" "$fixture/config/sources" "$fixture/log"
touch "$fixture/root/var/lib/dpkg/status"
main_status=$(sha256sum /var/lib/dpkg/status)
cat > "$fixture/apt.conf" <<APTCONF
Dir::Etc "$fixture/config";
Dir::Etc::main "-";
Dir::Etc::parts "parts";
Dir::Etc::sourcelist "sources.list";
Dir::Etc::sourceparts "sources";
Dir::State "$fixture/state";
Dir::State::status "$fixture/root/var/lib/dpkg/status";
Dir::Cache "$fixture/cache";
Dir::Log "$fixture/log";
APT::Architecture "amd64";
APT::Architectures { "amd64"; };
APT::Sandbox::User "_apt";
Acquire::Languages "none";
DPkg::Options { "--root=$fixture/root"; "--log=$fixture/dpkg.log"; "--force-confold"; "--force-confdef"; };
APTCONF
export APT_CONFIG="$fixture/apt.conf"
printf 'deb [signed-by=%s] file:%s ./\n' "$fixture/repository.gpg" "$fixture/repo" > "$fixture/config/sources.list"
make_package() {
 local name=$1 version=$2 depends=$3
 local stage="$fixture/package-$name-$version"
 mkdir -p "$stage/DEBIAN" "$stage/usr/share/$name"
 printf 'Package: %s\nVersion: %s\nArchitecture: all\nMaintainer: Toddy OS <repo@example.invalid>\nDescription: Disposable signed repository probe\n' "$name" "$version" > "$stage/DEBIAN/control"
 if [[ -n $depends ]]; then printf 'Depends: %s\n' "$depends" >> "$stage/DEBIAN/control";fi
 printf 'payload-%s\n' "$version" > "$stage/usr/share/$name/value"
 if [[ $name == toddy-apt-probe ]]; then
  mkdir "$stage/etc";printf 'default-%s\n' "$version" > "$stage/etc/toddy-apt-probe.conf"
  printf '/etc/toddy-apt-probe.conf\n' > "$stage/DEBIAN/conffiles"
 fi
 dpkg-deb --build "$stage" "$fixture/repo/${name}_${version}_all.deb"
}
publish_repository() {
 (cd "$fixture/repo" && apt-ftparchive packages . > Packages && apt-ftparchive release . > Release)
 gpg --batch --yes --local-user "$fingerprint" --clearsign --output "$fixture/repo/InRelease" "$fixture/repo/Release"
}
expect_rejection() {
 local label=$1;shift
 set +e
 "$@" > "$fixture/rejection.log" 2>&1
 local result=$?
 set -e
 cat "$fixture/rejection.log"
 [[ $result == 100 ]]
 printf 'EXPECTED_REJECTION %s exit=%s\n' "$label" "$result"
}
make_package toddy-apt-dependency 1 ''
make_package toddy-apt-probe 1 'toddy-apt-dependency (= 1)'
publish_repository
apt-get update
apt-get --yes install toddy-apt-probe
[[ $(dpkg-query --admindir="$fixture/root/var/lib/dpkg" -W -f='${Version}' toddy-apt-dependency) == 1 ]]
grep -Fx payload-1 "$fixture/root/usr/share/toddy-apt-probe/value"
printf 'owner-customized\n' > "$fixture/root/etc/toddy-apt-probe.conf"
make_package toddy-apt-dependency 2 ''
make_package toddy-apt-probe 2 'toddy-apt-dependency (= 2)'
publish_repository
apt-get update
# Index authentication must reject modified index bytes.
cp "$fixture/repo/Packages" "$fixture/packages.good"
printf '\nAltered: true\n' >> "$fixture/repo/Packages"
rm -f "$fixture/state/lists/"*Packages
expect_rejection tampered-index apt-get update -o APT::Update::Error-Mode=any
cp "$fixture/packages.good" "$fixture/repo/Packages"
apt-get update
# Preserve signed index but corrupt a not-yet-downloaded package.
payload="$fixture/repo/toddy-apt-probe_2_all.deb"
cp "$payload" "$fixture/payload.good"
printf 'tampered' >> "$payload"
expect_rejection tampered-payload apt-get --yes install toddy-apt-probe
cp "$fixture/payload.good" "$payload"
apt-get --yes install toddy-apt-probe
grep -Fx payload-2 "$fixture/root/usr/share/toddy-apt-probe/value"
grep -Fx owner-customized "$fixture/root/etc/toddy-apt-probe.conf"
[[ $(dpkg-query --admindir="$fixture/root/var/lib/dpkg" -W -f='${Version}' toddy-apt-dependency) == 2 ]]
# A different public key must not authorize this repository.
gpg --batch --pinentry-mode loopback --passphrase '' --quick-generate-key 'Toddy unrelated key <other@example.invalid>' ed25519 sign 0
other=$(gpg --batch --with-colons --list-keys other@example.invalid | awk -F: '$1=="fpr" {print $10;exit}')
gpg --batch --export "$other" > "$fixture/unrelated.gpg"
sed "s,repository.gpg,unrelated.gpg," "$fixture/config/sources.list" > "$fixture/wrong-source"
cp "$fixture/config/sources.list" "$fixture/source.good"
cp "$fixture/wrong-source" "$fixture/config/sources.list"
expect_rejection unrelated-key apt-get update -o APT::Update::Error-Mode=any
cp "$fixture/source.good" "$fixture/config/sources.list"
apt-get update
# Signed metadata corruption also fails closed, then restores cleanly.
cp "$fixture/repo/InRelease" "$fixture/inrelease.good"
printf 'broken-signature\n' > "$fixture/repo/InRelease"
expect_rejection malformed-signature apt-get update -o APT::Update::Error-Mode=any
cp "$fixture/inrelease.good" "$fixture/repo/InRelease"
apt-get update
apt-get --yes remove toddy-apt-probe toddy-apt-dependency
test -f "$fixture/root/etc/toddy-apt-probe.conf"
apt-get --yes purge toddy-apt-probe
test ! -e "$fixture/root/etc/toddy-apt-probe.conf"
[[ $(sha256sum /var/lib/dpkg/status) == "$main_status" ]]
printf 'NATIVE_APT_SIGNED_REPOSITORY_ACCEPTED dependency/conffile/tamper/key/recovery/remove/purge; main DB unchanged\n'
