#include <nma-wifi-dialog.h>
#include <nma-cert-chooser.h>
#include <nma-version.h>
#include <assert.h>
#include <stdio.h>
#ifndef TODDY_GTK_MAJOR
#error Explicit GTK ABI required
#endif
int main(void) {
 assert(NMA_MAJOR_VERSION==1 && NMA_MINOR_VERSION==10 && NMA_MICRO_VERSION==6);
 assert(gtk_get_major_version()==TODDY_GTK_MAJOR);
 assert(g_type_is_a(nma_wifi_dialog_get_type(),GTK_TYPE_DIALOG));
 assert(g_type_is_a(nma_cert_chooser_get_type(),GTK_TYPE_WIDGET));
 for(int cycle=0;cycle<2;cycle++) {
  GError *error=NULL;
  NMIPAddress *bad=nm_ip_address_new(AF_INET,"not-an-address",24,&error);
  assert(!bad && error);g_clear_error(&error);
  NMIPAddress *good=nm_ip_address_new(AF_INET,"192.0.2.11",24,&error);
  assert(good && !error);nm_ip_address_unref(good);
 }
 printf("{\"GTK_major\":%d,\"libnma_version\":\"1.10.6\",\"actual_widget_types\":true,\"libnm_refusal_recovery\":true,\"widget_open_or_focus_tested\":false}\n",TODDY_GTK_MAJOR);
 return 0;
}
