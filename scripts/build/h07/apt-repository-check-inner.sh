#!/bin/bash
# Actual native signed repository operations; all packages/keys/roots disposable.
set -euo pipefail
mkdir -p /sources/evidence/h07-apt
exec > >(tee /sources/evidence/h07-apt/native-repository.log) 2>&1
fixture=$(mktemp -d /tmp/toddy-apt-native.XXXXXX)
https_pid=
cleanup() {
 local result=$?
 if [[ -n $https_pid ]]; then
  kill "$https_pid" 2>/dev/null || true
  wait "$https_pid" 2>/dev/null || true
 fi
 if [[ -f $fixture/https.log ]]; then cat "$fixture/https.log";fi
 GNUPGHOME="$fixture/keys" gpgconf --kill gpg-agent >/dev/null 2>&1 || true
 if [[ $result == 0 ]]; then
  rm -rf "$fixture"
 else
  printf 'Preserved failed APT fixture: %s (exit %s)\n' "$fixture" "$result" >&2
 fi
 return "$result"
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
APT::Sandbox::Seccomp "true";
Acquire::Languages "none";
DPkg::Options { "--root=$fixture/root"; "--log=$fixture/dpkg.log"; "--force-confold"; "--force-confdef"; };
APTCONF
export APT_CONFIG="$fixture/apt.conf"
# A successful command can still report root fallback. Treat the exact frozen
# C-locale diagnostics as failed acceptance, not a harmless download warning.
# Effective worker identities also require observation in the final image.
apt-get() {
 local result
 local -a acquisition=(apt-get "$@")
 if [[ ${observe_https_workers:-false} == true ]]; then
  acquisition=(python3 -B /sources/evidence/h07-apt/apt-worker-probe.py
   --output /sources/evidence/h07-apt/https-worker.json
   --user _apt --executable /usr/libexec/apt/methods/https -- "${acquisition[@]}")
 fi
 if command "${acquisition[@]}" > "$fixture/apt-command.log" 2>&1; then
  result=0
 else
  result=$?
 fi
 cat "$fixture/apt-command.log"
 if grep -E 'No sandbox user|Download is performed unsandboxed as root' "$fixture/apt-command.log"; then
  printf 'Unexpected APT privilege fallback; preserve fixture for diagnosis\n' >&2
  return 125
 fi
 return "$result"
}
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
find "$fixture/state/lists" -maxdepth 1 -type f ! -name lock -delete
expect_rejection tampered-index apt-get update -o APT::Update::Error-Mode=any
cp "$fixture/packages.good" "$fixture/repo/Packages"
apt-get update
# Preserve signed index but corrupt a not-yet-downloaded package.
payload="$fixture/repo/toddy-apt-probe_2_all.deb"
cp "$payload" "$fixture/payload.good"
printf 'tampered' >> "$payload"
expect_rejection tampered-payload apt-get --yes install toddy-apt-probe
[[ $(dpkg-query --admindir="$fixture/root/var/lib/dpkg" -W -f='${Version}' toddy-apt-probe) == 1 ]]
[[ $(dpkg-query --admindir="$fixture/root/var/lib/dpkg" -W -f='${Version}' toddy-apt-dependency) == 1 ]]
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
# Exercise APT's own HTTPS method, independently of Curl's earlier TLS checks.
# The temporary trust anchor is scoped to these commands, never system trust.
(
 umask 077
 if ! openssl req -x509 -newkey rsa:2048 -noenc -days 1 \
  -subj /CN=localhost -addext subjectAltName=DNS:localhost \
  -keyout "$fixture/tls.key" -out "$fixture/tls.crt" \
  > "$fixture/tls-generation.log" 2>&1; then
  cat "$fixture/tls-generation.log"
  exit 1
 fi
)
chmod 644 "$fixture/tls.crt"
python3 - "$fixture" <<'PYSERVER' > "$fixture/https.log" 2>&1 &
import functools,http.server,os,pathlib,pwd,ssl,sys,time
root=pathlib.Path(sys.argv[1])
context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(root/'tls.crt',root/'tls.key')
class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Keep an actual payload request observable without changing its bytes
        # or authentication. This stays below the five-second client timeout.
        if self.path.endswith('.deb'):
            time.sleep(1)
        super().do_GET()
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),
    functools.partial(Handler,directory=str(root/'repo')))
server.socket=context.wrap_socket(server.socket,server_side=True)
(root/'https.port').write_text(str(server.server_port))
identity=pwd.getpwnam('tester')
os.setgroups([]);os.setgid(identity.pw_gid);os.setuid(identity.pw_uid)
server.serve_forever(poll_interval=0.1)
PYSERVER
https_pid=$!
for attempt in $(seq 1 100); do
 if ! kill -0 "$https_pid"; then
  cat "$fixture/https.log"
  exit 1
 fi
 if [[ -s $fixture/https.port ]]; then break;fi
 sleep 0.1
done
test -s "$fixture/https.port"
port=$(cat "$fixture/https.port")
tls_options=(-o "Acquire::https::CAInfo=$fixture/tls.crt" -o Acquire::https::Timeout=5 -o Acquire::Retries=0)
printf 'deb [signed-by=%s] https://localhost:%s/ ./\n' "$fixture/repository.gpg" "$port" > "$fixture/config/sources.list"
find "$fixture/state/lists" -maxdepth 1 -type f ! -name lock -delete
find "$fixture/cache/archives" -maxdepth 1 -type f -name '*.deb' -delete
find "$fixture/cache/archives/partial" -maxdepth 1 -type f -delete
apt-get "${tls_options[@]}" update -o APT::Update::Error-Mode=any
observe_https_workers=true apt-get "${tls_options[@]}" --yes install toddy-apt-probe
grep -Fx payload-2 "$fixture/root/usr/share/toddy-apt-probe/value"
grep -F 'toddy-apt-probe_2_all.deb' "$fixture/https.log" | grep -F ' 200 '
find "$fixture/state/lists" -maxdepth 1 -type f ! -name lock -delete
expect_rejection untrusted-tls apt-get "${tls_options[@]}" \
 -o Acquire::https::CAInfo=/etc/ssl/certs/ca-certificates.crt update -o APT::Update::Error-Mode=any
grep -iF 'certificate verify failed' "$fixture/rejection.log"
printf 'deb [signed-by=%s] https://127.0.0.1:%s/ ./\n' "$fixture/repository.gpg" "$port" > "$fixture/config/sources.list"
find "$fixture/state/lists" -maxdepth 1 -type f ! -name lock -delete
expect_rejection wrong-tls-name apt-get "${tls_options[@]}" update -o APT::Update::Error-Mode=any
grep -iF 'certificate verify failed' "$fixture/rejection.log"
printf 'deb [signed-by=%s] https://localhost:%s/ ./\n' "$fixture/repository.gpg" "$port" > "$fixture/config/sources.list"
apt-get "${tls_options[@]}" update -o APT::Update::Error-Mode=any
apt-get --yes purge toddy-apt-probe toddy-apt-dependency
[[ $(sha256sum /var/lib/dpkg/status) == "$main_status" ]]
printf 'NATIVE_APT_SIGNED_REPOSITORY_ACCEPTED dependency/conffile/tamper/key/HTTPS/trust/name/recovery/remove/purge; main DB unchanged\n'
