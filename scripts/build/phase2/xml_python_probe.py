"""Actual Python XML Unicode/XPath/lifetime and external-entity policy checks."""
import json
from pathlib import Path
import tempfile
import libxml2


def main():
    doc=libxml2.parseDoc('<root><item>ação 日本語</item></root>')
    assert doc.xpathEval('string(/root/item)')=='ação 日本語'
    doc.freeDoc()
    assert libxml2.XML_PARSE_NO_XXE==8388608
    with tempfile.TemporaryDirectory(prefix='toddy-xml-binding-') as name:
        path=Path(name)/'public-fixture.txt';path.write_text('TODDY_PUBLIC_ENTITY_FIXTURE')
        xml='<!DOCTYPE root [<!ENTITY e SYSTEM "'+path.as_uri()+'">]><root>&e;</root>'
        allowed=libxml2.readDoc(xml,None,None,libxml2.XML_PARSE_NOENT)
        assert allowed.getRootElement().content=='TODDY_PUBLIC_ENTITY_FIXTURE';allowed.freeDoc()
        denied=libxml2.readDoc(xml,None,None,libxml2.XML_PARSE_NOENT|libxml2.XML_PARSE_NO_XXE)
        assert denied.getRootElement().content=='';denied.freeDoc()
    print(json.dumps({'scope':'Native optional Python binding semantic consumer; not graphical acceptance',
        'unicode_xpath':True,'explicit_document_lifetime':True,'external_entity_positive_control':True,'no_xxe_refusal':True}))


if __name__=='__main__':main()
