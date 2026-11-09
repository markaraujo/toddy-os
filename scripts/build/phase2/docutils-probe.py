"""Exercise the actual man writer and explicit include/raw refusal settings."""
from io import StringIO
import json
import docutils
from docutils.core import publish_string
assert docutils.__version__=='0.23'
text='toddy(1)\n========\n\nNAME\n----\n\nToddy offline.\n'
out=publish_string(text,writer_name='manpage',settings_overrides={'raw_enabled':False,'file_insertion_enabled':False})
assert b'.TH' in out and b'.SH' in out and b'Toddy offline.' in out
warnings=StringIO()
refused=publish_string('.. include:: /etc/passwd\n',writer_name='manpage',settings_overrides={'raw_enabled':False,'file_insertion_enabled':False,'warning_stream':warnings,'halt_level':6})
assert b'root:x:' not in refused and 'disabled' in warnings.getvalue()
print(json.dumps({'scope':'Native Docutils manpage generation and explicit include-disabled refusal; no global document/security policy claim','version':docutils.__version__,'native_consumer_exit':0,'man_output_bytes':len(out)}))
