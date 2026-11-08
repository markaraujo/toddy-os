/* Real shipped keymap/state/registry APIs; not a physical keyboard test. */
#include <stdio.h>
#include <string.h>
#include <xkbcommon/xkbcommon.h>
#include <xkbcommon/xkbcommon-keysyms.h>
#include <xkbcommon/xkbregistry.h>

int main(int argc,char **argv) {
    if(argc!=2)return 1;
    int installed=strcmp(argv[1],"/usr/share/xkeyboard-config-2")==0;
    struct xkb_context *ctx=xkb_context_new(installed?XKB_CONTEXT_NO_ENVIRONMENT_NAMES:XKB_CONTEXT_NO_DEFAULT_INCLUDES);
    if(!ctx)return 2;
    if(!installed && !xkb_context_include_path_append(ctx,argv[1]))return 3;
    if(installed) {
        int found=0;
        for(unsigned int i=0;i<xkb_context_num_include_paths(ctx);i++)
            if(strcmp(xkb_context_include_path_get(ctx,i),argv[1])==0)found=1;
        if(!found)return 4;
    }
    const char *layouts[]={"us","br","pt"};
    for(int i=0;i<3;i++) {
        struct xkb_rule_names names={.rules="evdev",.model="pc105",.layout=layouts[i]};
        struct xkb_keymap *map=xkb_keymap_new_from_names(ctx,&names,XKB_KEYMAP_COMPILE_NO_FLAGS);
        if(!map)return 5;
        struct xkb_state *state=xkb_state_new(map);
        if(!state)return 6;
        xkb_keycode_t key=xkb_keymap_key_by_name(map,"AC01");
        xkb_keycode_t shift=xkb_keymap_key_by_name(map,"LFSH");
        if(key==XKB_KEYCODE_INVALID || shift==XKB_KEYCODE_INVALID)return 7;
        if(xkb_state_key_get_one_sym(state,key)!=XKB_KEY_a)return 8;
        xkb_state_update_key(state,shift,XKB_KEY_DOWN);
        if(xkb_state_key_get_one_sym(state,key)!=XKB_KEY_A)return 9;
        xkb_state_update_key(state,shift,XKB_KEY_UP);
        if(xkb_state_key_get_one_sym(state,key)!=XKB_KEY_a)return 10;
        xkb_state_unref(state);xkb_keymap_unref(map);
    }
    xkb_context_unref(ctx);
    struct rxkb_context *registry=rxkb_context_new(RXKB_CONTEXT_NO_DEFAULT_INCLUDES);
    if(!registry || !rxkb_context_include_path_append(registry,argv[1]))return 11;
    if(!rxkb_context_parse(registry,"evdev"))return 12;
    unsigned int found=0;
    for(struct rxkb_layout *layout=rxkb_layout_first(registry);layout;layout=rxkb_layout_next(layout)) {
        if(rxkb_layout_get_variant(layout))continue;
        const char *name=rxkb_layout_get_name(layout);
        for(int i=0;i<3;i++)if(strcmp(name,layouts[i])==0)found|=1u<<i;
    }
    rxkb_context_unref(registry);
    if(found!=7)return 13;
    puts("native-keymaps-us-br-pt-shift-registry");return 0;
}
