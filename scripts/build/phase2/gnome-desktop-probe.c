#define GNOME_DESKTOP_USE_UNSTABLE_API
#include <assert.h>
#include <libgnome-desktop/gnome-languages.h>
#include <libgnome-desktop/gnome-xkb-info.h>
#include <stdio.h>
#include <string.h>

int main(void)
{
    char *language=gnome_get_language_from_locale("pt_BR.UTF-8","C");
    char *country=gnome_get_country_from_locale("pt_BR.UTF-8","C");
    assert(language && strcmp(language,"Portuguese")==0);
    assert(country && strcmp(country,"Brazil")==0);
    assert(g_utf8_validate(language,-1,NULL) && g_utf8_validate(country,-1,NULL));
    g_free(language);g_free(country);
    GnomeXkbInfo *info=gnome_xkb_info_new();
    assert(info);
    const char *name=NULL,*short_name=NULL,*layout=NULL,*variant=NULL;
    assert(gnome_xkb_info_get_layout_info(info,"br",&name,&short_name,&layout,&variant));
    assert(name && g_utf8_validate(name,-1,NULL) && layout && strcmp(layout,"br")==0);
    assert(!gnome_xkb_info_get_layout_info(info,"toddy-nonexistent-layout",NULL,NULL,NULL,NULL));
    g_object_unref(info);
    puts("native GNOME Desktop Portuguese/Brazil ISO data and Brazilian keyboard lookup/unknown-layout refusal; no actual desktop or keyboard event");
    return 0;
}
