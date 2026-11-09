#define _POSIX_C_SOURCE 200809L
#include <assert.h>
#include <pipewire/pipewire.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

struct state { struct pw_main_loop *loop; int sequence; int acknowledged; };
static void done(void *data, uint32_t id, int sequence)
{
    struct state *s = data;
    if (id == PW_ID_CORE && sequence == s->sequence) {
        s->acknowledged = 1;
        pw_main_loop_quit(s->loop);
    }
}
static void error(void *data, uint32_t id, int sequence, int result, const char *message)
{
    (void)id; (void)sequence;
    fprintf(stderr, "core error %d: %s\n", result, message);
    pw_main_loop_quit(((struct state *)data)->loop);
}
int main(int argc, char **argv)
{
    pw_init(&argc, &argv);
    assert(strcmp(pw_get_library_version(), "1.6.8") == 0);
    struct state s = {0};
    s.loop = pw_main_loop_new(NULL);
    assert(s.loop);
    struct pw_context *context = pw_context_new(pw_main_loop_get_loop(s.loop), NULL, 0);
    assert(context);
    struct pw_core *core = pw_context_connect(context, NULL, 0);
    assert(core);
    struct spa_hook listener;
    const struct pw_core_events events = { PW_VERSION_CORE_EVENTS, .done=done, .error=error };
    pw_core_add_listener(core, &listener, &events, &s);
    s.sequence = pw_core_sync(core, PW_ID_CORE, 0);
    assert(s.sequence >= 0);
    alarm(10);
    assert(pw_main_loop_run(s.loop) == 0);
    alarm(0);
    assert(s.acknowledged);
    spa_hook_remove(&listener);
    pw_core_disconnect(core);
    pw_context_destroy(context);
    pw_main_loop_destroy(s.loop);
    pw_deinit();
    puts("native Pipewire1.6.8 real private daemon/client core synchronization and cleanup");
    return 0;
}
