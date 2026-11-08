"""Small real-file/transport-fixture contracts, never remote model acceptance."""
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import urllib.request
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'runtime/acquisition'))
from download import acquire, AcquisitionError, PublicRedirect
from choices import choose

DATA=b'local fixture model\x00'*140000
SHA=hashlib.sha256(DATA).hexdigest()
RECORD={'url':'https://fixture.invalid/model','sha256':SHA,'bytes':len(DATA),'license':'Apache-2.0'}
CONSENT={'sha256':SHA,'license':'Apache-2.0','network_approved':True}
class Reply(io.BytesIO):
    def __init__(self,data,status=200,headers=None):
        super().__init__(data);self.status=status;self.headers=headers or {'Content-Length':str(len(data))}

class AcquisitionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.cache=Path(self.temp.name)/'cache';self.cache.mkdir(mode=0o700)
        self.calls=[]
    def tearDown(self):self.temp.cleanup()
    def send(self,request):
        self.calls.append(request)
        start=int(request.get_header('Range','bytes=0-')[6:-1])
        return Reply(DATA[start:],206 if start else 200,{'Content-Length':str(len(DATA)-start),
            'Content-Range':f'bytes {start}-{len(DATA)-1}/{len(DATA)}'})
    def run_download(self,**kwargs):
        return acquire(RECORD,self.cache,consent=CONSENT,reserve_bytes=0,_transport=self.send,**kwargs)
    def test_cancel_resume_verified_and_cache_reuse(self):
        stopped=False
        def progress(done,total):
            nonlocal stopped
            stopped=True
        canceled=self.run_download(canceled=lambda:stopped,progress=progress)
        self.assertEqual(canceled['state'],'canceled');self.assertGreater(canceled['bytes'],0)
        self.assertLess(canceled['bytes'],len(DATA));self.assertFalse((self.cache/(SHA+'.gguf')).exists())
        result=self.run_download();self.assertEqual(result['state'],'verified')
        self.assertEqual(self.calls[-1].get_header('Range'),f"bytes={canceled['bytes']}-")
        self.assertEqual(Path(result['path']).read_bytes(),DATA)
        self.assertEqual(Path(result['path']).stat().st_mode&0o777,0o600)
        self.assertFalse(self.run_download()['network_used']);self.assertEqual(len(self.calls),2)
    def test_ignored_range_restarts_owned_partial(self):
        (self.cache/(SHA+'.part')).write_bytes(DATA[:8]);(self.cache/(SHA+'.part')).chmod(0o600)
        with patch.object(self,'send',lambda request:Reply(DATA)):
            self.assertEqual(self.run_download()['state'],'verified')
    def test_invalid_range_never_publishes(self):
        part=self.cache/(SHA+'.part');part.write_bytes(DATA[:8]);part.chmod(0o600)
        with patch.object(self,'send',lambda request:Reply(DATA[8:],206,{'Content-Range':'bytes 9-10/11'})):
            with self.assertRaisesRegex(AcquisitionError,'invalid_resume_response'):self.run_download()
        self.assertEqual(part.read_bytes(),DATA[:8]);self.assertFalse((self.cache/(SHA+'.gguf')).exists())
    def test_hash_size_truncation_and_failure_codes(self):
        for data,code in [(DATA[:-1]+b'X','artifact_integrity_failed'),(DATA[:9],'artifact_incomplete'),(DATA+b'X','artifact_size_exceeded')]:
            with self.subTest(code=code):
                (self.cache/(SHA+'.part')).unlink(missing_ok=True)
                with patch.object(self,'send',lambda request:Reply(data,headers={'Content-Length':str(len(DATA))})):
                    with self.assertRaisesRegex(AcquisitionError,code):self.run_download()
                self.assertFalse((self.cache/(SHA+'.gguf')).exists())
    def test_corrupt_full_partial_never_fetches_or_publishes(self):
        p=self.cache/(SHA+'.part');p.write_bytes(b'x'*len(DATA));p.chmod(0o600)
        with self.assertRaisesRegex(AcquisitionError,'artifact_integrity_failed'):self.run_download()
        self.assertFalse(self.calls)
    def test_consent_space_path_and_existing_conflicts(self):
        with self.assertRaisesRegex(AcquisitionError,'consent'):acquire(RECORD,self.cache,consent={})
        with patch('download.shutil.disk_usage',return_value=type('Disk',(),{'free':0})()):
            with self.assertRaisesRegex(AcquisitionError,'insufficient_space'):self.run_download()
        (self.cache/(SHA+'.part')).unlink()
        outside=Path(self.temp.name)/'outside';outside.write_bytes(b'preserve')
        (self.cache/(SHA+'.part')).symlink_to(outside)
        with self.assertRaises(OSError):self.run_download()
        self.assertEqual(outside.read_bytes(),b'preserve');(self.cache/(SHA+'.part')).unlink()
        final=self.cache/(SHA+'.gguf');final.write_bytes(b'conflict');final.chmod(0o600)
        with self.assertRaisesRegex(AcquisitionError,'existing_artifact_conflict'):self.run_download()
        self.assertEqual(final.read_bytes(),b'conflict');self.assertFalse(self.calls)
    def test_busy_and_hardlink_refused(self):
        import fcntl,os
        with open(self.cache/(SHA+'.lock'),'x+b') as lock:
            os.chmod(lock.name,0o600);fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            with self.assertRaisesRegex(AcquisitionError,'acquisition_busy'):self.run_download()
        part=self.cache/(SHA+'.part');part.write_bytes(b'original');part.chmod(0o600)
        os.link(part,self.cache/'alias')
        with self.assertRaisesRegex(AcquisitionError,'unsafe_cache_file'):self.run_download()
    def test_https_redirect_and_sensitive_error(self):
        redirect=PublicRedirect();request=urllib.request.Request(RECORD['url'],headers={'Authorization':'synthetic','Range':'bytes=8-'})
        with self.assertRaisesRegex(AcquisitionError,'invalid_artifact_url'):
            redirect.redirect_request(request,None,302,'',{},'http://other.invalid/secret?token=private')
        new=redirect.redirect_request(request,None,302,'',{},'https://cdn.invalid/model?signature=private')
        self.assertIsNone(new.get_header('Authorization'));self.assertEqual(new.get_header('Range'),'bytes=8-')
        import http.client
        with patch.object(self,'send',side_effect=http.client.IncompleteRead(b'synthetic-partial')):
            with self.assertRaisesRegex(AcquisitionError,'^artifact_transport_failed$'):self.run_download()
    def test_real_https_range_and_tls_verification(self):
        import http.server, ssl, subprocess, threading, urllib.error
        cert=Path(self.temp.name)/'cert.pem';key=Path(self.temp.name)/'key.pem'
        subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-days','1',
            '-config','/dev/null','-subj','/CN=localhost','-addext','subjectAltName=DNS:localhost',
            '-keyout',str(key),'-out',str(cert)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        ranges=[]
        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_GET(self):
                value=self.headers.get('Range');ranges.append(value)
                offset=int(value[6:-1]) if value else 0
                self.send_response(206 if offset else 200)
                self.send_header('Content-Length',str(len(DATA)-offset))
                if value:self.send_header('Content-Range',f'bytes {offset}-{len(DATA)-1}/{len(DATA)}')
                self.end_headers()
                try:self.wfile.write(DATA[offset:])
                except (BrokenPipeError,ConnectionResetError):pass
        server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
        tls=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);tls.load_cert_chain(cert,key)
        server.socket=tls.wrap_socket(server.socket,server_side=True)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            record={**RECORD,'url':f'https://localhost:{server.server_port}/fixture'}
            def transport(request):
                return urllib.request.build_opener(urllib.request.ProxyHandler({}),
                    urllib.request.HTTPSHandler(context=ssl.create_default_context(cafile=str(cert))),PublicRedirect()).open(request,timeout=3)
            stopped=False
            def progress(done,total):
                nonlocal stopped
                stopped=True
            first=acquire(record,self.cache,consent=CONSENT,_transport=transport,reserve_bytes=0,
                canceled=lambda:stopped,progress=progress)
            self.assertEqual(first['state'],'canceled')
            final=acquire(record,self.cache,consent=CONSENT,_transport=transport,reserve_bytes=0)
            self.assertEqual(final['state'],'verified');self.assertEqual(ranges,[None,f"bytes={first['bytes']}-"])
            self.assertEqual(Path(final['path']).read_bytes(),DATA)
            # Default trust rejects the disposable CA; no verify=False path exists.
            import urllib.error
            untrusted=urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with self.assertRaises(urllib.error.URLError) as rejected:untrusted.open(record['url'],timeout=3)
            self.assertIsInstance(rejected.exception.reason,ssl.SSLCertVerificationError)
        finally:server.shutdown();server.server_close();thread.join()

    def test_backend_choices_have_no_side_effects(self):
        self.assertEqual(choose('deferred')['state'],'deferred')
        args={'adapter_id':'openai','model_id':'fixture','connection_ref':'credential-ref'}
        self.assertEqual(choose('api',**args)['state'],'consent_required')
        self.assertEqual(choose('api',remote_consent=True,**args)['support'],'fixture-only-live-unverified')
        lock=json.loads((Path(__file__).resolve().parents[1]/'config/phase2/local-model.lock.json').read_text())
        self.assertEqual(choose('local',model=lock)['state'],'unsupported_cpu')
        args={'model':lock,'cpu_flags':lock['runtime']['required_cpu_flags'],'memory_bytes':8*1024**3,'cache':self.cache}
        with patch('choices.shutil.disk_usage',return_value=type('Disk',(),{'free':4*1024**3})()):
            self.assertEqual(choose('local',**args)['state'],'acquisition_consent_required')
        with patch('choices.shutil.disk_usage',return_value=type('Disk',(),{'free':0})()):
            self.assertEqual(choose('local',**args)['state'],'insufficient_space')
        self.assertEqual(list(self.cache.iterdir()),[])

if __name__=='__main__':unittest.main(verbosity=2)
