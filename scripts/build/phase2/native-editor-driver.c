/* Test-only GTK driver loaded into the actual unmodified editor process.
 * Programmatic widget actions/client renderer snapshots, not physical input. */
#include <gtk/gtk.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
static GtkWindow *window;
static GtkWidget *view;
static const char *root, *file, *mode;
static int phase, ticks, wide_width, wide_height;
static gboolean mapped_snapshot_taken;
static gboolean content_is(const char *expected);
static const char initial[]="Olá Toddy\n";
static const char saved[]="Olá Toddy\nLinha salva offline.\n";
static void fail(const char *reason) { fprintf(stderr,"TODDY_EDITOR_DRIVER_FAIL %s phase=%d ticks=%d window=%s\n",reason,phase,ticks,window?G_OBJECT_TYPE_NAME(window):"none");
 if(window&&view)fprintf(stderr,"TODDY_EDITOR_OBSERVED mapped=%d active=%d width=%d height=%d chars=%d initial_match=%d saved_match=%d\n",gtk_widget_get_mapped(GTK_WIDGET(window)),gtk_window_is_active(window),gtk_widget_get_width(GTK_WIDGET(window)),gtk_widget_get_height(GTK_WIDGET(window)),gtk_text_buffer_get_char_count(gtk_text_view_get_buffer(GTK_TEXT_VIEW(view))),content_is(initial),content_is(saved));fflush(stderr);_exit(97); }
