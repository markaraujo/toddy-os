/* Real private-bus construction; no desktop portal/backend/permission claim. */
#include <libportal/portal.h>
#include <libportal/portal-helpers.h>
#include <stdio.h>
int main(void) {
 g_assert_nonnull(g_getenv("DBUS_SESSION_BUS_ADDRESS"));
 g_assert_false(xdp_portal_running_under_flatpak());
 GError *error=NULL;g_assert_false(xdp_portal_running_under_snap(&error));g_assert_no_error(error);
 g_assert_false(xdp_portal_running_under_sandbox());
 for(int i=0;i<2;i++) {
  XdpPortal *portal=xdp_portal_initable_new(&error);g_assert_no_error(error);g_assert_nonnull(portal);g_assert_true(XDP_IS_PORTAL(portal));g_object_unref(portal);
 }
 puts("{\"private_session_bus\":true,\"normal_nonFlatpak_nonSnap_context\":true,\"construct_release_cycles\":2,\"desktop_backend_or_permission_UI_tested\":false}");return 0;
}
