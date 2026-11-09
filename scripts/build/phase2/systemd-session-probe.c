/* Real PAM session lifecycle. No password, token or owner credential is used. */
#define _GNU_SOURCE
#include <security/pam_appl.h>
#include <stdio.h>
#include <stdlib.h>
static int conversation(int n,const struct pam_message **m,struct pam_response **r,void *data) {
    (void)n;(void)m;(void)r;(void)data;return PAM_CONV_ERR;
}
static void string_json(const char *s) {
    if(!s){fputs("null",stdout);return;}putchar('"');
    for(const unsigned char *p=(const unsigned char *)s;*p;p++) {
        if(*p=='"'||*p=='\\'){putchar('\\');putchar(*p);}
        else if(*p<32)printf("\\u%04x",*p);
        else putchar(*p);
    }
    putchar('"');
}
int main(int argc,char **argv) {
    if(argc!=3)return 64;
    struct pam_conv conv={conversation,NULL};pam_handle_t *p=NULL;
    int r=pam_start_confdir("toddy-session",argv[2],&conv,argv[1],&p);
    if(r!=PAM_SUCCESS)return 10;
    if(pam_set_item(p,PAM_TTY,"tty1")!=PAM_SUCCESS)return 11;
    if(pam_putenv(p,"XDG_SESSION_TYPE=tty")!=PAM_SUCCESS)return 12;
    if(pam_putenv(p,"XDG_SESSION_CLASS=user")!=PAM_SUCCESS)return 13;
    r=pam_acct_mgmt(p,0);if(r!=PAM_SUCCESS){printf("{\"phase\":\"account-error\",\"code\":%d}\n",r);pam_end(p,r);return 14;}
    r=pam_open_session(p,0);if(r!=PAM_SUCCESS){printf("{\"phase\":\"session-error\",\"code\":%d}\n",r);pam_end(p,r);return 15;}
    fputs("{\"phase\":\"ready\",\"session_id\":",stdout);string_json(pam_getenv(p,"XDG_SESSION_ID"));
    fputs(",\"runtime_dir\":",stdout);string_json(pam_getenv(p,"XDG_RUNTIME_DIR"));
    fputs(",\"session_type\":",stdout);string_json(pam_getenv(p,"XDG_SESSION_TYPE"));
    fputs(",\"seat\":",stdout);string_json(pam_getenv(p,"XDG_SEAT"));fputs("}\n",stdout);fflush(stdout);
    (void)getchar();
    int close_result=pam_close_session(p,0);int end_result=pam_end(p,close_result);
    printf("{\"phase\":\"closed\",\"close\":%d,\"end\":%d}\n",close_result,end_result);fflush(stdout);
    return close_result==PAM_SUCCESS && end_result==PAM_SUCCESS ? 0:16;
}
