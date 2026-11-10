/* Non-widget value ownership and enum consumer; real display remains required. */
#include <handy.h>
#include <string.h>
#include <stdio.h>
int main(void) {
 g_assert_cmpint(HDY_MAJOR_VERSION,==,1);g_assert_cmpint(HDY_MINOR_VERSION,==,8);g_assert_cmpint(HDY_MICRO_VERSION,==,3);
 for(int i=0;i<2;i++) {
  GValue input=G_VALUE_INIT,copy=G_VALUE_INIT;g_value_init(&input,G_TYPE_STRING);g_value_set_string(&input,"Toddy ã");
  HdyValueObject *value=hdy_value_object_new(&input);g_value_set_string(&input,"changed");
  g_assert_cmpstr(hdy_value_object_get_string(value),==,"Toddy ã");
  g_value_init(&copy,G_TYPE_STRING);hdy_value_object_copy_value(value,&copy);g_object_unref(value);g_assert_cmpstr(g_value_get_string(&copy),==,"Toddy ã");
  g_value_unset(&input);g_value_unset(&copy);
  value=hdy_value_object_new_take_string(g_strdup("Recovered ã"));char *text=hdy_value_object_dup_string(value);g_object_unref(value);g_assert_cmpstr(text,==,"Recovered ã");g_free(text);
  GEnumClass *klass=g_type_class_ref(HDY_TYPE_NAVIGATION_DIRECTION);GEnumValue *ev=g_enum_get_value(klass,HDY_NAVIGATION_DIRECTION_BACK);g_assert_nonnull(ev);
  HdyEnumValueObject *object=hdy_enum_value_object_new(ev);g_assert_cmpint(hdy_enum_value_object_get_value(object),==,HDY_NAVIGATION_DIRECTION_BACK);g_assert_cmpstr(hdy_enum_value_object_get_nick(object),==,ev->value_nick);g_object_unref(object);g_type_class_unref(klass);
 }
 puts("{\"header_version\":\"1.8.3\",\"UTF8_value_copy_ownership\":true,\"take_dup_ownership\":true,\"navigation_enum\":true,\"reset_cycles\":2,\"widget_or_display_tested\":false}");
 return 0;
}
