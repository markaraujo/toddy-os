#include <gio/gio.h>
#include <assert.h>
#include <stdio.h>
#include <string.h>
int main(void) {
 GTlsBackend *backend=g_tls_backend_get_default();assert(backend);
 assert(!strcmp(G_OBJECT_TYPE_NAME(backend),"GTlsBackendGnutls"));
 assert(g_tls_backend_supports_tls(backend));
 GTlsDatabase *database=g_tls_backend_get_default_database(backend);assert(database);
 for(int cycle=0;cycle<2;cycle++) {
  GError *error=NULL;
  GTlsCertificate *bad=g_tls_certificate_new_from_pem("not a certificate",-1,&error);
  assert(!bad && error && error->domain==G_TLS_ERROR && error->code==G_TLS_ERROR_BAD_CERTIFICATE);
  g_clear_error(&error);
  /* OpenSSL's hashed .pem files contain TRUSTED CERTIFICATE auxiliary data.
   * GIO consumes the standard PEM bundle instead, with one object per root. */
  GList *roots=g_tls_certificate_list_new_from_file("/etc/ssl/certs/ca-certificates.crt",&error);
  assert(roots && !error && g_list_length(roots)==121);
  GTlsCertificate *root=NULL;
  for(GList *node=roots;node;node=node->next) {
   char *subject=g_tls_certificate_get_subject_name(node->data);
   if(subject && strstr(subject,"ISRG Root X1"))root=node->data;
   g_free(subject);
  }
  assert(root);
  GTlsCertificateFlags flags=g_tls_database_verify_chain(database,root,
   G_TLS_DATABASE_PURPOSE_AUTHENTICATE_SERVER,NULL,NULL,G_TLS_DATABASE_VERIFY_NONE,NULL,&error);
  assert(flags==0 && !error);g_list_free_full(roots,g_object_unref);
 }
 puts("{\"actual_GnuTLS_GIO_backend\":true,\"default_installed_factory_root_verified\":true,\"malformed_certificate_refused\":true,\"post_refusal_recovery_cycles\":2,\"real_credentials_used\":false}");
 return 0;
}
