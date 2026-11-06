#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
chroot_run <<'INNER'
set -euo pipefail
dpkg-query -S /usr/share/config.site | grep -F lfs-build-support
bash -c 'source /usr/share/config.site; test -z "${ac_cv_func_posix_spawn_file_actions_addchdir+x}"; test -z "${ac_cv_func_posix_spawn_file_actions_addfchdir+x}"'
grep -Fx 'ac_cv_func_posix_spawn_file_actions_addchdir=yes' /usr/share/doc/lfs-build-support/config.site.book-cross-original
fixture=$(mktemp -d /tmp/lfs-config-site-native.XXXXXX)
trap 'rm -rf "$fixture"' EXIT
cat > "$fixture/probe.c" <<'C'
#define _GNU_SOURCE
#include <spawn.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/wait.h>
extern char **environ;
int main(int argc,char **argv) {
 if(argc==2) return access("cwd-marker",F_OK)!=0;
 int fd=open(argv[1],O_RDONLY|O_DIRECTORY);
 if(fd<0 || chdir("/"))return 1;
 for(int mode=0;mode<2;mode++) {
  posix_spawn_file_actions_t a;
  if(posix_spawn_file_actions_init(&a))return 2;
  int result=mode ? posix_spawn_file_actions_addfchdir_np(&a,fd) : posix_spawn_file_actions_addchdir_np(&a,argv[1]);
  if(result)return 3;
  pid_t child;char *args[]={argv[2],"child",NULL};
  result=posix_spawn(&child,argv[2],&a,NULL,args,environ);
  posix_spawn_file_actions_destroy(&a);
  if(result)return 4;
  int status;if(waitpid(child,&status,0)!=child)return 5;
  if(!WIFEXITED(status)||WEXITSTATUS(status)!=0)return 6;
 }
 close(fd);return 0;
}
C
cc "$fixture/probe.c" -o "$fixture/probe"
touch "$fixture/cwd-marker"
"$fixture/probe" "$fixture" "$fixture/probe"
cd "$fixture"
cat > configure.ac <<'AC'
AC_INIT([native-spawn-capabilities],[1])
AC_PROG_CC
AC_CHECK_FUNCS([posix_spawn_file_actions_addchdir posix_spawn_file_actions_addfchdir posix_spawn_file_actions_addchdir_np posix_spawn_file_actions_addfchdir_np])
AC_OUTPUT
AC
autoconf
CONFIG_SITE=/usr/share/config.site ./configure --prefix=/usr
grep -Fx 'ac_cv_func_posix_spawn_file_actions_addchdir=no' config.log
grep -Fx 'ac_cv_func_posix_spawn_file_actions_addfchdir=no' config.log
grep -Fx 'ac_cv_func_posix_spawn_file_actions_addchdir_np=yes' config.log
grep -Fx 'ac_cv_func_posix_spawn_file_actions_addfchdir_np=yes' config.log
printf 'Native capability detection and actual child working-directory actions passed\n'
INNER
