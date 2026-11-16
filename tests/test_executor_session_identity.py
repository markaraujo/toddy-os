"""Only logind-owned active local unlocked same-UID session metadata can bind grants."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'runtime/executor'))
from session_identity import session_id


class SessionIdentityTests(unittest.TestCase):
    def test_active_local_owner_session(self):
        self.assertEqual(session_id(1000,{'Id':'c4','User':(1000,'/user/1000'),'Active':True,'Remote':False,'LockedHint':False}),'c4')

    def test_lock_inactive_remote_wrong_uid_and_missing_fields_deny(self):
        good={'Id':'c4','User':(1000,'/user/1000'),'Active':True,'Remote':False,'LockedHint':False}
        for patch in [{'Active':False},{'LockedHint':True},{'Remote':True},{'User':(1001,'/user/1001')},
                      {'User':(True,'/user/1')},{'Id':'../c4'},{'Active':1},{'LockedHint':None}]:
            self.assertIsNone(session_id(1000,{**good,**patch}))
        for key in good:
            row=good.copy();row.pop(key);self.assertIsNone(session_id(1000,row))


if __name__=='__main__':unittest.main()
