/* Native policy-engine profile; no filesystem/network bindings or bytecode load. */
#include <duktape.h>
#include <stdio.h>
#include <string.h>
#if DUK_VERSION != 20700 || defined(DUK_USE_BYTECODE_DUMP_SUPPORT)
#error Unexpected Duktape version/bytecode profile
#endif
static unsigned checks;
static int truth(duk_context *c,const char *source) {
    if(duk_peval_string(c,source)!=DUK_EXEC_SUCCESS || !duk_is_boolean(c,-1) || !duk_get_boolean(c,-1))return 1;
    duk_set_top(c,0);checks++;return 0;
}
static duk_ret_t add(duk_context *c) {duk_push_number(c,duk_require_number(c,0)+duk_require_number(c,1));return 1;}
static duk_ret_t load(duk_context *c,void *data) {(void)data;duk_load_function(c);return 1;}
static duk_ret_t dump(duk_context *c,void *data) {(void)data;duk_dump_function(c);return 1;}
int main(void) {
    duk_context *c=duk_create_heap_default();if(!c)return 1;
    const char *cases[]={
        "Duktape.version === 20700",
        "Math.sqrt(81) === 9 && Math.sin(0) === 0",
        "(function(s){return s.uid===1000&&s.active&&s.local;})({uid:1000,active:true,local:true})",
        "!(function(s){return s.uid===1000&&s.active&&s.local;})({uid:1001,active:true,local:true})",
        "'ação'.length === 4 && 'São Paulo'.indexOf('Paulo') === 4",
        "JSON.parse(JSON.stringify({uid:1000,tags:['owner']})).tags[0] === 'owner'",
        "(function(){var b=new Uint8Array(2);b[1]=42;return b[1]===42;})()",
        "(function(){for(var i=0;i<1000;i++){var a={v:i};}Duktape.gc();return a.v===999;})()"
    };
    for(unsigned i=0;i<sizeof cases/sizeof cases[0];i++)if(truth(c,cases[i]))return 10+(int)i;
    duk_push_c_function(c,add,2);duk_put_global_string(c,"nativeAdd");
    if(truth(c,"nativeAdd(20,22)===42"))return 30;
    if(duk_peval_string(c,"nativeAdd({},2)")!=DUK_EXEC_ERROR || duk_get_error_code(c,-1)!=DUK_ERR_TYPE_ERROR)return 31;
    duk_set_top(c,0);checks++;
    if(duk_peval_string(c,"if (")!=DUK_EXEC_ERROR || duk_get_error_code(c,-1)!=DUK_ERR_SYNTAX_ERROR)return 32;
    duk_set_top(c,0);checks++;
    if(duk_peval_string(c,"JSON.parse('{')")!=DUK_EXEC_ERROR)return 33;
    duk_set_top(c,0);checks++;
    memset(duk_push_fixed_buffer(c,16),0xbf,16);
    if(duk_safe_call(c,load,NULL,1,1)!=DUK_EXEC_ERROR || !strstr(duk_safe_to_string(c,-1),"unsupported"))return 34;
    duk_set_top(c,0);checks++;
    if(duk_peval_string(c,"(function(){return 42;})")!=DUK_EXEC_SUCCESS)return 35;
    if(duk_safe_call(c,dump,NULL,1,1)!=DUK_EXEC_ERROR || !strstr(duk_safe_to_string(c,-1),"unsupported"))return 36;
    duk_set_top(c,0);checks++;
    duk_destroy_heap(c);c=duk_create_heap_default();if(!c || truth(c,"21*2===42"))return 37;
    duk_destroy_heap(c);printf("{\"version\":20700,\"checks\":%u,\"bytecode_load_dump\":\"unsupported\",\"recovery\":true}\n",checks);return 0;
}
