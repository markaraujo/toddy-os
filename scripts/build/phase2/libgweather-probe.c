#include <libgweather/gweather.h>
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
int main(void) {
 for(int cycle=0;cycle<2;cycle++) {
  GWeatherLocation *world=gweather_location_get_world();assert(world);
  GWeatherLocation *br=gweather_location_find_by_country_code(world,"BR"),*pt=gweather_location_find_by_country_code(world,"PT");
  assert(br && pt && !strcmp(gweather_location_get_country(br),"BR") && !strcmp(gweather_location_get_country(pt),"PT"));
  GWeatherLocation *station=gweather_location_find_by_station_code(world,"SBGR"),*lisbon=gweather_location_find_by_station_code(world,"LPPT");
  assert(station && lisbon && gweather_location_has_coords(station));
  double lat,lon;gweather_location_get_coords(station,&lat,&lon);assert(fabs(lat+23.433333)<1e-6 && fabs(lon+46.466667)<1e-6);
  GVariant *bad=g_variant_ref_sink(g_variant_new_string("not a location tuple"));
  assert(gweather_location_deserialize(world,bad)==NULL);g_variant_unref(bad);
  GVariant *variant=g_variant_ref_sink(gweather_location_serialize(station));assert(variant);
  GWeatherLocation *copy=gweather_location_deserialize(world,variant);assert(copy && gweather_location_equal(station,copy));
  assert(gweather_location_get_distance(station,copy)<1e-6);
  g_object_unref(copy);g_variant_unref(variant);g_object_unref(station);g_object_unref(lisbon);g_object_unref(br);g_object_unref(pt);g_object_unref(world);
 }
 puts("{\"country_BR_PT_lookup\":true,\"SBGR_LPPT_station_lookup\":true,\"coordinates_match_owned_database\":true,\"location_variant_roundtrip\":true,\"wrong_variant_type_refused\":true,\"post_refusal_cycles\":2,\"remote_forecast_or_owner_position_tested\":false}");
 return 0;
}
