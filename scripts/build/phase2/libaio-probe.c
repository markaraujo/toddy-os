#include <errno.h>
#include <libaio.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

static int complete(io_context_t ctx, struct iocb *request, size_t expected)
{
    struct timespec deadline = { .tv_sec = 2 };
    struct io_event event;
    return io_submit(ctx, 1, &request) == 1 &&
           io_getevents(ctx, 1, 1, &event, &deadline) == 1 &&
           event.obj == request && event.res == expected && event.res2 == 0;
}

int main(void)
{
    const char payload[] = "Toddy OS isolated AIO fixture";
    for (int cycle = 0; cycle < 2; ++cycle) {
        io_context_t ctx = NULL;
        if (io_setup(0, &ctx) != -EINVAL || ctx != NULL || io_setup(8, &ctx) != 0)
            return 1;

        char name[] = "/tmp/toddy-libaio-XXXXXX";
        int fd = mkstemp(name);
        if (fd < 0 || unlink(name) != 0)
            return 1;

        struct iocb request;
        char data[sizeof(payload)];
        memcpy(data, payload, sizeof(payload));
        io_prep_pwrite(&request, fd, data, sizeof(data), 0);
        if (!complete(ctx, &request, sizeof(data)))
            return 1;
        memset(data, 0, sizeof(data));
        io_prep_pread(&request, fd, data, sizeof(data), 0);
        if (!complete(ctx, &request, sizeof(data)) || memcmp(data, payload, sizeof(data)) != 0)
            return 1;
        if (close(fd) != 0 || io_destroy(ctx) != 0)
            return 1;
    }
    puts("Linux AIO invalid-depth refusal and two asynchronous file write/read recoveries passed");
    return 0;
}
