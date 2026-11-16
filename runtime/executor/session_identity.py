"""Transport-owned local session lifetime for per-user background services.

A session grant belongs to the owner account while the exact granted interactive
session is active/unlocked/local. A user-systemd broker may be outside its session
scope; logind's same-UID Display is then the authority, never client JSON/PIDs.
"""
import re


def session_id(uid, properties):
    if not isinstance(properties, dict):return None
    session = properties.get('Id')
    user = properties.get('User')
    if (not isinstance(session, str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,128}', session)
            or not isinstance(user, (tuple, list)) or len(user) != 2
            or type(user[0]) is not int or user[0] != uid
            or properties.get('Active') is not True
            or properties.get('Remote') is not False
            or properties.get('LockedHint') is not False):
        return None
    return session
