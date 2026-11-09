/* Real strict UTF-8 parser, typed identity, depth bound and recovery consumer. */
#include <json-c/json.h>
#include <json-c/json_pointer.h>
#include <stdio.h>
#include <string.h>
#define REQUIRE(c) do { if (!(c)) return __LINE__; } while (0)
int main(void) {
    REQUIRE(!strcmp(json_c_version(),"0.19"));
    struct json_tokener *tok=json_tokener_new_ex(8);REQUIRE(tok);
    json_tokener_set_flags(tok,JSON_TOKENER_STRICT|JSON_TOKENER_VALIDATE_UTF8);
    const char *text="{\"identity\":{\"uid\":12345},\"allow\":false,\"name\":\"a\\u00e7\\u00e3o\"}";
    struct json_object *root=json_tokener_parse_ex(tok,text,(int)strlen(text)+1),*value=NULL;
    REQUIRE(root && json_tokener_get_error(tok)==json_tokener_success);
    REQUIRE(json_pointer_get(root,"/identity/uid",&value)==0 && json_object_is_type(value,json_type_int) && json_object_get_int64(value)==12345);
    REQUIRE(json_object_object_get_ex(root,"allow",&value) && json_object_is_type(value,json_type_boolean) && !json_object_get_boolean(value));
    REQUIRE(json_object_object_get_ex(root,"name",&value) && !strcmp(json_object_get_string(value),"a\xc3\xa7\xc3\xa3o"));
    REQUIRE(!json_object_object_get_ex(root,"missing",&value));
    const char *serialized=json_object_to_json_string_ext(root,JSON_C_TO_STRING_PLAIN);REQUIRE(serialized && strstr(serialized,"12345"));
    json_object_put(root);json_tokener_reset(tok);
    root=json_tokener_parse_ex(tok,"{\"bad\":",8);REQUIRE(!root && json_tokener_get_error(tok)!=json_tokener_success);json_tokener_reset(tok);
    const char invalid[]={'"',(char)0xff,'"',0};root=json_tokener_parse_ex(tok,invalid,sizeof invalid);REQUIRE(!root && json_tokener_get_error(tok)!=json_tokener_success);json_tokener_reset(tok);
    const char *deep="[[[[[[[[[[[[0]]]]]]]]]]]]";root=json_tokener_parse_ex(tok,deep,(int)strlen(deep)+1);REQUIRE(!root && json_tokener_get_error(tok)==json_tokener_error_depth);json_tokener_reset(tok);
    root=json_tokener_parse_ex(tok,"{\"ready\":true}",15);REQUIRE(root && json_tokener_get_error(tok)==json_tokener_success);json_object_put(root);json_tokener_free(tok);
    puts("{\"version\":\"0.19\",\"typed_identity\":true,\"unicode\":true,\"false_permission_preserved\":true,\"malformed_refused\":true,\"invalid_utf8_refused\":true,\"depth_bound_refused\":true,\"recovery\":true}");return 0;
}
