#include <gsound.h>
int main(void) {
 for(int i=0;i<2;i++) {
  GError *error=NULL;GSoundContext *c=gsound_context_new(NULL,&error);
  g_assert_no_error(error);g_assert_nonnull(c);
  g_assert_true(gsound_context_set_driver(c,"null",&error));g_assert_no_error(error);
  g_assert_true(gsound_context_set_attributes(c,&error,"application.name","Toddy ação","canberra.enable","0",NULL));g_assert_no_error(error);
  g_assert_false(gsound_context_play_simple(c,NULL,&error,"event.id","dialog-information",NULL));g_assert_error(error,GSOUND_ERROR,GSOUND_ERROR_DISABLED);g_clear_error(&error);
  g_assert_true(gsound_context_set_attributes(c,&error,"canberra.enable","1",NULL));g_assert_no_error(error);
  g_assert_true(gsound_context_play_simple(c,NULL,&error,"event.id","dialog-information",NULL));g_assert_no_error(error);
  g_object_unref(c);
 }
 g_print("GSound null backend/Unicode properties/disabled refusal/two recoveries; no audible output\n");
 return 0;
}
