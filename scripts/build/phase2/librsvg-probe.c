#include <librsvg/rsvg.h>
#include <cairo.h>
#include <gdk-pixbuf/gdk-pixbuf.h>
#include <stdint.h>
#include <string.h>

static const char svg[]="<svg xmlns='http://www.w3.org/2000/svg' width='8' height='8'><rect width='8' height='8' fill='#002040'/></svg>";

int main(void) {
    GError *error=NULL;
    RsvgHandle *h=rsvg_handle_new_from_data((const guint8 *)svg,strlen(svg),&error);
    g_assert_no_error(error); g_assert_nonnull(h);
    cairo_surface_t *s=cairo_image_surface_create(CAIRO_FORMAT_ARGB32,8,8);
    cairo_t *cr=cairo_create(s);
    RsvgRectangle viewport={0,0,8,8};
    g_assert_true(rsvg_handle_render_document(h,cr,&viewport,&error));g_assert_no_error(error);
    cairo_surface_flush(s);
    const uint32_t *pixels=(const uint32_t *)cairo_image_surface_get_data(s);
    g_assert_cmphex(pixels[4*8+4],==,0xff002040);
    cairo_destroy(cr);cairo_surface_destroy(s);g_object_unref(h);
    h=rsvg_handle_new_from_data((const guint8 *)"<svg",4,&error);
    g_assert_null(h);g_assert_nonnull(error);g_clear_error(&error);
    GdkPixbufLoader *loader=gdk_pixbuf_loader_new_with_type("svg",&error);
    g_assert_no_error(error);g_assert_nonnull(loader);
    g_assert_true(gdk_pixbuf_loader_write(loader,(const guchar *)svg,strlen(svg),&error));
    g_assert_no_error(error);g_assert_true(gdk_pixbuf_loader_close(loader,&error));g_assert_no_error(error);
    GdkPixbuf *p=gdk_pixbuf_loader_get_pixbuf(loader);g_assert_nonnull(p);
    g_assert_cmpint(gdk_pixbuf_get_width(p),==,8);g_assert_cmpint(gdk_pixbuf_get_height(p),==,8);
    const guchar *b=gdk_pixbuf_read_pixels(p)+4*gdk_pixbuf_get_rowstride(p)+4*gdk_pixbuf_get_n_channels(p);
    g_assert_cmpint(b[0],==,0);g_assert_cmpint(b[1],==,32);g_assert_cmpint(b[2],==,64);
    if(gdk_pixbuf_get_has_alpha(p))g_assert_cmpint(b[3],==,255);
    g_object_unref(loader);
    g_print("Native SVG/Cairo ARGB=ff002040, Gdk SVG RGB=0,32,64 and malformed SVG refusal passed\n");
    return 0;
}
