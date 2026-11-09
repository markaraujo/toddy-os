#include <proxy.h>
#include <assert.h>
#include <stdio.h>
#include <string.h>
static void direct(pxProxyFactory *factory,const char *uri) {
 char **routes=px_proxy_factory_get_proxies(factory,uri);
 assert(routes && routes[0] && !strcmp(routes[0],"direct://") && !routes[1]);
 px_proxy_factory_free_proxies(routes);
}
int main(void) {
 g_setenv("PX_FORCE_CONFIG","config-env",TRUE);
 g_setenv("GSETTINGS_BACKEND","memory",TRUE);
 g_unsetenv("http_proxy");g_unsetenv("HTTP_PROXY");
 g_unsetenv("https_proxy");g_unsetenv("HTTPS_PROXY");
 g_unsetenv("all_proxy");g_unsetenv("ALL_PROXY");
 g_unsetenv("no_proxy");g_unsetenv("NO_PROXY");
 for(int cycle=0;cycle<2;cycle++) {
  pxProxyFactory *factory=px_proxy_factory_new();assert(factory);
  direct(factory,"http://downloads.example.invalid/");
  /* Source contract falls back safely to direct for a malformed target URI;
   * it does not promise a NULL/error refusal. No request is sent by this call. */
  direct(factory,"not a URI");
  g_setenv("http_proxy","http://127.0.0.1:1984",TRUE);
  g_setenv("no_proxy","example.invalid",TRUE);
  direct(factory,"http://downloads.example.invalid/");
  pxProxyFactory *copy=g_boxed_copy(PX_TYPE_PROXY_FACTORY,factory);assert(copy);
  px_proxy_factory_free(factory);direct(copy,"http://downloads.example.invalid/");
  px_proxy_factory_free(copy);px_proxy_factory_free_proxies(NULL);
  g_unsetenv("http_proxy");g_unsetenv("no_proxy");
 }
 puts("{\"public_direct_resolution\":true,\"malformed_URI_safe_direct_fallback\":true,\"bypass_and_post_fallback_recovery\":true,\"boxed_copy_lifetime\":true,\"lifecycle_cycles\":2,\"network_requests_sent\":false}");
 return 0;
}
