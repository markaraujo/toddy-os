#include <cups/cups.h>
#include <assert.h>
#include <stdio.h>
#include <string.h>

int main(void) {
    for (int cycle = 0; cycle < 2; cycle++) {
        ipp_t *request = ippNewRequest(IPP_OP_GET_PRINTER_ATTRIBUTES);
        assert(request != NULL);
        ipp_attribute_t *uri = ippAddString(request, IPP_TAG_OPERATION, IPP_TAG_URI,
            "printer-uri", NULL, "ipp://localhost/printers/toddy-fixture");
        assert(uri != NULL);
        ipp_attribute_t *info = ippAddString(request, IPP_TAG_PRINTER, IPP_TAG_TEXT,
            "printer-info", NULL, "Toddy — impressão local");
        assert(info != NULL);
        assert(strcmp(ippGetString(info, 0, NULL), "Toddy — impressão local") == 0);
        assert(ippFindAttribute(request, "absent-attribute", IPP_TAG_ZERO) == NULL);
        assert(ippFindAttribute(request, "printer-info", IPP_TAG_TEXT) == info);
        ippDeleteAttribute(request, info);
        assert(ippFindAttribute(request, "printer-info", IPP_TAG_ZERO) == NULL);
        info = ippAddString(request, IPP_TAG_PRINTER, IPP_TAG_TEXT,
            "printer-info", NULL, "Recuperado");
        assert(info != NULL && strcmp(ippGetString(info, 0, NULL), "Recuperado") == 0);
        assert(ippLength(request) > 8);
        ippDelete(request);
    }
    puts("CUPS local IPP Unicode/add/find/delete/absent attribute/two recoveries; no server, jobs or printer access");
    return 0;
}
