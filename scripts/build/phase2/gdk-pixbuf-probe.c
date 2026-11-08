/* Real native PNG/JPEG stream roundtrip and invalid-input refusal; no UI claim. */
#include <assert.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <gdk-pixbuf/gdk-pixbuf.h>
#include <gio/gio.h>

static void roundtrip(const char *format,int alpha,int tolerance) {
    GError *error=NULL;
    GdkPixbuf *source=gdk_pixbuf_new(GDK_COLORSPACE_RGB,alpha,8,2,2);assert(source);
    gdk_pixbuf_fill(source,0x001020ff);
    gchar *encoded=NULL;gsize length=0;
    assert(gdk_pixbuf_save_to_buffer(source,&encoded,&length,format,&error,NULL));
    assert(error==NULL && encoded && length>20);
    GInputStream *stream=g_memory_input_stream_new_from_data(encoded,length,NULL);
    GdkPixbuf *decoded=gdk_pixbuf_new_from_stream(stream,NULL,&error);
    assert(decoded && error==NULL && gdk_pixbuf_get_width(decoded)==2 && gdk_pixbuf_get_height(decoded)==2);
    const guchar *pixel=gdk_pixbuf_read_pixels(decoded);assert(pixel);
    assert(abs((int)pixel[0])<=tolerance && abs((int)pixel[1]-16)<=tolerance && abs((int)pixel[2]-32)<=tolerance);
    if(alpha)assert(gdk_pixbuf_get_has_alpha(decoded) && pixel[3]==255);
    g_object_unref(decoded);g_object_unref(stream);g_free(encoded);g_object_unref(source);
}

int main(void) {
    assert(strcmp(gdk_pixbuf_version,"2.44.7")==0);
    roundtrip("png",1,0);roundtrip("jpeg",0,3);
    GError *error=NULL;
    GInputStream *stream=g_memory_input_stream_new_from_data("not an image",12,NULL);
    assert(gdk_pixbuf_new_from_stream(stream,NULL,&error)==NULL && error!=NULL);
    g_clear_error(&error);g_object_unref(stream);
    unsigned found=0;GSList *formats=gdk_pixbuf_get_formats();
    for(GSList *p=formats;p;p=p->next) {
        gchar *name=gdk_pixbuf_format_get_name(p->data);
        if(strcmp(name,"png")==0)found|=1;
        if(strcmp(name,"jpeg")==0)found|=2;
        if(strcmp(name,"gif")==0)found|=4;
        g_free(name);
    }
    g_slist_free(formats);assert(found==7);
    puts("native-pixbuf-png-jpeg-roundtrip-invalid-denied-builtin-png-jpeg-gif");return 0;
}
