/* Native GTK/Wayland fixture. Captures actual mapped widgets, not a desktop mockup. */
#include <assert.h>
#include <gtk/gtk.h>
#include <stdio.h>
#include <string.h>
static GtkWindow *window;
static GtkWidget *entry,*button,*status;
static GMainLoop *loop;
static int phase,clicks,initial_width,initial_height;
static gboolean mapped,focus_selected,active;
static gint64 started,activated,click_us;
static void clicked(GtkButton *widget,gpointer data) {
    (void)widget;(void)data;clicks++;click_us=g_get_monotonic_time()-activated;
    gtk_label_set_text(GTK_LABEL(status),"Action completed · Estado atualizado");
}
static void capture(const char *name) {
    int width=gtk_widget_get_width(GTK_WIDGET(window)),height=gtk_widget_get_height(GTK_WIDGET(window));
    assert(width>0 && height>0);
    GdkPaintable *paintable=gtk_widget_paintable_new(GTK_WIDGET(window));
    GtkSnapshot *snapshot=gtk_snapshot_new();
    gdk_paintable_snapshot(paintable,GDK_SNAPSHOT(snapshot),width,height);
    GskRenderNode *node=gtk_snapshot_free_to_node(snapshot);assert(node);
    GskRenderer *renderer=gtk_native_get_renderer(GTK_NATIVE(window));assert(renderer);
    graphene_rect_t rect=GRAPHENE_RECT_INIT(0,0,width,height);
    GdkTexture *texture=gsk_renderer_render_texture(renderer,node,&rect);assert(texture);
    assert(gdk_texture_save_to_png(texture,name));
    g_object_unref(texture);gsk_render_node_unref(node);g_object_unref(paintable);
}
static gboolean tick(gpointer data) {
    (void)data;
    if(phase==0) {
        mapped=gtk_widget_get_mapped(GTK_WIDGET(window));
        if(!mapped && g_get_monotonic_time()-started<15000000)return G_SOURCE_CONTINUE;
        assert(mapped);
        assert(strcmp(G_OBJECT_TYPE_NAME(gdk_display_get_default()),"GdkWaylandDisplay")==0);
        initial_width=gtk_widget_get_width(GTK_WIDGET(window));initial_height=gtk_widget_get_height(GTK_WIDGET(window));
        assert(initial_width>0 && initial_height>0);
        assert(gtk_widget_grab_focus(entry));
        GtkWidget *focus=gtk_window_get_focus(window);
        focus_selected=focus && (focus==entry || gtk_widget_is_ancestor(focus,entry));assert(focus_selected);
        active=gtk_window_is_active(window);capture("gtk-initial.png");
        gtk_editable_set_text(GTK_EDITABLE(entry),"ação offline");
        activated=g_get_monotonic_time();assert(gtk_widget_activate(button));phase=1;return G_SOURCE_CONTINUE;
    }
    if(phase==1) {
        assert(clicks==1 && strcmp(gtk_editable_get_text(GTK_EDITABLE(entry)),"ação offline")==0);
        assert(strcmp(gtk_label_get_text(GTK_LABEL(status)),"Action completed · Estado atualizado")==0);
        capture("gtk-action.png");gtk_window_set_default_size(window,900,620);phase=2;return G_SOURCE_CONTINUE;
    }
    int width=gtk_widget_get_width(GTK_WIDGET(window)),height=gtk_widget_get_height(GTK_WIDGET(window));
    assert(width>initial_width && height>=initial_height);capture("gtk-resized.png");
    printf("{\"scope\":\"Actual native GTK4 mapped Wayland fixture and client renderer snapshots; programmatic actions, not GNOME/GDM/KMS or physical input acceptance\",\"mapped\":%s,\"wayland\":true,\"focus_selected\":%s,\"active_observed\":%s,\"clicks\":%d,\"action_callback_us\":%lld,\"initial_size\":[%d,%d],\"resized_size\":[%d,%d],\"elapsed_us\":%lld}\n",mapped?"true":"false",focus_selected?"true":"false",active?"true":"false",clicks,(long long)click_us,initial_width,initial_height,width,height,(long long)(g_get_monotonic_time()-started));fflush(stdout);
    gtk_window_destroy(window);g_main_loop_quit(loop);return G_SOURCE_REMOVE;
}
int main(void) {
    gtk_init();started=g_get_monotonic_time();loop=g_main_loop_new(NULL,FALSE);
    window=GTK_WINDOW(gtk_window_new());gtk_window_set_title(window,"Toddy OS — native GTK validation fixture");gtk_window_set_default_size(window,640,420);
    GtkWidget *header=gtk_header_bar_new();gtk_window_set_titlebar(window,header);
    GtkWidget *box=gtk_box_new(GTK_ORIENTATION_VERTICAL,18);gtk_widget_set_margin_top(box,24);gtk_widget_set_margin_bottom(box,24);gtk_widget_set_margin_start(box,24);gtk_widget_set_margin_end(box,24);gtk_widget_add_css_class(box,"toddy-native-proof");
    GtkWidget *title=gtk_label_new("Native GTK4 · Wayland");gtk_widget_add_css_class(title,"title-1");gtk_label_set_xalign(GTK_LABEL(title),0);gtk_box_append(GTK_BOX(box),title);
    GtkWidget *description=gtk_label_new("B02 validation fixture. Actual native widgets and rendered state.\nThis is not the integrated GNOME desktop.");gtk_label_set_wrap(GTK_LABEL(description),TRUE);gtk_label_set_xalign(GTK_LABEL(description),0);gtk_box_append(GTK_BOX(box),description);
    entry=gtk_entry_new();gtk_editable_set_text(GTK_EDITABLE(entry),"Offline · Português");gtk_box_append(GTK_BOX(box),entry);
    button=gtk_button_new_with_label("Apply local change");gtk_widget_add_css_class(button,"suggested-action");g_signal_connect(button,"clicked",G_CALLBACK(clicked),NULL);gtk_box_append(GTK_BOX(box),button);
    status=gtk_label_new("Ready · No network or AI required");gtk_label_set_wrap(GTK_LABEL(status),TRUE);gtk_label_set_xalign(GTK_LABEL(status),0);gtk_box_append(GTK_BOX(box),status);gtk_window_set_child(window,box);
    GtkCssProvider *css=gtk_css_provider_new();gtk_css_provider_load_from_string(css,".toddy-native-proof { background-color: #0b1628; color: #e7edf4; }");gtk_style_context_add_provider_for_display(gdk_display_get_default(),GTK_STYLE_PROVIDER(css),GTK_STYLE_PROVIDER_PRIORITY_APPLICATION);g_object_unref(css);
    gtk_window_present(window);g_timeout_add(800,tick,NULL);g_main_loop_run(loop);g_main_loop_unref(loop);return 0;
}
