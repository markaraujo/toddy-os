"""Exercise real spellchecking through Spelling GI, without claiming a widget test."""
from pathlib import Path
import json
import os
import sys
work = Path(sys.argv[1])
work.mkdir(mode=0o700)
os.environ.update(HOME=str(work), XDG_CONFIG_HOME=str(work/'config'), XDG_CACHE_HOME=str(work/'cache'))
import gi
gi.require_version('Spelling', '1')
from gi.repository import Spelling
Spelling.init()
provider = Spelling.Provider.get_default()
assert provider.supports_language('en_US')
assert not provider.supports_language('zz_TODDY_UNKNOWN')
assert provider.load_dictionary('zz_TODDY_UNKNOWN') is None
languages = provider.list_languages()
assert languages.get_n_items() > 0
for cycle in range(2):
    checker = Spelling.Checker.new(provider, 'en_US')
    assert checker.get_language() == 'en_US'
    assert checker.check_word('hello', -1)
    assert not checker.check_word('helllo', -1)
    assert 'hello' in checker.list_corrections('helllo')
    checker.ignore_word('toddyzzqvsession')
    assert checker.check_word('toddyzzqvsession', -1)
    checker.set_language('en_US')
    assert checker.check_word('world', -1)
print(json.dumps({'namespace':'Spelling1','language':'en_US','known_and_misspelled_words':True,'hello_suggestion':True,'unsupported_language_refusals':2,'ignore_word':True,'checker_recovery_cycles':2,'graphical_widget_tested':False}))
