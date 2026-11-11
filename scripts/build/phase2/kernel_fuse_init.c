/* Diagnostic-only native kernel init; never installed or run on the host. */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <grp.h>
#include <linux/filter.h>
#include <linux/landlock.h>
#include <linux/reboot.h>
#include <linux/seccomp.h>
#include <sched.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mount.h>
#include <sys/prctl.h>
#include <sys/reboot.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <sys/utsname.h>
#include <sys/wait.h>
#include <unistd.h>
#ifndef PROBE_TOKEN
#error Invocation token required
#endif
static void finish(int ok,const char *what) {
 printf("TODDY_KERNEL_FUSE_%s token=%s %s\n",ok?"OK":"FAIL",PROBE_TOKEN,what);fflush(stdout);sync();reboot(LINUX_REBOOT_CMD_POWER_OFF);for(;;)pause();
}
static void need(int ok,const char *what) { if(!ok){printf("errno=%d %s\n",errno,strerror(errno));finish(0,what);} }
static int read_canary(const char *path) { char b[32]={0};int f=open(path,O_RDONLY);if(f<0)return 0;ssize_t n=read(f,b,sizeof b-1);close(f);return n==12&&!strcmp(b,"TODDY-CANARY"); }
static int worker(int sandbox) {
 if(setgroups(0,NULL)||setgid(101)||setuid(101)||getuid()!=101||getgid()!=101)return 10;
 if(!read_canary("/tmp/blocked/canary"))return 11;
 if(!sandbox)return 0; /* Fresh process recovery after prior restricted child. */
 if(prctl(PR_SET_NO_NEW_PRIVS,1,0,0,0))return 12;
 int abi=syscall(SYS_landlock_create_ruleset,NULL,0,LANDLOCK_CREATE_RULESET_VERSION);if(abi<3)return 13;
 const __u64 access=LANDLOCK_ACCESS_FS_READ_FILE|LANDLOCK_ACCESS_FS_WRITE_FILE|LANDLOCK_ACCESS_FS_READ_DIR|LANDLOCK_ACCESS_FS_MAKE_REG|LANDLOCK_ACCESS_FS_REMOVE_FILE|LANDLOCK_ACCESS_FS_TRUNCATE;
 struct landlock_ruleset_attr attr={.handled_access_fs=access};int rules=syscall(SYS_landlock_create_ruleset,&attr,sizeof attr,0);if(rules<0)return 14;
 int dir=open("/tmp/allowed",O_PATH|O_CLOEXEC);if(dir<0)return 15;
 struct landlock_path_beneath_attr rule={.allowed_access=access,.parent_fd=dir};if(syscall(SYS_landlock_add_rule,rules,LANDLOCK_RULE_PATH_BENEATH,&rule,0))return 16;
 close(dir);if(syscall(SYS_landlock_restrict_self,rules,0))return 17;close(rules);
 for(int i=0;i<2;i++) {
  int f=open("/tmp/allowed/roundtrip",O_CREAT|O_TRUNC|O_RDWR,0600);if(f<0)return 18;
  char b[8]={0};if(write(f,"Toddy",5)!=5||lseek(f,0,SEEK_SET)!=0||read(f,b,5)!=5||strcmp(b,"Toddy")){close(f);return 19;}close(f);
  errno=0;f=open("/tmp/blocked/canary",O_RDONLY);if(f>=0||errno!=EACCES)return 20;
  errno=0;f=open("/tmp/blocked/canary",O_WRONLY);if(f>=0||errno!=EACCES)return 21;
  errno=0;f=open("/tmp/blocked/new",O_CREAT|O_WRONLY,0600);if(f>=0||errno!=EACCES)return 22;
 }
 struct sock_filter code[]={BPF_STMT(BPF_LD|BPF_W|BPF_ABS,offsetof(struct seccomp_data,nr)),BPF_JUMP(BPF_JMP|BPF_JEQ|BPF_K,SYS_getppid,0,1),BPF_STMT(BPF_RET|BPF_K,SECCOMP_RET_ERRNO|EPERM),BPF_STMT(BPF_RET|BPF_K,SECCOMP_RET_ALLOW)};
 struct sock_fprog program={.len=sizeof code/sizeof code[0],.filter=code};if(prctl(PR_SET_SECCOMP,SECCOMP_MODE_FILTER,&program))return 23;
 errno=0;if(syscall(SYS_getppid)!=-1||errno!=EPERM)return 24;
 return 0;
}
static void child_check(int sandbox) {pid_t p=fork();need(p>=0,"fork");if(!p)_exit(worker(sandbox));int status;need(waitpid(p,&status,0)==p,"waitpid");if(!WIFEXITED(status)||WEXITSTATUS(status)){printf("worker_status=%d\n",status);finish(0,"unprivileged worker");}}
static int fuse_owner(void) {
 if(setgroups(0,NULL)||setgid(101)||setuid(101)||getuid()!=101||getgid()!=101)return 40;
 int fd=open("/dev/fuse",O_RDWR|O_NONBLOCK);if(fd<0)return 41;close(fd);
 errno=0;if(mount("owner-denial","/tmp","fuse",0,NULL)!=-1||errno!=EPERM)return 42;
 return 0;
}
int main(void) {
 if(getpid()!=1||geteuid()!=0)return 125;
 if(mount("devtmpfs","/dev","devtmpfs",MS_NOSUID,"mode=0755"))return 126;
 int console=open("/dev/console",O_RDWR);if(console<0)return 127;
 for(int i=0;i<3;i++){if(dup2(console,i)<0)return 127;}
 if(console>2)close(console);
 setvbuf(stdout,NULL,_IONBF,0);
 need(!mount("proc","/proc","proc",MS_NOSUID|MS_NODEV|MS_NOEXEC,NULL),"proc mount");need(!mount("sysfs","/sys","sysfs",MS_NOSUID|MS_NODEV|MS_NOEXEC,NULL),"sysfs mount");
 struct utsname u;need(!uname(&u)&&!strcmp(u.release,"7.1.8-toddy")&&!strcmp(u.machine,"x86_64"),"kernel identity");
 char cmd[4096]={0};int f=open("/proc/cmdline",O_RDONLY);need(f>=0,"cmdline");ssize_t n=read(f,cmd,sizeof cmd-1);close(f);need(n>0&&n<(ssize_t)sizeof cmd-1&&strstr(cmd,"toddy_probe_token=" PROBE_TOKEN),"invocation token");
 int efi=access("/sys/firmware/efi",F_OK)==0;need(strstr(cmd,efi?"toddy_probe_mode=uefi":"toddy_probe_mode=bios")!=NULL,"firmware identity");
 need(!mount("tmpfs","/tmp","tmpfs",MS_NOSUID|MS_NODEV,"size=8m,mode=1777"),"volatile fixture");need(!mkdir("/tmp/allowed",0777)&&!chmod("/tmp/allowed",0777)&&!mkdir("/tmp/blocked",0777)&&!chmod("/tmp/blocked",0777),"fixture directories");
 f=open("/tmp/blocked/canary",O_CREAT|O_EXCL|O_WRONLY,0666);need(f>=0&&write(f,"TODDY-CANARY",12)==12&&!fchmod(f,0666),"canary positive control");close(f);
 int abi=syscall(SYS_landlock_create_ruleset,NULL,0,LANDLOCK_CREATE_RULESET_VERSION);need(abi>=3,"Landlock ABI");
 for(int i=0;i<2;i++){child_check(1);need(read_canary("/tmp/blocked/canary")&&access("/tmp/blocked/new",F_OK)<0&&errno==ENOENT,"canary unchanged/no denied write");child_check(0);}
 pid_t p=fork();need(p>=0,"namespace fork");if(!p)_exit(unshare(CLONE_NEWUSER|CLONE_NEWNS|CLONE_NEWIPC|CLONE_NEWNET)?1:0);int status;need(waitpid(p,&status,0)==p&&WIFEXITED(status)&&!WEXITSTATUS(status),"namespace creation");
 f=open("/dummy.ko",O_RDONLY);need(f>=0&&!syscall(SYS_finit_module,f,"",0),"native module insertion");close(f);need(!access("/sys/module/dummy",F_OK),"module visible");need(!syscall(SYS_delete_module,"dummy",O_NONBLOCK)&&access("/sys/module/dummy",F_OK)<0&&errno==ENOENT,"module removed");
 for(int cycle=0;cycle<2;cycle++) {
  f=open("/fuse.ko",O_RDONLY);need(f>=0&&!syscall(SYS_finit_module,f,"",0),"FUSE module insertion");close(f);
  struct stat device;need(!stat("/dev/fuse",&device)&&S_ISCHR(device.st_mode)&&!access("/sys/module/fuse",F_OK),"FUSE device and module present");
  p=fork();need(p>=0,"FUSE owner fork");if(!p)_exit(fuse_owner());need(waitpid(p,&status,0)==p&&WIFEXITED(status)&&!WEXITSTATUS(status),"UID101 FUSE open/direct mount denial");
  need(!syscall(SYS_delete_module,"fuse",O_NONBLOCK)&&access("/sys/module/fuse",F_OK)<0&&errno==ENOENT,"FUSE unload recovery");
 }
 printf("Landlock ABI=%d uid=101 rulesets=2 allowed_roundtrips=4 denied_reads=4 denied_writes=4 denied_creates=4 fresh_process_recoveries=2 seccomp_denials=2 namespace=pass module=insert-remove fuse=2-owner-opens-direct-mount-denials-unloads firmware=%s\n",abi,efi?"uefi":"bios");
 finish(1,efi?"firmware=uefi":"firmware=bios");return 0;
}
