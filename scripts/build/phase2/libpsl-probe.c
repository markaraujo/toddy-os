#include <libpsl.h>
#include <assert.h>
#include <stdio.h>
#include <string.h>
int main(void) {
 for(int cycle=0;cycle<2;cycle++) {
  const psl_ctx_t *builtin=psl_builtin();assert(builtin);
  assert(psl_is_public_suffix(builtin,"co.uk") && !psl_is_public_suffix(builtin,"example.co.uk"));
  assert(!strcmp(psl_registrable_domain(builtin,"www.example.co.uk"),"example.co.uk"));
  assert(!psl_is_cookie_domain_acceptable(builtin,"www.example.co.uk","co.uk"));
  assert(psl_is_cookie_domain_acceptable(builtin,"www.example.co.uk","example.co.uk"));
  char *lower=NULL;assert(psl_str_to_utf8lower("ÖSTERREICH.AT","UTF-8",NULL,&lower)==PSL_SUCCESS && lower && !strcmp(lower,"österreich.at"));psl_free_string(lower);lower=NULL;
  assert(psl_str_to_utf8lower("Ö","toddy-invalid-charset",NULL,&lower)==PSL_ERR_CONVERTER && lower==NULL);
  FILE *input=tmpfile();assert(input && fputs("example\n*.wild.example\n!exception.wild.example\n",input)>=0 && fflush(input)==0);rewind(input);
  psl_ctx_t *private=psl_load_fp(input);assert(private);assert(fclose(input)==0);
  assert(psl_is_public_suffix(private,"a.wild.example") && !psl_is_public_suffix(private,"exception.wild.example"));
  assert(!strcmp(psl_registrable_domain(private,"www.exception.wild.example"),"exception.wild.example"));psl_free(private);
  assert(psl_is_public_suffix(builtin,"co.uk"));
 }
 puts("{\"builtin_public_suffix_and_registrable_domain\":true,\"public_suffix_cookie_refused\":true,\"ICU_UTF8_lowercase\":true,\"invalid_converter_refused\":true,\"private_runtime_wildcard_and_exception\":true,\"recovery_cycles\":2}");return 0;
}
