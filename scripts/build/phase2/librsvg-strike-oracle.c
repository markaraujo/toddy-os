/* Independent selected Pango1.58 text-decoration oracle; upstream SVG unchanged. */
#include <pango/pangocairo.h>
#include <pango/pangofc-fontmap.h>
#include <fontconfig/fontconfig.h>
#include <assert.h>
#include <stdio.h>
#include <math.h>
#include <stdint.h>

int main(int argc,char **argv) {
    assert(argc==5);
    FcConfig *config=FcConfigCreate();assert(config);
    char *conf=g_build_filename(argv[1],"fonts.conf",NULL);
    assert(FcConfigParseAndLoad(config,(const FcChar8 *)conf,FcTrue));
    assert(FcConfigAppFontAddDir(config,(const FcChar8 *)argv[1]));g_free(conf);
    PangoFontMap *map=pango_cairo_font_map_new_for_font_type(CAIRO_FONT_TYPE_FT);assert(map);
    pango_fc_font_map_set_config(PANGO_FC_FONT_MAP(map),config);FcConfigDestroy(config);
    PangoContext *context=pango_font_map_create_context(map);
    pango_context_set_round_glyph_positions(context,FALSE);
    pango_cairo_context_set_resolution(context,72);
    cairo_font_options_t *options=cairo_font_options_create();
    cairo_font_options_set_antialias(options,CAIRO_ANTIALIAS_GRAY);
    cairo_font_options_set_hint_style(options,CAIRO_HINT_STYLE_NONE);
    cairo_font_options_set_hint_metrics(options,CAIRO_HINT_METRICS_OFF);
    pango_cairo_context_set_font_options(context,options);cairo_font_options_destroy(options);
    PangoLayout *layout=pango_layout_new(context);
    pango_layout_set_auto_dir(layout,FALSE);
    PangoFontDescription *font=pango_font_description_new();
    pango_font_description_set_family(font,"FreeSerif,serif");
    pango_font_description_set_size(font,32*PANGO_SCALE);
    pango_layout_set_font_description(layout,font);
    PangoFont *selected=pango_context_load_font(context,font);assert(selected);
    PangoFontMetrics *metrics=pango_font_get_metrics(selected,pango_language_get_default());
    double strike_y=147-(double)pango_font_metrics_get_strikethrough_position(metrics)/PANGO_SCALE;
    double strike_height=(double)pango_font_metrics_get_strikethrough_thickness(metrics)/PANGO_SCALE;
    pango_font_metrics_unref(metrics);g_object_unref(selected);pango_font_description_free(font);
    pango_layout_set_text(layout,"Line through",-1);
    PangoRectangle ink,logical;pango_layout_get_extents(layout,&ink,&logical);
    PangoAttrList *attrs=pango_attr_list_new();pango_attr_list_insert(attrs,pango_attr_strikethrough_new(TRUE));
    pango_layout_set_attributes(layout,attrs);pango_attr_list_unref(attrs);
    cairo_surface_t *surface=cairo_image_surface_create(CAIRO_FORMAT_ARGB32,480,360);
    cairo_t *cr=cairo_create(surface);cairo_set_source_rgba(cr,1,0,1,1);
    cairo_move_to(cr,39,147-(double)pango_layout_get_baseline(layout)/PANGO_SCALE);
    pango_cairo_show_layout(cr,layout);
    assert(cairo_status(cr)==CAIRO_STATUS_SUCCESS);
    assert(cairo_surface_write_to_png(surface,argv[2])==CAIRO_STATUS_SUCCESS);
    /* The selected Pango source uses min(ink.x,logical.x), max(widths).
       The old golden uses ink bounds. Check every pixel, preserving that failure. */
    double new_x=39+fmin(ink.x,logical.x)/PANGO_SCALE;
    double new_end=new_x+fmax(ink.width,logical.width)/PANGO_SCALE;
    double old_x=39+(double)ink.x/PANGO_SCALE;
    double old_end=old_x+(double)ink.width/PANGO_SCALE;
    cairo_surface_t *actual=cairo_image_surface_create_from_png(argv[3]);
    cairo_surface_t *reference=cairo_image_surface_create_from_png(argv[4]);
    assert(cairo_surface_status(actual)==CAIRO_STATUS_SUCCESS&&cairo_surface_status(reference)==CAIRO_STATUS_SUCCESS);
    assert(cairo_image_surface_get_width(actual)==480&&cairo_image_surface_get_height(actual)==360);
    assert(cairo_image_surface_get_width(reference)==480&&cairo_image_surface_get_height(reference)==360);
    cairo_surface_flush(actual);cairo_surface_flush(reference);
    int changed=0;
    for(int y=0;y<360;y++)for(int x=0;x<480;x++) {
        uint32_t a=*(uint32_t *)(cairo_image_surface_get_data(actual)+y*cairo_image_surface_get_stride(actual)+x*4);
        uint32_t b=*(uint32_t *)(cairo_image_surface_get_data(reference)+y*cairo_image_surface_get_stride(reference)+x*4);
        if(a==b)continue;
        changed++;
        assert(y>=floor(strike_y)&&y<ceil(strike_y+strike_height));
        assert((x>=floor(new_x)&&x<ceil(old_x))||(x>=floor(old_end)&&x<ceil(new_end)));
        assert((a>>24)>0&&((a>>16)&255)==(a>>24)&&(a&255)==(a>>24)&&((a>>8)&255)==0);
    }
    assert(changed==12);
    printf("{\"pango_version\":\"%s\",\"origin_x\":39,\"baseline_y\":147,\"logical_x\":%.9f,\"logical_width\":%.9f,\"ink_x\":%.9f,\"ink_width\":%.9f,\"strike_y\":%.9f,\"strike_height\":%.9f,\"changed_pixels\":%d,\"outside_decoration_changes\":0,\"upstream_golden_passed\":false}\n",
        pango_version_string(),(double)logical.x/PANGO_SCALE,(double)logical.width/PANGO_SCALE,
        (double)ink.x/PANGO_SCALE,(double)ink.width/PANGO_SCALE,strike_y,strike_height,changed);
    cairo_surface_destroy(actual);cairo_surface_destroy(reference);
    cairo_destroy(cr);cairo_surface_destroy(surface);
    g_object_unref(layout);g_object_unref(context);g_object_unref(map);return 0;
}
