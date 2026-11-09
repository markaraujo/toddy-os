#include <assert.h>
#include <pulse/pulseaudio.h>
#include <pulse/glib-mainloop.h>
#include <stdio.h>
#include <string.h>
int main(void) {
    pa_sample_spec spec={PA_SAMPLE_S16LE,48000,2};assert(pa_sample_spec_valid(&spec));
    assert(pa_frame_size(&spec)==4 && pa_usec_to_bytes(10000,&spec)==1920);
    pa_cvolume volume;assert(pa_cvolume_set(&volume,2,PA_VOLUME_NORM));assert(pa_cvolume_valid(&volume));
    pa_channel_map map;assert(pa_channel_map_init_stereo(&map));assert(pa_channel_map_compatible(&map,&spec));
    pa_proplist *props=pa_proplist_new();assert(props);assert(pa_proplist_sets(props,PA_PROP_APPLICATION_NAME,"Toddy ação")==0);
    assert(strcmp(pa_proplist_gets(props,PA_PROP_APPLICATION_NAME),"Toddy ação")==0);
    pa_mainloop *loop=pa_mainloop_new();assert(loop);
    pa_context *context=pa_context_new_with_proplist(pa_mainloop_get_api(loop),"Toddy audio API",props);assert(context);
    int result=pa_context_connect(context,"unix:/this-path-does-not-exist/toddy-pulse",PA_CONTEXT_NOAUTOSPAWN,NULL);
    if(result==0)for(int i=0;i<32 && pa_context_get_state(context)!=PA_CONTEXT_FAILED;i++)assert(pa_mainloop_iterate(loop,0,NULL)>=0);
    assert(result<0 || pa_context_get_state(context)==PA_CONTEXT_FAILED);
    pa_context_disconnect(context);pa_context_unref(context);pa_mainloop_free(loop);pa_proplist_free(props);
    pa_glib_mainloop *glib=pa_glib_mainloop_new(NULL);assert(glib);assert(pa_glib_mainloop_get_api(glib));pa_glib_mainloop_free(glib);
    puts("native Pulse client sample/channel/volume/Unicode/mainloops and absent-server refusal, autospawn disabled; no audible output");return 0;
}
