#include <assert.h>
#include <errno.h>
#include <libinput.h>
#include <stdio.h>
#include <unistd.h>

static unsigned denied;
static int open_restricted(const char *path, int flags, void *data)
{
    (void)path; (void)flags;
    assert(data == &denied);
    denied++;
    return -EACCES;
}
static void close_restricted(int fd, void *data)
{
    assert(data == &denied);
    close(fd);
}
int main(void)
{
    const struct libinput_interface interface = {open_restricted, close_restricted};
    struct libinput *context = libinput_path_create_context(&interface, &denied);
    assert(context);
    assert(libinput_get_user_data(context) == &denied);
    libinput_log_set_priority(context, LIBINPUT_LOG_PRIORITY_ERROR);
    assert(libinput_log_get_priority(context) == LIBINPUT_LOG_PRIORITY_ERROR);
    assert(libinput_get_fd(context) >= 0);
    assert(libinput_dispatch(context) == 0);
    assert(libinput_get_event(context) == NULL);
    assert(libinput_path_add_device(context, "/dev/toddy-nonexistent-input") == NULL);
    assert(denied == 0);
    libinput_suspend(context);
    assert(libinput_resume(context) == 0);
    assert(libinput_unref(context) == NULL);
    puts("native libinput context/FD/empty dispatch/log policy/suspend/resume and invalid-path refusal before open callback");
    return 0;
}
