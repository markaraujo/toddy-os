"""Actual build-tool YAML parsing/emission and unsafe-constructor refusal."""
import json
import os
import yaml

assert yaml.__version__=='6.0.3'
assert yaml.__with_libyaml__ is False
data={'drivers':['llvmpipe','virgl'],'offline':True,'name':'Toddy — ação'}
assert yaml.safe_load(yaml.safe_dump(data,allow_unicode=True))==data
assert yaml.safe_load('first: &list [1, 2]\nsecond: *list\n')=={'first':[1,2],'second':[1,2]}
try:
    yaml.safe_load('!!python/object/new:builtins.object []')
except yaml.constructor.ConstructorError:
    pass
else:
    raise AssertionError('Unsafe constructor accepted by safe loader')
try:
    yaml.safe_load('list: [unterminated')
except yaml.YAMLError:
    pass
else:
    raise AssertionError('Invalid YAML accepted')
print(json.dumps({'uid':os.getuid(),'version':yaml.__version__,'libyaml_accelerator':False,
                  'safe_unicode_roundtrip':True,'anchor_alias':True,'unsafe_constructor_rejected':True,
                  'invalid_yaml_rejected':True,'scope':'Pure-Python build tool for Mesa; optional C accelerator not built'}))
