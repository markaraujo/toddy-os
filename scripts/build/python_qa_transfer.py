"""Select a recoverable QA transfer step from actual Dpkg states.

This policy performs no installation or acceptance. Its caller must validate
both prepared archives, the predecessor, path ownership and the transaction
record before asserting transaction_started, then verify each action's result.
"""

INSTALLED = 'install ok installed'
CONFIGURABLE = {'install ok unpacked', 'install ok half-configured'}
REINSTALLABLE = {'install reinstreq half-installed', 'install ok half-installed'}


def next_action(predecessor_version, successor_version, core, qa, *, transaction_started):
    if (type(transaction_started) is not bool or predecessor_version == successor_version
            or not all(isinstance(value, str) and value for value in (predecessor_version, successor_version))):
        raise ValueError('Distinct versions and a verified transaction boolean are required')
    def state(value):
        if value is None:
            return None
        if not isinstance(value, (tuple, list)) or len(value) != 2 or not all(isinstance(item, str) for item in value):
            raise ValueError('Expected package version/status pair')
        return tuple(value)
    core, qa = state(core), state(qa)
    if core is None or core[0] not in {predecessor_version, successor_version}:
        raise ValueError('Unexpected or missing Python version; preserve state for diagnosis')
    if qa is not None and qa[0] != successor_version:
        raise ValueError('Unexpected QA version; preserve state for diagnosis')
    if core[0] == predecessor_version:
        if qa is not None:
            raise ValueError('QA appeared before core transfer; inspect the ownership boundary')
        if core[1] == INSTALLED:
            return 'install_core'
        # Real SIGKILL experiment: Dpkg can retain the old version while its
        # payload is half-installed. Version equality is not a success marker.
        if transaction_started and core[1] in REINSTALLABLE:
            return 'install_core'
        raise ValueError('Incomplete predecessor requires the matching recorded transfer attempt')
    if core[1] == INSTALLED and qa == (successor_version, INSTALLED):
        return 'verify_complete'
    if not transaction_started:
        raise ValueError('Partial transfer requires its matching recorded archive identities')
    if core[1] in REINSTALLABLE:
        return 'install_core'
    if core[1] in CONFIGURABLE:
        return 'configure_core'
    if core[1] != INSTALLED:
        raise ValueError('Unreviewed core package state')
    if qa is None or qa[1] in REINSTALLABLE:
        return 'install_qa'
    if qa[1] in CONFIGURABLE:
        return 'configure_qa'
    raise ValueError('Unreviewed QA package state')
