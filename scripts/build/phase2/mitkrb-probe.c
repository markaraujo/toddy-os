#include <krb5.h>
#include <assert.h>
#include <stdio.h>
#include <string.h>

int main(void) {
    krb5_context context = NULL;
    assert(krb5_init_context(&context) == 0);
    for (int cycle = 0; cycle < 2; cycle++) {
        krb5_principal principal = NULL, copy = NULL, bad = NULL;
        krb5_ccache cache = NULL, reopened = NULL, empty = NULL;
        char *name = NULL, *cache_name = NULL;
        assert(krb5_parse_name_flags(context, "toddy@EXAMPLE.INVALID",
               KRB5_PRINCIPAL_PARSE_REQUIRE_REALM, &principal) == 0);
        assert(krb5_unparse_name(context, principal, &name) == 0);
        assert(strcmp(name, "toddy@EXAMPLE.INVALID") == 0);
        assert(krb5_parse_name_flags(context, "missing-realm",
               KRB5_PRINCIPAL_PARSE_REQUIRE_REALM, &bad) != 0 && bad == NULL);
        assert(krb5_cc_new_unique(context, "MEMORY", NULL, &cache) == 0);
        assert(krb5_cc_initialize(context, cache, principal) == 0);
        assert(krb5_cc_get_full_name(context, cache, &cache_name) == 0);
        assert(krb5_cc_resolve(context, cache_name, &reopened) == 0);
        assert(krb5_cc_get_principal(context, reopened, &copy) == 0);
        assert(krb5_principal_compare(context, principal, copy));
        krb5_free_principal(context, copy); copy = NULL;
        assert(krb5_cc_close(context, reopened) == 0);
        assert(krb5_cc_destroy(context, cache) == 0);
        assert(krb5_cc_resolve(context, cache_name, &empty) == 0);
        assert(krb5_cc_get_principal(context, empty, &copy) != 0 && copy == NULL);
        assert(krb5_cc_destroy(context, empty) == 0);
        krb5_free_string(context, cache_name);
        krb5_free_unparsed_name(context, name);
        krb5_free_principal(context, principal);
    }
    krb5_free_context(context);
    puts("Kerberos local principal/MEMORY cache reopen/destroy/realm and absent-principal refusals/two recoveries; no tickets or network authentication");
    return 0;
}
