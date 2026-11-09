#include <assert.h>
#include <canberra.h>
#include <stdio.h>
#include <string.h>
static int finished;
static void done(ca_context *c,uint32_t id,int error,void *data) {
    assert(c && id==42 && error==CA_SUCCESS && data==&finished);finished++;
}
int main(int argc,char **argv) {
    ca_context *context;ca_proplist *props;assert(ca_context_create(&context)==0);assert(ca_proplist_create(&props)==0);
    assert(ca_proplist_sets(props,CA_PROP_APPLICATION_NAME,"Toddy ação")==0);
    assert(ca_context_change_props_full(context,props)==0);
    assert(ca_context_cancel(context,42)==CA_ERROR_STATE);
    assert(ca_context_change_props(context,CA_PROP_CANBERRA_ENABLE,"0",NULL)==0);
    assert(ca_context_play(context,42,CA_PROP_EVENT_ID,"dialog-information",NULL)==CA_ERROR_DISABLED);
    assert(ca_context_change_props(context,CA_PROP_CANBERRA_ENABLE,"1",NULL)==0);
    if(argc==2) {
        assert(strcmp(argv[1],"--null-module")==0);
        assert(ca_context_set_driver(context,"null")==0 && ca_context_open(context)==0);
        assert(ca_context_open(context)==CA_ERROR_STATE);
        assert(ca_proplist_sets(props,CA_PROP_EVENT_ID,"dialog-information")==0);
        assert(ca_context_play_full(context,42,props,done,&finished)==0 && finished==1);
        assert(ca_context_cancel(context,42)==0);
        assert(ca_context_cache_full(context,props)==CA_ERROR_NOTSUPPORTED);
    }
    assert(ca_proplist_destroy(props)==0 && ca_context_destroy(context)==0);
    puts(argc==2 ? "native Canberra installed null-module callback/cancel/state/refusal; no audible output" : "native Canberra Unicode properties/lifecycle/disabled-event and unopened-cancel refusal; no module/device output");
    return 0;
}
