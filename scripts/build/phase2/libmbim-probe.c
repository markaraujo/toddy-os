#include <libmbim-glib.h>
int main(void) {
 for(guint i=0;i<2;i++) {
  MbimUuid uuid;g_assert_true(mbim_uuid_from_printable("00000000-0000-0000-0000-000000000001",&uuid));
  gchar *printed=mbim_uuid_get_printable(&uuid);g_assert_cmpstr(printed,==,"00000000-0000-0000-0000-000000000001");g_free(printed);
  g_assert_false(mbim_uuid_from_printable("invalid",&uuid));
  guint8 raw[4]={0};GError *error=NULL;MbimMessage *bad=mbim_message_new(raw,sizeof raw);
  g_assert_false(mbim_message_validate(bad,&error));g_assert_nonnull(error);g_clear_error(&error);mbim_message_unref(bad);
  MbimMessage *message=mbim_message_open_new(42+i,4096);g_assert_true(mbim_message_validate(message,&error));g_assert_no_error(error);
  g_assert_cmpuint(mbim_message_get_transaction_id(message),==,42+i);g_assert_cmpint(mbim_message_get_message_type(message),==,MBIM_MESSAGE_TYPE_OPEN);mbim_message_unref(message);
 }
 g_print("MBIM UUID/message C API/invalid UUID and truncated message refusal/two recoveries; no device access\n");return 0;
}
