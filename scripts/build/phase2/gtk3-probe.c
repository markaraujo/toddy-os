#include <assert.h>
#include <gtk/gtk.h>
#include <stdio.h>

int main(void)
{
    assert(gtk_get_major_version()==3 && gtk_get_minor_version()==24 && gtk_get_micro_version()==52);
    GdkRGBA color;
    assert(gdk_rgba_parse(&color, "#002040"));
    assert(color.red==0.0 && color.alpha==1.0);
    GtkCssProvider *provider=gtk_css_provider_new();
    GError *error=NULL;
    assert(gtk_css_provider_load_from_data(provider, "* { color: #002040; }", -1, &error));
    assert(error==NULL);
    g_object_unref(provider);
    GtkBuilder *builder=gtk_builder_new();
    const char xml[]="<interface><object class='GtkAdjustment' id='value'><property name='lower'>0</property><property name='upper'>100</property><property name='value'>42</property></object></interface>";
    assert(gtk_builder_add_from_string(builder, xml, -1, &error)>0 && error==NULL);
    GtkAdjustment *value=GTK_ADJUSTMENT(gtk_builder_get_object(builder, "value"));
    assert(value && gtk_adjustment_get_value(value)==42.0);
    gtk_adjustment_set_value(value, 43.0);
    assert(gtk_adjustment_get_value(value)==43.0);
    g_object_unref(builder);
    puts("native GTK3.24.52/GDK color/CSS parse/non-widget Builder adjustment update; no window/display acceptance");
    return 0;
}
