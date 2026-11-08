#include <seccomp.h>
#include <sys/syscall.h>
#include <sys/wait.h>
#include <unistd.h>
#include <assert.h>
#include <errno.h>
int main(void) {
    assert(seccomp_init(0x12345678U) == NULL);
    pid_t child = fork(); assert(child >= 0);
    if (!child) {
        scmp_filter_ctx context = seccomp_init(SCMP_ACT_ALLOW); assert(context);
        assert(seccomp_rule_add(context, SCMP_ACT_ERRNO(EPERM), SCMP_SYS(getppid), 0) == 0);
        assert(seccomp_load(context) == 0);
        errno = 0;
        assert(syscall(SYS_getppid) == -1 && errno == EPERM);
        assert(syscall(SYS_getpid) > 0);
        seccomp_release(context); _exit(0);
    }
    int status = 0; assert(waitpid(child, &status, 0) == child);
    assert(WIFEXITED(status) && WEXITSTATUS(status) == 0);
    assert(syscall(SYS_getppid) > 0);
    return 0;
}
