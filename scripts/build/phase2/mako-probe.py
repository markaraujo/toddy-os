"""Actual native Mako functional/codegen consumers; no full upstream-suite claim."""
import json
import os
from pathlib import Path
import subprocess
import sys

import mako
from mako.exceptions import SyntaxException
from mako.lookup import TemplateLookup
from mako.template import Template

assert mako.__version__ == '1.4.1'
work = Path(sys.argv[1])
assert work.is_absolute() and not work.exists()
assert work.is_relative_to('/build') or work.is_relative_to('/tmp')
work.mkdir()
checks = []
assert Template('Olá ${name} — Привет').render(name='Toddy') == 'Olá Toddy — Привет'
checks.append('unicode-expression')
assert Template('${value | h}').render(value='<navy>') == '&lt;navy&gt;'
checks.append('html-escape')
assert Template('% for n in values:\n${n}\n% endfor\n').render(values=[1, 2, 3]) == '1\n2\n3\n'
checks.append('loop')
(work / 'base.mako').write_text('HEADER:<%block name="content">base</%block>')
(work / 'child.mako').write_text('<%inherit file="base.mako"/><%block name="content">Olá Toddy</%block>')
lookup = TemplateLookup(directories=[str(work)], module_directory=str(work / 'modules'), input_encoding='utf-8')
assert lookup.get_template('child.mako').render() == 'HEADER:Olá Toddy'
checks.append('lookup-inheritance-cache')
try:
    Template('${unterminated')
except SyntaxException:
    checks.append('invalid-syntax-rejected')
else:
    raise AssertionError('Malformed template accepted')
code = Template('int main(void){int total=0;\n% for n in values:\ntotal+=${n};\n% endfor\nreturn total==42?0:1;}\n').render(values=[20, 22])
(work / 'generated.c').write_text(code)
subprocess.run(['cc', str(work / 'generated.c'), '-o', str(work / 'generated')], check=True)
result = subprocess.run([str(work / 'generated')])
assert result.returncode == 0
checks.append('generated-c-compile-execute')
print(json.dumps({'version':mako.__version__, 'uid':os.getuid(), 'checks':checks,
                  'c_consumer_exit':result.returncode,
                  'scope':'Six actual native library/code-generation consumers; pytest upstream suite not executed'}))
