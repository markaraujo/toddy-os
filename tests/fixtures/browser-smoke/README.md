# Native browser consumer fixture

Serve this directory on guest loopback with `python3 -m http.server 8765 --bind
127.0.0.1 --directory <fixture-directory>` and open `http://127.0.0.1:8765/` in
the actual packaged browser as the normal logged-in GNOME owner. Never launch the
browser as root or disable its sandbox. No external assets, keys or account are
needed. Keep this fixture outside the delivered default browser home page.

Record the real application opening, page rendering, keyboard focus, entering
`Toddy OK`, submitting, navigation/Back, and a readable narrow window. Save actual
native scanouts and independently observed normal-owner process identity. The
stored-value page proves only that the same origin/profile can read its value.
To claim restart persistence also record the original browser exiting and a new
process opening the same profile and stored-value page. Do not clear the profile
between these two launches. Use a separate disposable test profile, without owner
credentials. Serve on loopback only; a file URL has different storage semantics.

Source files or host-browser fixture checks are not Toddy GNOME/Firefox runtime
acceptance. Remaining security, offline-failure, privilege and integrated desktop
gates require their own actual guest evidence.
