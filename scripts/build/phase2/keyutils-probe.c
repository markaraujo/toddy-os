#include <keyutils.h>
#include <stdio.h>
#include <string.h>

int main(void)
{
    if (strcmp(keyutils_version_string, "keyutils-1.6.3") != 0 ||
        strspn(keyutils_build_string, "0123456789-") != 10 ||
        strlen(keyutils_build_string) != 10) {
        fprintf(stderr, "Unexpected keyutils shared library version\n");
        return 1;
    }
    puts("Keyutils C shared version and build metadata verified");
    return 0;
}
