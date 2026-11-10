#include <bluetooth-settings-widget.h>
int main(void) {
 GType type=bluetooth_settings_widget_get_type();
 g_assert_true(g_type_is_a(type,GTK_TYPE_WIDGET));
 g_assert_cmpstr(g_type_name(type),==,"BluetoothSettingsWidget");
 g_print("Installed BluetoothSettingsWidget C SDK/type ABI only; no widget instantiated\n");
 return 0;
}
