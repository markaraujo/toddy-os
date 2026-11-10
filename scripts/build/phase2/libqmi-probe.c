#include <libqmi-glib.h>
int main(void) {
 for(guint i=0;i<2;i++) {
  GError *error=NULL;QmiMessage *message=qmi_message_new(QMI_SERVICE_DMS,1,42+i,9);g_assert_nonnull(message);
  gsize len=0;const guint8 *bytes=qmi_message_get_raw(message,&len,&error);g_assert_no_error(error);g_assert_nonnull(bytes);g_assert_cmpuint(len,>,3);
  GByteArray *raw=g_byte_array_sized_new(len);g_byte_array_append(raw,bytes,len-1);
  g_assert_null(qmi_message_new_from_raw(raw,&error));g_assert_no_error(error);g_assert_cmpuint(raw->len,==,len-1);
  g_byte_array_append(raw,bytes+len-1,1);QmiMessage *decoded=qmi_message_new_from_raw(raw,&error);g_assert_no_error(error);g_assert_nonnull(decoded);g_assert_cmpuint(raw->len,==,0);
  g_assert_cmpuint(qmi_message_get_transaction_id(decoded),==,42+i);g_assert_cmpint(qmi_message_get_service(decoded),==,QMI_SERVICE_DMS);g_assert_cmpuint(qmi_message_get_message_id(decoded),==,9);qmi_message_unref(decoded);
  g_byte_array_append(raw,bytes,len);raw->data[1]=raw->data[2]=0;
  g_assert_null(qmi_message_new_from_raw(raw,&error));g_assert_nonnull(error);g_clear_error(&error);
  g_byte_array_unref(raw);qmi_message_unref(message);
 }
 g_print("QMI C message roundtrip/incomplete retention/malformed refusal/two fresh recoveries; no device access\n");return 0;
}
