/* Private password arrives only on stdin. Never print passwords or hashes. */
#define _GNU_SOURCE
#include <security/pam_appl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static int converse(int n,const struct pam_message **m,struct pam_response **out,void *data) {
    struct pam_response *r=calloc((size_t)n,sizeof *r);if(!r)return PAM_BUF_ERR;
    for(int i=0;i<n;i++) {
        if(m[i]->msg_style==PAM_PROMPT_ECHO_OFF)r[i].resp=strdup((const char *)data);
        else if(m[i]->msg_style!=PAM_TEXT_INFO && m[i]->msg_style!=PAM_ERROR_MSG) {
            for(int j=0;j<i;j++) {if(r[j].resp){explicit_bzero(r[j].resp,strlen(r[j].resp));free(r[j].resp);}}
            free(r);return PAM_CONV_ERR;
        }
    }
    *out=r;return PAM_SUCCESS;
}
int main(int argc,char **argv) {
    if(argc!=3)return 64;
    char *password=NULL;size_t capacity=0;ssize_t n=getline(&password,&capacity,stdin);if(n<0)return 65;
    if(n && password[n-1]=='\n')password[n-1]='\0';
    struct pam_conv conv={converse,password};pam_handle_t *p=NULL;
    int start=pam_start_confdir("toddy-password",argv[2],&conv,argv[1],&p);
    int auth=-1,account=-1,cred=-1;
    if(start==PAM_SUCCESS) {auth=pam_authenticate(p,PAM_DISALLOW_NULL_AUTHTOK);account=pam_acct_mgmt(p,0);if(auth==PAM_SUCCESS)cred=pam_setcred(p,PAM_ESTABLISH_CRED);}
    explicit_bzero(password,capacity);free(password);
    int end=p ? pam_end(p,auth):PAM_SYSTEM_ERR;
    printf("{\"start\":%d,\"auth\":%d,\"account\":%d,\"credential\":%d,\"end\":%d}\n",start,auth,account,cred,end);
    return start==PAM_SUCCESS && end==PAM_SUCCESS ? 0:66;
}
