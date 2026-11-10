/* Actual owned ZIP extraction/refusal/cancel/recovery; no file-manager GUI claim. */
#include <gnome-autoar/gnome-autoar.h>
#include <gio/gio.h>
#include <stdio.h>
#include <locale.h>
#include <string.h>
typedef struct {guint complete,cancel;GError *error;} State;
static void completed(AutoarExtractor *e,gpointer data){((State*)data)->complete++;}
static void cancelled(AutoarExtractor *e,gpointer data){((State*)data)->cancel++;}
static void failed(AutoarExtractor *e,GError *error,gpointer data){State *s=data;g_assert_null(s->error);s->error=g_error_copy(error);}
static void run(const char *root,const char *archive,const char *destination,int mode) {
 char *src=g_build_filename(root,archive,NULL),*dst=g_build_filename(root,destination,NULL);GFile *input=g_file_new_for_path(src),*output=g_file_new_for_path(dst);
 AutoarExtractor *extractor=autoar_extractor_new(input,output);autoar_extractor_set_output_is_dest(extractor,TRUE);autoar_extractor_set_delete_after_extraction(extractor,FALSE);
 State state={0};g_signal_connect(extractor,"completed",G_CALLBACK(completed),&state);g_signal_connect(extractor,"cancelled",G_CALLBACK(cancelled),&state);g_signal_connect(extractor,"error",G_CALLBACK(failed),&state);
 GCancellable *cancel=g_cancellable_new();if(mode==2)g_cancellable_cancel(cancel);
 autoar_extractor_start(extractor,cancel);
 if(mode==0) {
  g_assert_no_error(state.error);g_assert_cmpuint(state.complete,==,1);g_assert_cmpuint(state.cancel,==,0);g_assert_cmpuint(autoar_extractor_get_completed_files(extractor),==,1);
  char *file=g_build_filename(dst,"documento-ã.txt",NULL),*text=NULL;gsize size=0;GError *error=NULL;g_assert_true(g_file_get_contents(file,&text,&size,&error));g_assert_no_error(error);g_assert_cmpstr(text,==,"Olá Toddy\n");g_assert_cmpuint(autoar_extractor_get_completed_size(extractor),==,strlen(text));g_free(text);g_free(file);
 } else if(mode==1) {g_assert_nonnull(state.error);g_assert_cmpuint(state.complete,==,0);g_assert_cmpuint(state.cancel,==,0);g_assert_false(g_file_test(dst,G_FILE_TEST_EXISTS));}
 else {g_assert_no_error(state.error);g_assert_cmpuint(state.complete,==,0);g_assert_cmpuint(state.cancel,==,1);g_assert_false(g_file_test(dst,G_FILE_TEST_EXISTS));}
 g_assert_true(g_file_test(src,G_FILE_TEST_IS_REGULAR));g_clear_error(&state.error);g_object_unref(cancel);g_object_unref(extractor);g_object_unref(input);g_object_unref(output);g_free(src);g_free(dst);
}
int main(int argc,char **argv) {
 g_assert_cmpint(argc,==,2);g_assert_nonnull(setlocale(LC_ALL,""));const char *charset=NULL;g_assert_true(g_get_charset(&charset));
 for(int i=0;i<2;i++) {
  char normal[32],bad[32],stop[32],recovery[32];g_snprintf(normal,sizeof normal,"normal-%d",i);g_snprintf(bad,sizeof bad,"empty-%d",i);g_snprintf(stop,sizeof stop,"cancel-%d",i);g_snprintf(recovery,sizeof recovery,"recovery-%d",i);
  run(argv[1],"payload.zip",normal,0);run(argv[1],"empty.zip",bad,1);run(argv[1],"payload.zip",stop,2);run(argv[1],"payload.zip",recovery,0);
 }
 puts("{\"UTF8_ZIP_extractions\":4,\"empty_archive_refusals\":2,\"precancelled_no_destination\":2,\"recovery_cycles\":2,\"source_archive_retained\":true,\"GUI_or_mid_extraction_Stop_tested\":false}");return 0;
}
