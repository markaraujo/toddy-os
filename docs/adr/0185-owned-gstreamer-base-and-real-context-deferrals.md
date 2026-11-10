# ADR-0185: Owned GStreamer Base and explicit real-context deferrals

Status: native base package/synthetic samples accepted; GL/devices/session pending.

Use frozen BLFS13.1-systemd multimedia/gst10-plugins-base.html1.28.6, official
archive SHA256`0ba699c7c6c66f4ba640be78cb38a24715add9683f3e3a199f5369dc5a4f04ac`.
Actual core/ALSA/Ogg/Vorbis/Pango/ISO/GUdev/Mesa/GLES2/EGL/Wayland/GBM/DRM SDKs
were measured before preparation. Select raw audio/video/app/playback/ALSA/Ogg/
Vorbis/Pango and full supported EGL/GLES2 Wayland/surfaceless/GBM compilation.
Optional ORC JIT/compiler, extra codecs, X11, examples/docs are omitted; no moving
version/dependency download or baseline upgrade. Preserve API checks. Runtime
codecs/devices are not inferred from compilation or parser availability.

Read actual test source before execution. Of134registered originals,17require
real GL contexts and remain compiled/deferred to native session, not passing
skips. Run remaining117once in read-only-input/unprivileged/no-external-route
isolation, private loopback for actual TCP fixtures. Result80OK/37validate SKIP;
all37optional validator programs remain unqualified. All exact descriptors,
selected results and stdout reasons retained; no blanket original-suite pass.
Actual two GL API/matrix portable originals are included; no GL context claim.

Compiled660ELFs/331regular staged files. Actual GstApp/Audio/Video GI and typed
8×8RGB/48kHz stereo caps pass. Two cycles each consume an exact192byte red RGB
video sample and64byte silent stereo audio sample through real appsink, receive
EOS and verify actual pipeline stateNULL. These synthetic samples are not a
speaker, camera, video display, full playback or GNOME screencast.

Controlled native install/post0/0 changed910paths and owns1004entries; archive
`690fa299efae5e634dc3f48b650fe4391486035ee368f11900661f60a1450168`.
Actual installed UID101 synthetic GI/sample/EOS→NULL checks pass in private no-route
namespace; four audio/video/app/GL SDK versions and package audits0. Private
registry removed. Full root transaction verification retained; no preference or
system service changed by postcheck. [Actual source/originals/deferred descriptors/native proof](../evidence/B02-gst-plugins-base-install.json).

Keep exact source named notices and leading runtime C/header conditions, including
bundled FFT code; per-file terms prevail. Media/network input stays untrusted data
in user processes, never a permission source for the privileged executor. These
new parsers must not run as permanent root GUI/agent processes. No privileged
clock helper, automatic external test service or paid provider is introduced.

The missing Gst runtime from the failed first native Shell attempt is now supplied
with base libraries. To prioritize B02's first graphical boundary, a next fresh
native probe may use an actual registered ephemeral PAM/logind/user-bus session
and these new owned inputs before all basic apps are built. Reuse accepted PAM
client/module evidence; opening a session is a consumer operation, not a replay
of the credential suite. No owner credentials or GDM/authenticated-login claim.
Settings/basic apps/real audio and GDM remain explicit final B02 gates. New session
instrumentation must preserve original failure; never rerun its unchanged inputs.
