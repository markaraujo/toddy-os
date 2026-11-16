"""Fixed installed factory for accepted live-media closure/finalizer bindings.

The finalizer and root composition have not yet qualified the real native image.
There is deliberately no JSON/env/path hook, current-root copy, callable-only
approval, marker-as-success or generic fallback. The coordinator replaces this
factory only with retained native qualification bound to the actual bundle/code.
"""
from .disk_plan import InstallError


def create():
    raise InstallError('installer_composed_closure_unavailable')
