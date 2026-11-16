import io
import json
import unittest
from unittest.mock import patch

from runtime.ui import cli


class TerminalTests(unittest.TestCase):
    def test_lost_acceptance_uses_lookup_without_resubmission(self):
        calls=[]
        class Service:
            def call(self, method, *args):
                calls.append(method)
                if method=='GetCapabilities':
                    return json.dumps({'version':1,'profile_id':'owner','profile_revision':'a'*64,
                        'features':['durable-tasks','cancel','agent-text-v1'],'tools':[],
                        'agent_backend':True,'provider_mode':'local'})
                if method=='SubmitTask': raise OSError('lost reply')
                if method=='LookupRequest': return json.dumps({'version':1,'found':True,'task':{'task_id':'accepted'}})
                raise AssertionError(method)
        with patch.object(cli,'follow',return_value=0) as follow:
            self.assertEqual(cli.submit(Service(),'hello',request_id='known',output=io.StringIO()),0)
            self.assertEqual(follow.call_args.args[1],'accepted')
        self.assertEqual(calls,['GetCapabilities','SubmitTask','LookupRequest'])

    def test_unknown_acceptance_reports_request_and_never_replays(self):
        class Service:
            def call(self, method, *args):
                if method=='GetCapabilities':
                    return json.dumps({'version':1,'profile_id':'owner','profile_revision':'a'*64,
                        'features':['durable-tasks','cancel','agent-text-v1'],'tools':[],
                        'agent_backend':True,'provider_mode':'local'})
                raise OSError('offline')
        output=io.StringIO()
        self.assertEqual(cli.submit(Service(),'hello',request_id='known',output=output),3)
        self.assertIn('lookup owner known',output.getvalue())

    def test_interrupt_requests_stop_then_observes_completion_and_drains_text(self):
        calls=[]
        class Service:
            once=False
            def call(self,method,*args):
                calls.append(method)
                if method=='GetTask':
                    if not self.once:
                        self.once=True
                        raise KeyboardInterrupt()
                    return json.dumps({'version':1,'task_id':'known','profile_revision':'a'*64,
                        'sequence':2,'state':'canceled','cancel_requested':True,'result_uncertain':False,
                        'summary':'Stopped safely','operation_id':None})
                if method=='RequestCancel': return '{}'
                if method=='GetTaskText':
                    return json.dumps({'version':1,'task_id':'known','chunks':[{'sequence':1,'text':'partial\x1b[2J'}],
                        'next_sequence':1,'latest_sequence':1,'complete':True,'history_enabled':False})
                if method=='AcknowledgeTaskText':return '{"version":1}'
                raise AssertionError(method)
        output=io.StringIO()
        self.assertEqual(cli.follow(Service(),'known',output=output),2)
        self.assertEqual(calls,['GetTask','RequestCancel','GetTask','GetTaskText','AcknowledgeTaskText'])
        self.assertNotIn('\x1b',output.getvalue())

    def test_help_imports_no_graphical_or_bus_runtime(self):
        import subprocess, sys
        result=subprocess.run([sys.executable,'-m','runtime.ui.cli','--help'],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('select-profile',result.stdout)


if __name__=='__main__':unittest.main()
