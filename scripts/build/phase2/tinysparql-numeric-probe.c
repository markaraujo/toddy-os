/* Verify typed values and lossless lexical output without changing SQLite settings. */
#include <tinysparql.h>
#include <gio/gio.h>
#include <stdio.h>
#include <string.h>
int main(void) {
 GError *error=NULL; GFile *ontology=tracker_sparql_get_ontology_nepomuk();
 TrackerSparqlConnection *db=tracker_sparql_connection_new(0,NULL,ontology,NULL,&error);
 g_assert_no_error(error);g_assert_nonnull(db);
 const char *queries[]={
 "SELECT (xsd:double(10) / xsd:double(3) AS ?v) WHERE {}",
 "SELECT (1 / xsd:double(42) AS ?v) WHERE {}",
 "SELECT (1 / xsd:double(17) AS ?v) WHERE {}",
 "SELECT (xsd:double(4) / xsd:double(9) AS ?v) WHERE {}"};
 const char *expected[]={"3.3333333333333335","0.023809523809523808","0.058823529411764705","0.44444444444444442"};
 const double values[]={10.0/3.0,1.0/42.0,1.0/17.0,4.0/9.0};
 for(unsigned i=0;i<G_N_ELEMENTS(queries);i++) {
  TrackerSparqlCursor *c=tracker_sparql_connection_query(db,queries[i],NULL,&error);
  g_assert_no_error(error);g_assert_nonnull(c);g_assert_true(tracker_sparql_cursor_next(c,NULL,&error));g_assert_no_error(error);
  g_assert_cmpfloat(tracker_sparql_cursor_get_double(c,0),==,values[i]);
  const char *text=tracker_sparql_cursor_get_string(c,0,NULL);g_assert_cmpstr(text,==,expected[i]);
  char *end=NULL;double recovered=g_ascii_strtod(text,&end);g_assert_cmpstr(end,==,"");g_assert_cmpfloat(recovered,==,values[i]);
  g_assert_false(tracker_sparql_cursor_next(c,NULL,&error));g_assert_no_error(error);
  tracker_sparql_cursor_close(c);g_object_unref(c);
 }
 tracker_sparql_connection_close(db);g_object_unref(db);g_object_unref(ontology);
 puts("{\"typed_double_arithmetic_cases\":4,\"lossless_text_roundtrip_cases\":4,\"SQLite_settings_changed\":false}");
 return 0;
}
