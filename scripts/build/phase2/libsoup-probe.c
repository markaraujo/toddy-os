#include <libsoup/soup.h>
#include <assert.h>
#include <stdio.h>
#include <string.h>
static gint requests;
static void reply(SoupServer *server,SoupServerMessage *message,const char *path,
 GHashTable *query,gpointer data) {
 (void)server;(void)path;(void)query;(void)data;
 g_atomic_int_inc(&requests);
 soup_server_message_set_status(message,SOUP_STATUS_OK,NULL);
 soup_server_message_set_response(message,"text/plain",SOUP_MEMORY_STATIC,"navy",4);
}
static gpointer run_server(gpointer data) {
 GMainLoop *loop=data;GMainContext *context=g_main_loop_get_context(loop);
 g_main_context_push_thread_default(context);g_main_loop_run(loop);
 g_main_context_pop_thread_default(context);return NULL;
}
static void request(SoupSession *session,const char *uri) {
 GError *error=NULL;SoupMessage *message=soup_message_new("GET",uri);assert(message);
 GBytes *body=soup_session_send_and_read(session,message,NULL,&error);
 assert(body && !error && soup_message_get_status(message)==SOUP_STATUS_OK);
 gsize size;const void *data=g_bytes_get_data(body,&size);
 assert(size==4 && !memcmp(data,"navy",4));g_bytes_unref(body);g_object_unref(message);
}
int main(void) {
 assert(soup_get_major_version()==3 && soup_get_minor_version()==6 && soup_get_micro_version()==6);
 GMainContext *context=g_main_context_new();g_main_context_push_thread_default(context);
 GMainLoop *loop=g_main_loop_new(context,FALSE);SoupServer *server=soup_server_new(NULL,NULL);
 soup_server_add_handler(server,NULL,reply,NULL,NULL);GError *error=NULL;
 assert(soup_server_listen_local(server,0,SOUP_SERVER_LISTEN_IPV4_ONLY,&error) && !error);
 GSList *uris=soup_server_get_uris(server);assert(uris && !uris->next);
 char *uri=g_uri_to_string(uris->data);g_slist_free_full(uris,(GDestroyNotify)g_uri_unref);
 g_main_context_pop_thread_default(context);GThread *thread=g_thread_new("http-peer",run_server,loop);
 for(int cycle=0;cycle<2;cycle++) {
  SoupSession *session=soup_session_new();soup_session_set_timeout(session,5);
  soup_session_set_proxy_resolver(session,NULL);request(session,uri);
  GCancellable *stop=g_cancellable_new();g_cancellable_cancel(stop);
  SoupMessage *message=soup_message_new("GET",uri);assert(message);
  GBytes *body=soup_session_send_and_read(session,message,stop,&error);
  assert(!body && g_error_matches(error,G_IO_ERROR,G_IO_ERROR_CANCELLED));g_clear_error(&error);
  g_object_unref(message);g_object_unref(stop);request(session,uri);
  soup_session_abort(session);g_object_unref(session);
 }
 assert(g_atomic_int_get(&requests)==4);
 g_main_loop_quit(loop);g_thread_join(thread);soup_server_disconnect(server);
 g_object_unref(server);g_main_loop_unref(loop);g_main_context_unref(context);g_free(uri);
 puts("{\"actual_HTTP_client_server_roundtrip\":true,\"precancelled_request_refused\":true,\"cancelled_request_not_dispatched\":true,\"post_cancel_recovery_cycles\":2,\"server_requests\":4,\"external_network_used\":false}");
 return 0;
}
