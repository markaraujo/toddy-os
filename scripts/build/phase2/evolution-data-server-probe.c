#include <libecal/libecal.h>
#include <libedataserver/libedataserver.h>
#include <assert.h>
#include <stdio.h>
#include <string.h>
int main(void) {
 assert(eds_major_version==3 && eds_minor_version==60 && eds_micro_version==2);
 const char *ics="BEGIN:VEVENT\r\nUID:toddy-synthetic-calendar\r\nDTSTAMP:20261109T120000Z\r\nDTSTART:20261109T130000Z\r\nDTEND:20261109T140000Z\r\nSUMMARY:Reunião azul-marinho\r\nEND:VEVENT\r\n";
 for(int cycle=0;cycle<2;cycle++) {
  ECalComponent *event=e_cal_component_new_from_string(ics);assert(event);
  assert(!strcmp(e_cal_component_get_uid(event),"toddy-synthetic-calendar"));
  char *before=e_cal_component_get_as_string(event);assert(before && strstr(before,"Reunião azul-marinho"));
  ECalComponent *invalid=e_cal_component_new_from_string("not a calendar");assert(!invalid);
  char *after=e_cal_component_get_as_string(event);assert(after && !strcmp(before,after));
  ECalComponent *reopened=e_cal_component_new_from_string(after);assert(reopened);
  assert(!strcmp(e_cal_component_get_uid(reopened),"toddy-synthetic-calendar"));
  g_free(before);g_free(after);g_object_unref(reopened);g_object_unref(event);
  GError *error=NULL;ESource *source=e_source_new_with_uid("toddy-synthetic-source",NULL,&error);
  assert(source && !error);e_source_set_display_name(source,"Calendário local");
  assert(!strcmp(e_source_get_uid(source),"toddy-synthetic-source"));
  assert(!strcmp(e_source_get_display_name(source),"Calendário local"));g_object_unref(source);
 }
 puts("{\"UTF8_calendar_roundtrip\":true,\"malformed_calendar_refused\":true,\"prior_event_preserved\":true,\"local_source_identity\":true,\"recovery_cycles\":2,\"real_accounts_used\":false}");
 return 0;
}
