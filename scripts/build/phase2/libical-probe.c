#include <libical/ical.h>
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int main(void) {
 const char *text="BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//Toddy//B02//EN\r\nBEGIN:VEVENT\r\nUID:toddy-private-calendar-probe\r\nDTSTART:20261109T120000Z\r\nDTEND:20261109T130000Z\r\nSUMMARY:Reunião local\r\nRRULE:FREQ=DAILY;COUNT=3\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n";
 for(int cycle=0;cycle<2;cycle++) {
  icalcomponent *calendar=icalcomponent_new_from_string(text);assert(calendar);
  icalcomponent *event=icalcomponent_get_first_component(calendar,ICAL_VEVENT_COMPONENT);assert(event);
  assert(!strcmp(icalcomponent_get_summary(event),"Reunião local"));
  struct icaltimetype start=icalcomponent_get_dtstart(event);assert(start.year==2026 && start.month==11 && start.day==9 && icaltime_is_utc(start));
  icalproperty *property=icalcomponent_get_first_property(event,ICAL_RRULE_PROPERTY);assert(property);
  struct icalrecurrencetype *rule=icalproperty_get_rrule(property);assert(rule);
  icalrecur_iterator *iter=icalrecur_iterator_new(rule,start);assert(iter);
  for(int day=9;day<=11;day++){struct icaltimetype next=icalrecur_iterator_next(iter);assert(next.year==2026 && next.month==11 && next.day==day && next.hour==12);}
  assert(icaltime_is_null_time(icalrecur_iterator_next(iter)));icalrecur_iterator_free(iter); /* rule is borrowed from the property. */
  char *serialized=icalcomponent_as_ical_string_r(calendar);assert(serialized);
  icalcomponent *restored=icalcomponent_new_from_string(serialized);assert(restored && icalcomponent_count_components(restored,ICAL_VEVENT_COMPONENT)==1);
  icalcomponent_free(restored);free(serialized);
  icalerror_set_error_state(ICAL_PARSE_ERROR,ICAL_ERROR_NONFATAL);
  icalcomponent *bad=icalcomponent_new_from_string("not an iCalendar document");assert(!bad);
  assert(!strcmp(icalcomponent_get_summary(event),"Reunião local"));
  icalcomponent_free(calendar);icalerror_clear_errno();
 }
 puts("{\"UTF8_calendar_roundtrip\":true,\"UTC_daily_recurrence_count\":3,\"invalid_document_refused\":true,\"prior_state_preserved\":true,\"recovery_cycles\":2}");return 0;
}
