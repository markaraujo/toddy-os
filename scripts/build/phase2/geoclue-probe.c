#include <geoclue.h>
#include <gio/gio.h>
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
int main(void) {
 for(int cycle=0;cycle<2;cycle++) {
  GClueLocation *location=gclue_location_skeleton_new();assert(location);
  gclue_location_set_latitude(location,-23.433333);gclue_location_set_longitude(location,-46.466667);
  gclue_location_set_accuracy(location,5.0);gclue_location_set_description(location,"Posição sintética · Toddy");
  assert(fabs(gclue_location_get_latitude(location)+23.433333)<1e-9);
  assert(!strcmp(gclue_location_get_description(location),"Posição sintética · Toddy"));
  GVariant *props=g_dbus_interface_skeleton_get_properties(G_DBUS_INTERFACE_SKELETON(location));assert(props);
  const char *wrong=NULL;assert(!g_variant_lookup(props,"Latitude","&s",&wrong));
  double lat=0;assert(g_variant_lookup(props,"Latitude","d",&lat) && fabs(lat+23.433333)<1e-9);
  g_variant_unref(props);g_object_unref(location);
  GClueClient *client=gclue_client_skeleton_new();assert(client);
  gclue_client_set_desktop_id(client,"org.toddy.NativeGeoProbe");
  assert(!strcmp(gclue_client_get_desktop_id(client),"org.toddy.NativeGeoProbe"));g_object_unref(client);
 }
 puts("{\"actual_GObject_DBUS_skeletons\":true,\"UTF8_typed_properties\":true,\"wrong_variant_lookup_refused\":true,\"typed_property_recovery_cycles\":2,\"actual_service_authorization_or_owner_position_tested\":false}");
 return 0;
}
