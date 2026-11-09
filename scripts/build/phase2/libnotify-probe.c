#include <assert.h>
#include <libnotify/notify.h>
#include <stdio.h>
#include <string.h>

int main(void)
{
    assert(notify_init("Toddy native qualification"));
    assert(notify_is_initted());
    assert(strcmp(notify_get_app_name(), "Toddy native qualification") == 0);
    NotifyNotification *notification = notify_notification_new("Toddy", "Navy desktop", "dialog-information");
    assert(notification);
    assert(notify_notification_update(notification, "Toddy updated", "Offline state", NULL));
    char *summary = NULL, *body = NULL;
    g_object_get(notification, "summary", &summary, "body", &body, NULL);
    assert(strcmp(summary, "Toddy updated") == 0 && strcmp(body, "Offline state") == 0);
    g_free(summary); g_free(body);
    notify_notification_set_timeout(notification, NOTIFY_EXPIRES_DEFAULT);
    notify_notification_set_urgency(notification, NOTIFY_URGENCY_NORMAL);
    notify_notification_set_hint(notification, "category", g_variant_new_string("device"));
    notify_notification_clear_hints(notification);
    GError *error = NULL;
    assert(!notify_notification_show(notification, &error));
    assert(error != NULL);
    printf("private empty-bus refusal: %s\n", error->message);
    g_clear_error(&error);
    g_object_unref(notification);
    notify_uninit();
    assert(!notify_is_initted());
    puts("native libnotify initialization/update/properties/hints/cleanup and absent-server refusal; no displayed notification");
    return 0;
}