static GtkWidget *find_view(GtkWidget *w) {
 if(GTK_IS_TEXT_VIEW(w))return w;
 for(GtkWidget *child=gtk_widget_get_first_child(w);child;child=gtk_widget_get_next_sibling(child)) { GtkWidget *found=find_view(child);if(found)return found; }
 return NULL;
}
static gboolean implicit_newline(void) {
 GtkTextBuffer *buffer=gtk_text_view_get_buffer(GTK_TEXT_VIEW(view));
 if(!g_object_class_find_property(G_OBJECT_GET_CLASS(buffer),"implicit-trailing-newline"))fail("missing declared GtkSourceBuffer newline contract");
 gboolean value=FALSE;g_object_get(buffer,"implicit-trailing-newline",&value,NULL);return value;
}
static gboolean content_is(const char *expected) {
 GtkTextBuffer *b=gtk_text_view_get_buffer(GTK_TEXT_VIEW(view));GtkTextIter a,z;gtk_text_buffer_get_bounds(b,&a,&z);
 char *text=gtk_text_buffer_get_text(b,&a,&z,FALSE);gsize length=strlen(expected);
 if(implicit_newline()&&length&&expected[length-1]=='\n')length--;
 char *buffer_expected=g_strndup(expected,length);gboolean ok=strcmp(text,buffer_expected)==0;g_free(text);g_free(buffer_expected);return ok;
}
static gboolean file_is_saved(void) { char *text=NULL;gsize size=0;gboolean ok=g_file_get_contents(file,&text,&size,NULL)&&size==strlen(saved)&&memcmp(text,saved,size)==0;g_free(text);return ok; }
static gboolean focus_is_view(void) { GtkWidget *f=gtk_window_get_focus(window);return f&&(f==view||gtk_widget_is_ancestor(f,view)); }
static void capture(const char *suffix) {
 int width=gtk_widget_get_width(GTK_WIDGET(window)),height=gtk_widget_get_height(GTK_WIDGET(window));if(width<=0||height<=0)fail("invalid allocated window geometry");
 GdkPaintable *p=gtk_widget_paintable_new(GTK_WIDGET(window));GtkSnapshot *s=gtk_snapshot_new();gdk_paintable_snapshot(p,GDK_SNAPSHOT(s),width,height);
 GskRenderNode *n=gtk_snapshot_free_to_node(s);if(!n)fail("no actual rendered window node");
 GskRenderer *renderer=gtk_native_get_renderer(GTK_NATIVE(window));if(!renderer)fail("no native renderer");graphene_rect_t rect=GRAPHENE_RECT_INIT(0,0,width,height);
 GdkTexture *texture=gsk_renderer_render_texture(renderer,n,&rect);if(!texture)fail("no rendered texture");
 char *name=g_strdup_printf("%s/gtk-editor-%s-%s.png",root,mode,suffix);if(!gdk_texture_save_to_png(texture,name))fail("PNG write failed");
 g_free(name);g_object_unref(texture);gsk_render_node_unref(n);g_object_unref(p);
}
static gboolean tick(gpointer unused) {
 (void)unused;if(++ticks>100)fail("bounded graphical state deadline exceeded");
 if(phase==0) {
  if(!window) {
   GListModel *windows=gtk_window_get_toplevels();
   for(guint i=0;i<g_list_model_get_n_items(windows);i++) {
    GtkWindow *candidate=g_list_model_get_item(windows,i);
    if(strcmp(G_OBJECT_TYPE_NAME(candidate),"EditorWindow")==0&&gtk_widget_get_mapped(GTK_WIDGET(candidate))) { window=candidate;break; }
    g_object_unref(candidate);
   }
  }
  if(!window)return G_SOURCE_CONTINUE;
  view=find_view(GTK_WIDGET(window));if(!view)return G_SOURCE_CONTINUE;
  if(!content_is(strcmp(mode,"write")==0?initial:saved))return G_SOURCE_CONTINUE;
  if(strcmp(G_OBJECT_TYPE_NAME(gdk_display_get_default()),"GdkWaylandDisplay")!=0)fail("not actual Wayland display");
  fprintf(stderr,"TODDY_EDITOR_BUFFER implicit_trailing_newline=%d chars=%d\n",implicit_newline(),gtk_text_buffer_get_char_count(gtk_text_view_get_buffer(GTK_TEXT_VIEW(view))));
  gtk_window_present(window);if(!gtk_widget_grab_focus(view))fail("text view refused focus");
  gtk_window_set_default_size(window,920,640);phase=1;return G_SOURCE_CONTINUE;
 }
 if(phase==1) {
  if(gtk_widget_get_width(GTK_WIDGET(window))>=800&&!mapped_snapshot_taken) { capture("mapped");mapped_snapshot_taken=TRUE;fprintf(stderr,"TODDY_EDITOR_MAPPED active=%d\n",gtk_window_is_active(window)); }
  if(gtk_widget_get_width(GTK_WIDGET(window))<800||!gtk_window_is_active(window))return G_SOURCE_CONTINUE;
  if(!focus_is_view())fail("actual GTK focus is not editor text view");
  wide_width=gtk_widget_get_width(GTK_WIDGET(window));wide_height=gtk_widget_get_height(GTK_WIDGET(window));capture("opened");
  if(strcmp(mode,"write")==0) { gtk_text_buffer_set_text(gtk_text_view_get_buffer(GTK_TEXT_VIEW(view)),saved,(int)strlen(saved)-(implicit_newline()?1:0));phase=2; }
  else { if(!file_is_saved())fail("reopened bytes differ");gtk_window_set_default_size(window,640,480);phase=4; }
  return G_SOURCE_CONTINUE;
 }
 if(phase==2) {
  if(!content_is(saved)||!gtk_text_buffer_get_modified(gtk_text_view_get_buffer(GTK_TEXT_VIEW(view))))fail("edit did not affect actual document");
  capture("edited");if(!gtk_widget_activate_action(GTK_WIDGET(window),"page.save",NULL))fail("real page.save action unavailable");phase=3;return G_SOURCE_CONTINUE;
 }
 if(phase==3) {
  if(!file_is_saved()||gtk_text_buffer_get_modified(gtk_text_view_get_buffer(GTK_TEXT_VIEW(view))))return G_SOURCE_CONTINUE;
  capture("saved");gtk_window_set_default_size(window,640,480);phase=4;return G_SOURCE_CONTINUE;
 }
 if(gtk_widget_get_width(GTK_WIDGET(window))>=wide_width)return G_SOURCE_CONTINUE;
 if(!content_is(saved)||!file_is_saved()||!focus_is_view()||!gtk_window_is_active(window))fail("saved text, active window or focus lost after resize");
 capture("narrow");char *path=g_strdup_printf("%s/editor-%s-result.json",root,mode);
 char *json=g_strdup_printf("{\"phase\":\"%s\",\"real_editor_window\":true,\"mapped_wayland\":true,\"active_window\":true,\"text_view_focus\":true,\"saved_UTF8_document\":true,\"wide_size\":[%d,%d],\"narrow_size\":[%d,%d],\"programmatic_GTK_driver\":true,\"physical_input_tested\":false}\n",mode,wide_width,wide_height,gtk_widget_get_width(GTK_WIDGET(window)),gtk_widget_get_height(GTK_WIDGET(window)));
 if(!g_file_set_contents(path,json,-1,NULL))fail("result write failed");g_free(path);g_free(json);gtk_window_close(window);g_object_unref(window);window=NULL;return G_SOURCE_REMOVE;
}
__attribute__((constructor)) static void start_driver(void) {
 root=g_getenv("TODDY_EDITOR_TEST_ROOT");file=g_getenv("TODDY_EDITOR_TEST_FILE");mode=g_getenv("TODDY_EDITOR_TEST_PHASE");
 if(!root||!file||!mode||!g_str_has_prefix(root,"/tmp/toddy-editor-native-")||!g_str_has_prefix(file,root)||getuid()!=101||getgid()!=101)fail("invalid private test context");
 if(strcmp(mode,"write")&&strcmp(mode,"reopen"))fail("invalid phase");g_timeout_add(500,tick,NULL);
}
