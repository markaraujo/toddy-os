from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts/build/phase2'))
from llvm_recover import merge_support_results,RELATIVE,SUPPORT


class UnitRecoveryTests(unittest.TestCase):
    def original(self):
        return [{'name':'LLVM-Unit :: ADT/Passed','code':'PASS'},
                {'name':SUPPORT+'Other/Passed','code':'PASS'},
                {'name':RELATIVE,'code':'FAIL','output':'Which is: "elative/path.h"'}]

    def corrected(self):
        return [{'name':SUPPORT+'Other/Passed','code':'PASS'},{'name':RELATIVE,'code':'PASS'}]

    def test_combines_actual_recheck_without_mutating_original(self):
        old=self.original();result=merge_support_results(old,self.corrected())
        self.assertEqual([r['code'] for r in result],['PASS']*3)
        self.assertEqual(old[-1]['code'],'FAIL')

    def test_unknown_or_additional_failure_is_never_qualified(self):
        old=self.original();old[0]['code']='FAIL'
        with self.assertRaises(AssertionError):merge_support_results(old,self.corrected())
        old=self.original();old[-1]['output']='different failure'
        with self.assertRaises(AssertionError):merge_support_results(old,self.corrected())

    def test_missing_skipped_or_failed_affected_case_refused(self):
        with self.assertRaises(AssertionError):merge_support_results(self.original(),self.corrected()[:1])
        for code in ['FAIL','UNSUPPORTED']:
            new=self.corrected();new[-1]['code']=code
            with self.assertRaises(AssertionError):merge_support_results(self.original(),new)
