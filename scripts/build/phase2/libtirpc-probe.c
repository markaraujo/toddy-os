#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <rpc/xdr.h>

int main(void)
{
    const unsigned char expected[] = { 0x01, 0x23, 0x45, 0x67 };

    for (int cycle = 0; cycle < 2; ++cycle) {
        XDR stream;
        char bytes[sizeof(expected)];
        uint32_t value = UINT32_C(0x01234567);
        xdrmem_create(&stream, bytes, sizeof(bytes), XDR_ENCODE);
        int ok = xdr_u_int32_t(&stream, &value) && xdr_getpos(&stream) == sizeof(bytes);
        xdr_destroy(&stream);
        if (!ok || memcmp(bytes, expected, sizeof(bytes)) != 0)
            return 1;

        value = 0;
        xdrmem_create(&stream, bytes, sizeof(bytes) - 1, XDR_DECODE);
        ok = !xdr_u_int32_t(&stream, &value) && xdr_getpos(&stream) == 0 && value == 0;
        xdr_destroy(&stream);
        if (!ok)
            return 1;

        xdrmem_create(&stream, bytes, sizeof(bytes), XDR_DECODE);
        ok = xdr_u_int32_t(&stream, &value) && value == UINT32_C(0x01234567);
        xdr_destroy(&stream);
        if (!ok)
            return 1;
    }

    puts("TI-RPC XDR byte order, truncation refusal and two local recoveries passed");
    return 0;
}
