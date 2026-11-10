#include <glibtop.h>
#include <glibtop/open.h>
#include <glibtop/mem.h>
#include <glibtop/procstate.h>
#include <glibtop/uptime.h>
#include <unistd.h>
#include <stdio.h>

int main(void) {
    glibtop *server = NULL;
    g_assert_nonnull(glibtop_init_r(&server, 0, GLIBTOP_FEATURES_NO_SERVER));
    for (unsigned int cycle = 0; cycle < 2; cycle++) {
        glibtop_mem memory;
        glibtop_uptime uptime;
        glibtop_proc_state state;
        glibtop_get_mem(&memory);
        g_assert_cmpuint(memory.flags & (1ULL << GLIBTOP_MEM_TOTAL), !=, 0);
        g_assert_cmpuint(memory.total, >, 0);
        g_assert_cmpuint(memory.used, <=, memory.total);
        glibtop_get_uptime(&uptime);
        g_assert_cmpfloat(uptime.uptime, >, 0);
        glibtop_get_proc_state(&state, 2147483647);
        g_assert_cmpuint(state.flags, ==, 0);
        glibtop_get_proc_state(&state, getpid());
        g_assert_cmpuint(state.flags & (1ULL << GLIBTOP_PROC_STATE_UID), !=, 0);
        g_assert_cmpint(state.uid, ==, getuid());
        g_assert_cmpint(state.gid, ==, getgid());
        g_assert_cmpint(getuid(), ==, 101);
        g_assert_cmpint(geteuid(), ==, 101);
    }
    glibtop_close();
    puts("Libgtop direct local memory/uptime/own-process/missing-PID refusal/two recoveries; no server or elevated identity");
    return 0;
}
