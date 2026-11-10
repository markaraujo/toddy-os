#include <NetworkManager.h>
#include <assert.h>
#include <stdio.h>
#include <string.h>
int main(void) {
 for(int cycle=0;cycle<2;cycle++) {
  GError *error=NULL;
  NMIPAddress *bad=nm_ip_address_new(AF_INET,"invalid-address",24,&error);
  assert(!bad && error);g_clear_error(&error);
  NMIPAddress *address=nm_ip_address_new(AF_INET,"192.0.2.10",24,&error);
  assert(address && !error && nm_ip_address_get_prefix(address)==24);
  assert(!strcmp(nm_ip_address_get_address(address),"192.0.2.10"));
  NMConnection *c=nm_simple_connection_new();
  NMSetting *setting=nm_setting_connection_new();
  g_object_set(setting,NM_SETTING_CONNECTION_ID,"Rede sintética · Toddy",NM_SETTING_CONNECTION_UUID,"b1044400-0158-4158-8158-000000000001",NM_SETTING_CONNECTION_TYPE,NM_SETTING_WIRED_SETTING_NAME,NULL);
  nm_connection_add_setting(c,setting);nm_connection_add_setting(c,nm_setting_wired_new());
  NMSetting *ip4=nm_setting_ip4_config_new();g_object_set(ip4,NM_SETTING_IP_CONFIG_METHOD,NM_SETTING_IP4_CONFIG_METHOD_MANUAL,NULL);
  assert(nm_setting_ip_config_add_address(NM_SETTING_IP_CONFIG(ip4),address));nm_ip_address_unref(address);nm_connection_add_setting(c,ip4);
  NMSetting *ip6=nm_setting_ip6_config_new();g_object_set(ip6,NM_SETTING_IP_CONFIG_METHOD,NM_SETTING_IP6_CONFIG_METHOD_AUTO,NULL);nm_connection_add_setting(c,ip6);
  assert(nm_connection_verify(c,&error) && !error);
  GVariant *v=nm_connection_to_dbus(c,NM_CONNECTION_SERIALIZE_ALL);assert(v);
  NMConnection *copy=nm_simple_connection_new_from_dbus(v,&error);assert(copy && !error);
  assert(!strcmp(nm_connection_get_id(copy),"Rede sintética · Toddy"));
  assert(nm_connection_verify(copy,&error) && !error);
  g_object_unref(copy);g_variant_unref(v);g_object_unref(c);
 }
 puts("{\"typed_UTF8_connection_roundtrip\":true,\"invalid_address_refused\":true,\"recovery_cycles\":2,\"actual_daemon_or_network_tested\":false}");return 0;
}
