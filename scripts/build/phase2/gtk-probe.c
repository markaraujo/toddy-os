#include <gtk/gtk.h>
#include <math.h>

int main(void) {
    g_assert_cmpuint(gtk_get_major_version(),==,4);
    g_assert_cmpuint(gtk_get_minor_version(),==,22);
    g_assert_cmpuint(gtk_get_micro_version(),==,4);
    GtkBitset *bits=gtk_bitset_new_empty();gtk_bitset_add_range(bits,3,4);
    g_assert_cmpuint(gtk_bitset_get_size(bits),==,4);g_assert_true(gtk_bitset_contains(bits,6));
    gtk_bitset_remove(bits,4);g_assert_false(gtk_bitset_contains(bits,4));gtk_bitset_unref(bits);
    const char *names[]={"Toddy","Português","Terminal",NULL};
    GtkStringList *list=gtk_string_list_new(names);
    g_assert_cmpuint(g_list_model_get_n_items(G_LIST_MODEL(list)),==,3);
    g_assert_cmpstr(gtk_string_list_get_string(list,1),==,"Português");
    gtk_string_list_remove(list,0);g_assert_cmpuint(g_list_model_get_n_items(G_LIST_MODEL(list)),==,2);
    g_object_unref(list);
    GdkRGBA color;g_assert_true(gdk_rgba_parse(&color,"#002040"));
    g_assert_true(fabs(color.red)<0.000001&&fabs(color.green-32.0/255)<0.000001&&fabs(color.blue-64.0/255)<0.000001);
    g_print("Native GTK4.22.4 version/bitset/Unicode list model/navy color APIs passed; no window opened\n");
    return 0;
}
