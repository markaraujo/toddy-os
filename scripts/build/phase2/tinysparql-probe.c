/* Real private local RDF store persistence/refusal/reset; no desktop/indexer claim. */
#include <tinysparql.h>
#include <gio/gio.h>
#include <locale.h>
#include <stdio.h>
#include <string.h>
static void label(TrackerSparqlConnection *connection,const char *expected) {
 GError *error=NULL;TrackerSparqlCursor *cursor=tracker_sparql_connection_query(connection,"SELECT ?title WHERE { <urn:toddy:b02> nie:title ?title }",NULL,&error);g_assert_no_error(error);g_assert_nonnull(cursor);
 gboolean row=tracker_sparql_cursor_next(cursor,NULL,&error);g_assert_no_error(error);
 if(expected){g_assert_true(row);g_assert_cmpstr(tracker_sparql_cursor_get_string(cursor,0,NULL),==,expected);g_assert_false(tracker_sparql_cursor_next(cursor,NULL,&error));g_assert_no_error(error);}else g_assert_false(row);
 tracker_sparql_cursor_close(cursor);g_object_unref(cursor);
}
int main(int argc,char **argv) {
 g_assert_cmpint(argc,==,2);g_assert_nonnull(setlocale(LC_ALL,""));const char *charset=NULL;g_assert_true(g_get_charset(&charset));
 for(int i=0;i<2;i++) {
  char *path=g_strdup_printf("%s/store-%d",argv[1],i);GFile *store=g_file_new_for_path(path),*ontology=tracker_sparql_get_ontology_nepomuk();GError *error=NULL;
  TrackerSparqlConnection *connection=tracker_sparql_connection_new(0,store,ontology,NULL,&error);g_assert_no_error(error);g_assert_nonnull(connection);
  tracker_sparql_connection_update(connection,"INSERT DATA { <urn:toddy:b02> a nie:InformationElement ; nie:title 'Toddy ã' . }",NULL,&error);g_assert_no_error(error);label(connection,"Toddy ã");
  tracker_sparql_connection_close(connection);g_object_unref(connection);
  connection=tracker_sparql_connection_new(0,store,NULL,NULL,&error);g_assert_no_error(error);g_assert_nonnull(connection);label(connection,"Toddy ã");
  TrackerSparqlCursor *bad=tracker_sparql_connection_query(connection,"SELECT !!!",NULL,&error);g_assert_null(bad);g_assert_nonnull(error);g_clear_error(&error);label(connection,"Toddy ã");
  tracker_sparql_connection_update(connection,"DELETE WHERE { <urn:toddy:b02> ?p ?o }",NULL,&error);g_assert_no_error(error);label(connection,NULL);
  tracker_sparql_connection_close(connection);g_object_unref(connection);g_object_unref(store);g_object_unref(ontology);g_free(path);
 }
 puts("{\"UTF8_insert_query\":true,\"persisted_after_connection_reopen\":true,\"malformed_query_refused_state_preserved\":true,\"delete_reset_cycles\":2,\"desktop_indexer_GUI_or_cancellation_tested\":false}");return 0;
}
