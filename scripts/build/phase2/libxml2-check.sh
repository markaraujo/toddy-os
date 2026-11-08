#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/h06/common.sh
chroot_run <<'NATIVE'
set -euo pipefail
[[ $(pkg-config --modversion libxml-2.0) == 2.15.3 ]]
[[ $(dpkg-query -W -f='${Status}' libxml2) == 'install ok installed' ]]
test -z "$(dpkg --audit)"
apt-get check
work=$(mktemp -d /tmp/toddy-xml-consumer.XXXXXX)
trap 'rm -rf "$work"' EXIT
cat > "$work/probe.c" <<'C'
#include <libxml/parser.h>
#include <libxml/tree.h>
#include <string.h>
static xmlParserErrors deny(void *data, const char *url, const char *id,
                           xmlResourceType type, xmlParserInputFlags flags,
                           xmlParserInput **out) {
    (void)url; (void)id; (void)type; (void)flags;
    (*(int *)data)++; *out = NULL; return XML_IO_ENOENT;
}
int main(void) {
    const char *normal = "<root><value>Pronto</value></root>";
    const char *external = "<!DOCTYPE root [<!ENTITY data SYSTEM 'file:///toddy-dummy-secret'>]><root>&data;</root>";
    xmlDoc *doc; xmlParserCtxt *context; int calls = 0;
    if (strcmp(xmlParserVersion, "21503")) return 1;
    doc = xmlReadMemory(normal, (int)strlen(normal), "fixture.xml", NULL, XML_PARSE_NONET | XML_PARSE_NO_XXE);
    if (!doc || strcmp((char *)xmlDocGetRootElement(doc)->name, "root")) return 2;
    xmlFreeDoc(doc);
    context = xmlNewParserCtxt(); if (!context) return 3;
    xmlCtxtSetResourceLoader(context, deny, &calls);
    doc = xmlCtxtReadMemory(context, external, (int)strlen(external), "fixture.xml", NULL,
                           XML_PARSE_NOENT | XML_PARSE_NONET | XML_PARSE_NO_XXE | XML_PARSE_NOERROR | XML_PARSE_NOWARNING);
    if (!doc || calls != 0) return 4;
    xmlFreeDoc(doc); xmlFreeParserCtxt(context);
    /* Positive control: the same denying loader sees the attempted external
       entity when NO_XXE is omitted; no real file/network resource is opened. */
    context = xmlNewParserCtxt(); if (!context) return 5;
    xmlCtxtSetResourceLoader(context, deny, &calls);
    doc = xmlCtxtReadMemory(context, external, (int)strlen(external), "fixture.xml", NULL,
                           XML_PARSE_NOENT | XML_PARSE_NONET | XML_PARSE_NOERROR | XML_PARSE_NOWARNING);
    if (calls != 1) return 6;
    if (doc) xmlFreeDoc(doc);
    xmlFreeParserCtxt(context); xmlCleanupParser(); return 0;
}
C
cc "$work/probe.c" $(pkg-config --cflags --libs libxml-2.0) -o "$work/probe"
"$work/probe"
printf '<root/>\n' | xmllint --nonet --noout -
if printf '<root>\n' | xmllint --nonet --noout - 2>"$work/expected-error";then exit 1;fi
xml2-config --libs
ldd /usr/lib/libxml2.so
NATIVE
