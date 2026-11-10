#include <bytesize/bs_size.h>
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(void) {
    for (int cycle = 0; cycle < 2; cycle++) {
        BSError *error = NULL;
        int sign = 0;
        BSSize one = bs_size_new_from_str("1 GiB", &error);
        assert(one && !error && bs_size_get_bytes(one, &sign, &error) == UINT64_C(1073741824) && sign == 1 && !error);
        BSSize half = bs_size_new_from_bytes(UINT64_C(536870912), 1);
        BSSize sum = bs_size_add(one, half);
        assert(bs_size_get_bytes(sum, &sign, &error) == UINT64_C(1610612736) && !error);
        BSSize third = bs_size_div_int(sum, 3, &error);
        assert(third && !error && bs_size_cmp(third, half, false) == 0);
        assert(bs_size_new_from_str("not a size", &error) == NULL && error && error->code == BS_ERROR_INVALID_SPEC);
        bs_clear_error(&error); assert(!error);
        assert(bs_size_div_int(one, 0, &error) == NULL && error && error->code == BS_ERROR_ZERO_DIV);
        bs_clear_error(&error); assert(!error);
        BSSize huge = bs_size_new_from_str("18446744073709551616 B", &error);
        assert(huge && !error);
        char *decimal = bs_size_get_bytes_str(huge);
        assert(decimal && strcmp(decimal, "18446744073709551616") == 0);
        free(decimal);
        (void)bs_size_get_bytes(huge, &sign, &error);
        assert(error && error->code == BS_ERROR_OVER);
        bs_clear_error(&error); assert(!error);
        assert(bs_size_get_bytes(one, &sign, &error) == UINT64_C(1073741824) && !error);
        bs_size_free(huge); bs_size_free(third); bs_size_free(sum);
        bs_size_free(half); bs_size_free(one);
    }
    puts("Libbytesize exact binary units/add/divide/big integer/invalid specification/zero division/overflow/two recoveries; no disk access");
    return 0;
}
