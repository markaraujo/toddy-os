#include <geocode-glib/geocode-glib.h>
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
int main(void) {
 for(int cycle=0;cycle<2;cycle++) {
  GeocodeLocation *location=geocode_location_new_with_description(-15.793889,-47.882778,1000,"Brasília · Toddy");
  assert(location && !strcmp(geocode_location_get_description(location),"Brasília · Toddy"));
  GError *error=NULL;
  assert(!geocode_location_set_from_uri(location,"geo:invalid",&error) && error);g_clear_error(&error);
  assert(geocode_location_set_from_uri(location,"geo:-15.793889,-47.882778",&error) && !error);
  assert(fabs(geocode_location_get_latitude(location)+15.793889)<1e-6);
  assert(fabs(geocode_location_get_longitude(location)+47.882778)<1e-6);
  gchar *uri=geocode_location_to_uri(location,GEOCODE_LOCATION_URI_SCHEME_GEO);assert(uri);
  GeocodeLocation *copy=geocode_location_new(0,0,GEOCODE_LOCATION_ACCURACY_UNKNOWN);
  assert(geocode_location_set_from_uri(copy,uri,&error) && !error);
  assert(geocode_location_get_distance_from(location,copy)<1e-6);
  g_free(uri);g_object_unref(copy);g_object_unref(location);
 }
 puts("{\"UTF8_location_description\":true,\"geo_URI_roundtrip\":true,\"malformed_URI_refused\":true,\"post_refusal_recovery_cycles\":2,\"remote_geocoding_tested\":false}");
 return 0;
}
