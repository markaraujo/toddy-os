#include <gio/gio.h>
#include <gdm-client.h>
#include <assert.h>
#include <stdio.h>
#include <string.h>
int main(void) {
 for(int cycle=0;cycle<2;cycle++) {
  GdmClient *client=gdm_client_new();assert(GDM_IS_CLIENT(client));
  const char *extensions[]={"org.gnome.DisplayManager.UserVerifier.ChoiceList","org.gnome.DisplayManager.UserVerifier.CustomJSON",NULL};
  gdm_client_set_enabled_extensions(client,extensions);
  GStrv copy=gdm_client_get_enabled_extensions(client);
  assert(g_strv_length(copy)==2 && !strcmp(copy[0],extensions[0]) && !strcmp(copy[1],extensions[1]));
  copy[0][0]='X';g_strfreev(copy);copy=gdm_client_get_enabled_extensions(client);
  assert(!strcmp(copy[0],extensions[0]));g_strfreev(copy);
  GCancellable *cancel=g_cancellable_new();g_cancellable_cancel(cancel);GError *error=NULL;
  GdmUserVerifier *verifier=gdm_client_get_user_verifier_sync(client,cancel,&error);
  assert(!verifier && g_error_matches(error,G_IO_ERROR,G_IO_ERROR_CANCELLED));g_clear_error(&error);g_object_unref(cancel);
  copy=gdm_client_get_enabled_extensions(client);assert(g_strv_length(copy)==2 && !strcmp(copy[0],extensions[0]));g_strfreev(copy);
  g_object_unref(client);
 }
 puts("{\"actual_client_and_owned_extension_copies\":true,\"precancelled_connection_refused\":true,\"recovery_cycles\":2,\"actual_login_PAM_or_desktop_tested\":false}");return 0;
}
