/* Actual VTE regex/PTY/Bash process boundaries; no display or widget claim. */
#define _GNU_SOURCE
#include <vte/vte.h>
#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/wait.h>
#include <unistd.h>
static void require(int condition,const char *message) {
    if(!condition){fprintf(stderr,"VTE postcondition: %s\n",message);exit(1);}
}
static void cycle(const char *command,const char *marker,int stop,const char *profile,int interactive) {
    GError *error=NULL;VtePty *pty=vte_pty_new_sync(VTE_PTY_DEFAULT,NULL,&error);
    require(pty!=NULL && error==NULL,"PTY creation");
    require(vte_pty_set_size(pty,30,100,&error) && error==NULL,"PTY resize");
    int rows=0,columns=0;require(vte_pty_get_size(pty,&rows,&columns,&error) && rows==30 && columns==100,"PTY geometry");
    require(vte_pty_set_utf8(pty,TRUE,&error) && error==NULL,"PTY UTF8 mode");
    int fd=vte_pty_get_fd(pty);struct winsize size={0};
    require(fd>=0 && ioctl(fd,TIOCGWINSZ,&size)==0 && size.ws_row==30 && size.ws_col==100,"actual terminal ioctl");
    pid_t child=fork();require(child>=0,"fork");
    if(child==0) {
        vte_pty_child_setup(pty);
        if(interactive)execl("/usr/bin/bash","bash","--noprofile","--norc","-i","-c",command,"toddy-probe",profile,(char*)NULL);
        else execl("/usr/bin/bash","bash","--noprofile","--norc","-c",command,(char*)NULL);
        _exit(127);
    }
    require(fcntl(fd,F_SETFL,fcntl(fd,F_GETFL)|O_NONBLOCK)==0,"nonblocking PTY");
    char data[8192]={0};size_t used=0;gint64 end=g_get_monotonic_time()+10*G_TIME_SPAN_SECOND;
    while(strstr(data,marker)==NULL && g_get_monotonic_time()<end) {
        struct pollfd event={fd,POLLIN|POLLHUP,0};int ready=poll(&event,1,100);
        require(ready>=0 || errno==EINTR,"PTY poll");
        if(ready>0 && used<sizeof(data)-1) {
            /* VTE enables TIOCPKT: each master read starts with a control
             * byte. Zero means text follows; nonzero is a control-only packet.
             * Keep control bytes out of the UTF8 text/marker buffer. */
            unsigned char packet[2048];ssize_t n=read(fd,packet,sizeof(packet));
            if(n>0 && packet[0]==0){
                size_t count=(size_t)n-1;require(count<sizeof(data)-used,"bounded PTY text");
                memcpy(data+used,packet+1,count);used+=count;data[used]=0;
            } else if(n>0)continue;
            else if(n==0 || (n<0 && errno==EIO))break;
            else require(errno==EAGAIN || errno==EINTR,"PTY read");
        }
    }
    if(strstr(data,marker)==NULL) {
        int status=0;if(waitpid(child,&status,WNOHANG)==0){kill(child,SIGKILL);waitpid(child,&status,0);}
        fprintf(stderr,"PTY diagnostic: %s\n",data);require(0,"actual child marker absent");
    }
    if(stop){require(getpgid(child)==child,"owned process group identity");require(kill(-child,SIGTERM)==0,"actual managed Stop");}
    int status=0;pid_t waited=0;end=g_get_monotonic_time()+5*G_TIME_SPAN_SECOND;
    while((waited=waitpid(child,&status,WNOHANG))==0 && g_get_monotonic_time()<end)g_usleep(10000);
    if(waited==0){kill(child,SIGKILL);waitpid(child,&status,0);require(0,"child completion timeout");}
    require(waited==child,"actual child wait");
    if(stop)require(WIFSIGNALED(status) && WTERMSIG(status)==SIGTERM,"Stop signal postcondition");
    else require(WIFEXITED(status) && WEXITSTATUS(status)==0,"actual shell exit0");
    g_object_unref(pty);
}
int main(int argc,char **argv) {
    require(argc==2,"controlled shell hook path");
    require(vte_get_major_version()==0 && vte_get_minor_version()==84 && vte_get_micro_version()==1,"runtime version");
    GError *error=NULL;VteRegex *regex=vte_regex_new_for_match("Toddy[0-9]+",-1,VTE_REGEX_FLAGS_DEFAULT,&error);
    require(regex!=NULL && error==NULL,"regex compile");
    char *value=vte_regex_substitute(regex,"Toddy42","OS",0,&error);
    require(value!=NULL && strcmp(value,"OS")==0 && error==NULL,"regex substitution");g_free(value);vte_regex_unref(regex);
    regex=vte_regex_new_for_match("[",-1,VTE_REGEX_FLAGS_DEFAULT,&error);
    require(regex==NULL && error!=NULL,"invalid regex refusal");g_clear_error(&error);
    for(int i=0;i<2;i++)cycle("printf 'TODDY_PTY_ã\\n'","TODDY_PTY_ã",0,argv[1],0);
    cycle("printf 'TODDY_STOP_READY\\n'; exec sleep 60","TODDY_STOP_READY",1,argv[1],0);
    cycle("printf 'TODDY_RECOVERY_ã\\n'","TODDY_RECOVERY_ã",0,argv[1],0);
    const char *hook="export VTE_VERSION=8401 TERM=xterm-256color; owner_counter=0; owner_hook='owner_counter=$((owner_counter+1))'; PROMPT_COMMAND=\"$owner_hook\"; PS1='OWNER_PROMPT$ '; . \"$1\"; [[ ${PROMPT_COMMAND[0]} == \"$owner_hook\" ]] || exit 20; eval \"${PROMPT_COMMAND[0]}\"; [[ $owner_counter == 1 && $PS1 == *'OWNER_PROMPT$ '* ]] || exit 21; printf 'TODDY_HOOK_PRESERVED\\n'";
    cycle(hook,"TODDY_HOOK_PRESERVED",0,argv[1],1);
    puts("{\"version\":\"0.84.1\",\"regex_compile_replace\":true,\"invalid_regex_refused\":true,\"PTY_resize_UTF8\":true,\"normal_shell_cycles\":3,\"managed_process_group_Stop\":true,\"fresh_PTY_after_Stop\":true,\"interactive_owner_prompt_hook_preserved\":true,\"GTK_GNOME_Terminal_or_display_tested\":false}");
}
