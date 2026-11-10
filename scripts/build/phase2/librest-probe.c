#include <rest/rest.h>
#include <string.h>
int main(void) {
  RestXmlParser *parser=rest_xml_parser_new();
  const char *xml="<document><title>Olá Toddy 🐾</title></document>";
  for (int i=0;i<2;i++) {
    RestXmlNode *root=rest_xml_parser_parse_from_data(parser,xml,strlen(xml));
    g_assert_nonnull(root);
    RestXmlNode *title=rest_xml_node_find(root,"title");
    g_assert_nonnull(title);g_assert_cmpstr(title->content,==,"Olá Toddy 🐾");
    rest_xml_node_unref(root);
    root=rest_xml_parser_parse_from_data(parser,"not XML",7);
    g_assert_null(root);
    RestProxy *proxy=rest_proxy_new("http://127.0.0.1:1/",FALSE);
    RestProxyCall *call=rest_proxy_new_call(proxy);
    rest_proxy_call_set_function(call,"local-only");
    rest_proxy_call_add_param(call,"title","Olá Toddy 🐾");
    g_assert_cmpstr(rest_proxy_call_get_function(call),==,"local-only");
    g_object_unref(call);g_object_unref(proxy);
  }
  g_object_unref(parser);
  g_print("UTF8 XML/two malformed refusals/two fresh proxy+parser recoveries; no request sent\n");
  return 0;
}
