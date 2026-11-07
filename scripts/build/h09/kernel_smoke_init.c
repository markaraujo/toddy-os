/* Private native-kernel diagnostic. Never an installed system init. */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <linux/reboot.h>
#include <sched.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mount.h>
#include <sys/reboot.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <sys/utsname.h>
#include <sys/wait.h>
#include <unistd.h>

#ifndef PROBE_TOKEN
#error PROBE_TOKEN must bind this init to its private boot invocation
#endif

static void finish(int ok, const char *message)
{
    printf("TODDY_KERNEL_SMOKE_%s token=%s %s\n", ok ? "OK" : "FAIL", PROBE_TOKEN, message);
    fflush(stdout);
    sync();
    reboot(LINUX_REBOOT_CMD_POWER_OFF);
    for (;;) pause();
}

static void require(int condition, const char *message)
{
    if (!condition) {
        printf("Diagnostic errno=%d (%s)\n", errno, strerror(errno));
        finish(0, message);
    }
}

int main(void)
{
    /* Refuse accidental execution in the builder or development workstation. */
    if (getpid() != 1 || geteuid() != 0) return 125;
    if (mount("devtmpfs", "/dev", "devtmpfs", MS_NOSUID, "mode=0755")) return 126;
    int console = open("/dev/console", O_RDWR);
    if (console < 0) return 127;
    for (int fd = 0; fd < 3; ++fd) if (dup2(console, fd) < 0) return 127;
    if (console > 2) close(console);
    setvbuf(stdout, NULL, _IONBF, 0);
    require(!mount("proc", "/proc", "proc", MS_NOSUID | MS_NODEV | MS_NOEXEC, NULL), "proc mount");
    require(!mount("sysfs", "/sys", "sysfs", MS_NOSUID | MS_NODEV | MS_NOEXEC, NULL), "sysfs mount");
    struct utsname system;
    require(!uname(&system), "uname syscall");
    require(!strcmp(system.release, "7.1.8-toddy") && !strcmp(system.machine, "x86_64"), "native kernel identity");
    char cmdline[4096] = {0};
    int fd = open("/proc/cmdline", O_RDONLY);
    require(fd >= 0, "kernel command line");
    ssize_t length = read(fd, cmdline, sizeof(cmdline) - 1);
    close(fd);
    require(length > 0 && length < (ssize_t)sizeof(cmdline) - 1, "bounded command line");
    require(strstr(cmdline, "toddy_probe_token=" PROBE_TOKEN) != NULL, "boot token");
    int efi = access("/sys/firmware/efi", F_OK) == 0;
    require(strstr(cmdline, efi ? "toddy_probe_mode=uefi" : "toddy_probe_mode=bios") != NULL, "firmware mode");
    require(!mount("tmpfs", "/tmp", "tmpfs", MS_NOSUID | MS_NODEV, "size=8m,mode=1777"), "volatile filesystem");
    fd = open("/tmp/roundtrip", O_CREAT | O_EXCL | O_RDWR, 0600);
    require(fd >= 0, "create volatile data");
    const char payload[] = "native-kernel-volatile-roundtrip";
    char copy[sizeof(payload)] = {0};
    require(write(fd, payload, sizeof(payload)) == (ssize_t)sizeof(payload), "write data");
    require(!fsync(fd) && lseek(fd, 0, SEEK_SET) == 0, "sync and seek");
    require(read(fd, copy, sizeof(copy)) == (ssize_t)sizeof(copy) && !memcmp(copy, payload, sizeof(copy)), "read data");
    close(fd);
    pid_t child = fork();
    require(child >= 0, "fork");
    if (!child) _exit(unshare(CLONE_NEWUSER | CLONE_NEWNS | CLONE_NEWIPC | CLONE_NEWNET) ? 1 : 0);
    int status = 0;
    require(waitpid(child, &status, 0) == child && WIFEXITED(status) && !WEXITSTATUS(status), "native namespace creation");
    fd = open("/dummy.ko", O_RDONLY);
    require(fd >= 0, "staged native module");
    require(!syscall(SYS_finit_module, fd, "", 0), "actual module insertion");
    close(fd);
    require(!access("/sys/module/dummy", F_OK), "loaded module visible");
    require(!syscall(SYS_delete_module, "dummy", O_NONBLOCK), "actual module removal");
    require(access("/sys/module/dummy", F_OK) < 0 && errno == ENOENT, "removed module absent");
    printf("Native kernel=%s machine=%s firmware=%s pid1=diagnostic namespaces=pass module=insert-remove data=roundtrip\n",
           system.release, system.machine, efi ? "uefi" : "bios");
    finish(1, efi ? "firmware=uefi" : "firmware=bios");
    return 0;
}
