"""Fixed production factory; unavailable evidence fails before journal/disk work."""
from .disk_plan import InstallError


def create():
    from .composition import Composition,LiveBindings
    from .linux_disk import LinuxDisk
    try:
        return LiveBindings(Composition(),LinuxDisk())
    except (OSError,ValueError,KeyError,TypeError,ImportError) as error:
        # Never expose input contents, credentials or a generic fallback binding.
        raise InstallError('installer_composed_closure_unavailable') from error
