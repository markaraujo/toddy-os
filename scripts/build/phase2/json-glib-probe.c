#include <assert.h>
#include <json-glib/json-glib.h>
#include <stdio.h>
#include <string.h>

int main(void)
{
    JsonParser *parser=json_parser_new();
    GError *error=NULL;
    const char text[]="{\"name\":\"Toddy ação\",\"count\":42,\"offline\":true}";
    assert(json_parser_load_from_data(parser,text,-1,&error) && error==NULL);
    JsonNode *root=json_parser_get_root(parser);
    assert(root && JSON_NODE_HOLDS_OBJECT(root));
    JsonObject *object=json_node_get_object(root);
    assert(strcmp(json_object_get_string_member(object,"name"),"Toddy ação")==0);
    assert(json_object_get_int_member(object,"count")==42);
    assert(json_object_get_boolean_member(object,"offline"));
    assert(!json_parser_load_from_data(parser,"{broken",-1,&error));
    assert(error!=NULL);
    g_clear_error(&error);
    g_object_unref(parser);
    puts("native JSON-GLib Unicode/object/int/bool and malformed-input refusal; no network/service/UI acceptance");
    return 0;
}
