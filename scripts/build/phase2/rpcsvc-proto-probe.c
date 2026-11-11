#include "fixture.h"
#include <stdio.h>
#include <string.h>

int main(void)
{
    for (int cycle = 0; cycle < 2; ++cycle) {
        char buffer[64];
        XDR stream;
        fixture input = { .sequence = 42, .label = "toddy" };
        fixture decoded = { 0 };
        xdrmem_create(&stream, buffer, sizeof(buffer), XDR_ENCODE);
        if (!xdr_fixture(&stream, &input))
            return 1;
        unsigned int length = xdr_getpos(&stream);
        xdr_destroy(&stream);

        xdrmem_create(&stream, buffer, length, XDR_DECODE);
        int ok = xdr_fixture(&stream, &decoded) &&
                 decoded.sequence == 42 && decoded.label &&
                 strcmp(decoded.label, "toddy") == 0;
        xdr_destroy(&stream);
        xdr_free((xdrproc_t)xdr_fixture, (char *)&decoded);
        if (!ok)
            return 1;
    }
    puts("Generated rpcgen XDR C round-tripped two records");
    return 0;
}
