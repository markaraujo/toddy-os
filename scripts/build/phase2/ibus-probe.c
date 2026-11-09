#include <ibus.h>
#include <assert.h>
#include <stdio.h>
#include <string.h>
int main(void) {
 ibus_init();
 for(int cycle=0;cycle<2;cycle++) {
  IBusText *text=ibus_text_new_from_string("Toddy: ação 🐶");
  g_object_ref_sink(text);
  GVariant *v=g_variant_ref_sink(ibus_serializable_serialize(IBUS_SERIALIZABLE(text)));
  IBusSerializable *copy=ibus_serializable_deserialize(v);
  assert(IBUS_IS_TEXT(copy));g_object_ref_sink(copy);
  assert(!strcmp(ibus_text_get_text(IBUS_TEXT(copy)),"Toddy: ação 🐶"));
  g_object_unref(copy);g_variant_unref(v);g_object_unref(text);
  guint key=0,mods=0;
  assert(!ibus_key_event_from_string("ToddyUnknownModifier+a",&key,&mods));
  assert(ibus_key_event_from_string("Control+a",&key,&mods));
  assert(key==IBUS_KEY_a && mods==IBUS_CONTROL_MASK);
  assert(ibus_keyval_to_unicode(ibus_unicode_to_keyval(0x00e3))==0x00e3);
 }
 puts("{\"UTF8_serialization_roundtrip\":true,\"unknown_modifier_refused\":true,\"valid_key_recovery\":true,\"cycles\":2,\"display_or_real_input_tested\":false}");
 return 0;
}
